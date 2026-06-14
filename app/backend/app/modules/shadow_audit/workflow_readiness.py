from __future__ import annotations

from datetime import UTC, datetime
import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import CaseImagingInput, CaseModelInputSnapshot
from app.modules.shadow_audit.imaging_contract import imaging_preprocessing_state, is_ready_preprocessed_imaging_reference

CLINICAL_BRANCH_NAME = 'clinical_mlp'
IMAGING_BRANCH_NAME = 'imaging_resnet18'
MULTIMODAL_BRANCH_NAME = 'multimodal_resnet18'

BRANCH_STATUS_READY = 'ready'
BRANCH_STATUS_BLOCKED = 'blocked'
BRANCH_STATUS_SCHEMA_UNVERIFIED = 'schema_unverified'
BRANCH_STATUS_PREPROCESSING_REQUIRED = 'preprocessing_required'
BRANCH_STATUS_UNAVAILABLE = 'unavailable'

WORKFLOW_OVERALL_READY_PARTIAL = 'ready_partial'
WORKFLOW_OVERALL_READY_ALL = 'ready_all'
WORKFLOW_OVERALL_BLOCKED = 'blocked'

PREVIEW_LIMITATIONS = [
    'preview_only',
    'shadow_only',
    'not_for_diagnosis',
    'no_runner_invocation',
    'no_recommendation',
    'no_trace_or_evidence',
]

MULTIMODAL_CLINICAL_FEATURE_COLUMNS_PATH = Path(
    '/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/'
    'multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json'
)
MULTIMODAL_SCHEMA_ID = 'clinical_mlp_cap_cop_input_schema_v1'
MULTIMODAL_FEATURE_SET_ID = 'cap_cop_clinical_feature_set_v1'


def _now() -> datetime:
    return datetime.now(UTC)


def _latest_snapshot(db: Session, case_id: UUID) -> CaseModelInputSnapshot | None:
    return db.execute(
        select(CaseModelInputSnapshot)
        .where(CaseModelInputSnapshot.case_id == case_id)
        .order_by(
            CaseModelInputSnapshot.created_at.desc().nullslast(),
            CaseModelInputSnapshot.updated_at.desc().nullslast(),
            CaseModelInputSnapshot.id.desc(),
        )
    ).scalars().first()


def _latest_ready_snapshot(db: Session, case_id: UUID) -> CaseModelInputSnapshot | None:
    return db.execute(
        select(CaseModelInputSnapshot)
        .where(CaseModelInputSnapshot.case_id == case_id)
        .where(CaseModelInputSnapshot.validation_status == 'ready_for_inference')
        .where(CaseModelInputSnapshot.current_assessment_status == 'ready_for_inference')
        .where(CaseModelInputSnapshot.not_for_diagnosis.is_(True))
        .where(CaseModelInputSnapshot.runtime_stub.is_(True))
        .order_by(
            CaseModelInputSnapshot.created_at.desc().nullslast(),
            CaseModelInputSnapshot.updated_at.desc().nullslast(),
            CaseModelInputSnapshot.id.desc(),
        )
    ).scalars().first()

def _latest_ready_multimodal_snapshot(db: Session, case_id: UUID) -> CaseModelInputSnapshot | None:
    rows = db.execute(
        select(CaseModelInputSnapshot)
        .where(CaseModelInputSnapshot.case_id == case_id)
        .where(CaseModelInputSnapshot.validation_status == 'ready_for_inference')
        .where(CaseModelInputSnapshot.current_assessment_status == 'ready_for_inference')
        .where(CaseModelInputSnapshot.not_for_diagnosis.is_(True))
        .where(CaseModelInputSnapshot.runtime_stub.is_(True))
        .order_by(
            CaseModelInputSnapshot.created_at.desc().nullslast(),
            CaseModelInputSnapshot.updated_at.desc().nullslast(),
            CaseModelInputSnapshot.id.desc(),
        )
    ).scalars().all()
    for row in rows:
        contract = _multimodal_clinical_payload_contract(row)
        if contract['ready']:
            return row
    return None


@lru_cache(maxsize=1)
def _multimodal_runner_feature_columns() -> list[str]:
    if not MULTIMODAL_CLINICAL_FEATURE_COLUMNS_PATH.exists():
        raise RuntimeError(f"artifact_missing: {MULTIMODAL_CLINICAL_FEATURE_COLUMNS_PATH}")
    payload = json.loads(MULTIMODAL_CLINICAL_FEATURE_COLUMNS_PATH.read_text(encoding='utf-8'))
    feature_columns = payload.get('feature_columns')
    if not isinstance(feature_columns, list) or len(feature_columns) != 36:
        raise RuntimeError('multimodal_clinical_schema_unverified: feature_columns must contain 36 entries')
    return [str(value) for value in feature_columns]


def _coerce_multimodal_numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return None
        for separator in (' ', ',', ';', '\t'):
            normalized = normalized.replace(separator, ' ')
        token = normalized.split(' ', 1)[0]
        try:
            return float(token)
        except ValueError:
            return None
    return None


def _multimodal_clinical_feature_values(snapshot: CaseModelInputSnapshot) -> tuple[dict[str, float], dict[str, Any]]:
    mapped = snapshot.mapped_features_json if isinstance(snapshot.mapped_features_json, dict) else {}
    if not mapped:
        raise RuntimeError('clinical_input_insufficient: clinical snapshot missing mapped_features_json')
    feature_columns = _multimodal_runner_feature_columns()
    mapped_keys = list(mapped.keys())
    missing = [feature_name for feature_name in feature_columns if feature_name not in mapped]
    if missing:
        raise RuntimeError(f'clinical_input_insufficient: missing features {missing}')
    extra = [feature_name for feature_name in mapped_keys if feature_name not in feature_columns]
    if extra:
        raise RuntimeError(f'multimodal_clinical_schema_unverified: unexpected features {extra}')

    ordered_snapshot_features: list[str] = []
    provided_features = snapshot.doctor_provided_features_json if isinstance(snapshot.doctor_provided_features_json, list) else []
    for item in provided_features:
        if isinstance(item, dict):
            feature_name = item.get('feature_name') or item.get('model_feature_name')
        else:
            feature_name = item
        feature_name = str(feature_name or '').strip()
        if feature_name:
            ordered_snapshot_features.append(feature_name)

    if not ordered_snapshot_features:
        ordered_snapshot_features = list(mapped_keys)

    if ordered_snapshot_features != feature_columns:
        raise RuntimeError('multimodal_clinical_schema_unverified: snapshot feature order must exactly match artifact order')

    runner_values: dict[str, float] = {}
    invalid: list[str] = []
    for feature_name in feature_columns:
        numeric_value = _coerce_multimodal_numeric_value(mapped.get(feature_name))
        if numeric_value is None:
            invalid.append(feature_name)
            continue
        runner_values[feature_name] = float(numeric_value)
    if invalid:
        raise RuntimeError(f'clinical_input_insufficient: non-numeric features {invalid}')
    summary = {
        'feature_order': feature_columns,
        'feature_order_matches_artifact': ordered_snapshot_features == feature_columns,
        'feature_count': len(feature_columns),
        'translation_mode': 'strict_exact_artifact_order',
        'default_fallback_allowed': False,
        'alias_mapping_allowed': False,
        'translated_from_snapshot_features': list(ordered_snapshot_features),
        'artifact_feature_order': feature_columns,
        'snapshot_feature_order': list(ordered_snapshot_features),
        'mapped_feature_keys': mapped_keys,
        'explicit_default_features': [],
        'snapshot_extra_features': extra,
        'note': 'Snapshot clinical provenance must already match the runner artifact feature order without alias or default fallback.',
    }
    return runner_values, summary


def _multimodal_clinical_payload_contract(snapshot: CaseModelInputSnapshot | None) -> dict[str, Any]:
    required_inputs = [
        'clinical_snapshot_ready_for_inference',
        'current_assessment_status=ready_for_inference',
        'not_for_diagnosis=true',
        'runtime_stub=true',
        'artifact_order=clinical_tabular_standardization_v1.json',
        'full_36_feature_payload',
        'Striated_shadow.1',
        'no_alias_or_default_fallback',
        'snapshot_feature_order_matches_artifact',
    ]
    detected_inputs: dict[str, Any] = {
        'selected_snapshot': _snapshot_summary(snapshot),
        'feature_order_source': str(MULTIMODAL_CLINICAL_FEATURE_COLUMNS_PATH),
        'translation_mode': 'strict_exact_artifact_order',
        'default_fallback_allowed': False,
        'alias_mapping_allowed': False,
        'feature_count': 0,
        'feature_order_matches_artifact': False,
        'missing_required_features': [],
        'invalid_numeric_features': [],
        'extra_snapshot_features': [],
        'artifact_feature_order': [],
        'snapshot_feature_order': [],
        'runner_feature_values': {},
    }
    if snapshot is None:
        return {
            'ready': False,
            'status': BRANCH_STATUS_UNAVAILABLE,
            'disabled_reasons': ['missing_snapshot'],
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'create_controlled_clinical_snapshot',
        }

    validation_status = str(snapshot.validation_status or '').strip().lower()
    assessment_status = str(snapshot.current_assessment_status or '').strip().lower()
    reasons: list[str] = []
    if validation_status == 'schema_unverified' or assessment_status == 'schema_unverified':
        reasons.append('multimodal_clinical_schema_unverified')
    if validation_status != 'ready_for_inference' or assessment_status != 'ready_for_inference':
        reasons.append('clinical_input_insufficient')
    if not bool(snapshot.not_for_diagnosis):
        reasons.append('not_for_diagnosis_false')
    if not bool(snapshot.runtime_stub):
        reasons.append('runtime_safety_not_ready')
    try:
        feature_values, feature_summary = _multimodal_clinical_feature_values(snapshot)
    except RuntimeError as exc:
        message = str(exc)
        detected_inputs['artifact_error'] = message
        if message.startswith('multimodal_clinical_schema_unverified'):
            return {
                'ready': False,
                'status': BRANCH_STATUS_SCHEMA_UNVERIFIED,
                'disabled_reasons': ['multimodal_clinical_schema_unverified'],
                'required_inputs': required_inputs,
                'detected_inputs': detected_inputs,
                'next_action': 'refresh_clinical_validation',
            }
        return {
            'ready': False,
            'status': BRANCH_STATUS_BLOCKED,
            'disabled_reasons': ['clinical_input_insufficient'],
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'repair_clinical_snapshot_payload',
        }

    detected_inputs.update(feature_summary)
    detected_inputs['runner_feature_values'] = feature_values
    detected_inputs['snapshot_validation_status'] = snapshot.validation_status
    detected_inputs['snapshot_current_assessment_status'] = snapshot.current_assessment_status
    detected_inputs['snapshot_not_for_diagnosis'] = bool(snapshot.not_for_diagnosis)
    detected_inputs['snapshot_runtime_stub'] = bool(snapshot.runtime_stub)
    detected_inputs['snapshot_model_input_schema_id'] = snapshot.model_input_schema_id
    detected_inputs['snapshot_disease_task_feature_set_id'] = snapshot.disease_task_feature_set_id

    if feature_summary['feature_count'] != 36:
        reasons.append('multimodal_clinical_schema_unverified')
    if not feature_summary['feature_order_matches_artifact']:
        reasons.append('multimodal_clinical_schema_unverified')

    reasons = list(dict.fromkeys(reasons))
    ready = not reasons
    if ready:
        status = BRANCH_STATUS_READY
        next_action = 'launch_multimodal_resnet18_shadow'
    elif 'multimodal_clinical_schema_unverified' in reasons:
        status = BRANCH_STATUS_SCHEMA_UNVERIFIED
        next_action = 'refresh_clinical_validation'
    else:
        status = BRANCH_STATUS_BLOCKED
        next_action = 'repair_clinical_snapshot_payload'

    return {
        'ready': ready,
        'status': status,
        'disabled_reasons': reasons,
        'required_inputs': required_inputs,
        'detected_inputs': detected_inputs,
        'next_action': next_action,
    }


def _latest_imaging_input(db: Session, case_id: UUID) -> CaseImagingInput | None:
    return db.execute(
        select(CaseImagingInput)
        .where(CaseImagingInput.case_id == case_id)
        .order_by(
            CaseImagingInput.created_at.desc().nullslast(),
            CaseImagingInput.updated_at.desc().nullslast(),
            CaseImagingInput.id.desc(),
        )
    ).scalars().first()


def _latest_ready_imaging_input(db: Session, case_id: UUID) -> CaseImagingInput | None:
    rows = db.execute(
        select(CaseImagingInput)
        .where(CaseImagingInput.case_id == case_id)
        .order_by(
            CaseImagingInput.created_at.desc().nullslast(),
            CaseImagingInput.updated_at.desc().nullslast(),
            CaseImagingInput.id.desc(),
        )
    ).scalars().all()
    for row in rows:
        if _imaging_is_ready(row):
            return row
    return None


def _snapshot_summary(row: CaseModelInputSnapshot | None) -> dict[str, Any]:
    if row is None:
        return {}
    mapped_features = row.mapped_features_json if isinstance(row.mapped_features_json, dict) else {}
    missing_features = list(row.missing_features_json or [])
    defaulted_features = list(row.defaulted_features_json or [])
    doctor_provided_features = list(row.doctor_provided_features_json or [])
    source_refs = list(row.source_refs_json or [])
    return {
        'input_snapshot_id': row.input_snapshot_id,
        'case_id': str(row.case_id),
        'patient_id': str(row.patient_id),
        'trace_id': row.trace_id,
        'model_version_id': str(row.model_version_id),
        'model_input_schema_id': row.model_input_schema_id,
        'disease_task_feature_set_id': row.disease_task_feature_set_id,
        'validation_status': row.validation_status,
        'current_assessment_status': row.current_assessment_status,
        'insufficient_data_for_assessment': bool(row.insufficient_data_for_assessment),
        'runtime_stub': bool(row.runtime_stub),
        'not_for_diagnosis': bool(row.not_for_diagnosis),
        'mapped_feature_count': len(mapped_features),
        'missing_feature_count': len(missing_features),
        'defaulted_feature_count': len(defaulted_features),
        'doctor_provided_feature_count': len(doctor_provided_features),
        'source_ref_count': len(source_refs),
        'created_at': row.created_at.isoformat() if row.created_at else None,
        'updated_at': row.updated_at.isoformat() if row.updated_at else None,
    }


def _imaging_is_ready(row: CaseImagingInput) -> bool:
    return is_ready_preprocessed_imaging_reference(row)

def _imaging_summary(row: CaseImagingInput | None) -> dict[str, Any]:
    if row is None:
        return {}
    state = imaging_preprocessing_state(row)
    return {
        'input_asset_id': row.input_asset_id,
        'case_id': str(row.case_id),
        'patient_id': str(row.patient_id),
        'trace_id': row.trace_id,
        'modality': row.modality,
        'source_type': row.source_type,
        'storage_uri': row.storage_uri,
        'deidentified': bool(row.deidentified),
        'not_for_diagnosis': bool(row.not_for_diagnosis),
        'source_format': state.get('source_format'),
        'preprocessed_format': state.get('preprocessed_format'),
        'preprocessing_status': state.get('preprocessing_status'),
        'candidate_kind': state.get('candidate_kind'),
        'managed_preprocessed_reference': is_ready_preprocessed_imaging_reference(row),
        'ready': _imaging_is_ready(row),
        'created_at': row.created_at.isoformat() if row.created_at else None,
        'updated_at': row.updated_at.isoformat() if row.updated_at else None,
    }


def _clinical_branch(db: Session, case_id: UUID) -> dict[str, Any]:
    latest = _latest_snapshot(db, case_id)
    latest_ready = _latest_ready_snapshot(db, case_id)
    required_inputs = [
        'case_model_input_snapshot',
        'validation_status=ready_for_inference',
        'current_assessment_status=ready_for_inference',
        'not_for_diagnosis=true',
        'runtime_stub=true',
    ]
    if latest_ready is not None:
        return {
            'branch_name': CLINICAL_BRANCH_NAME,
            'status': BRANCH_STATUS_READY,
            'can_run': True,
            'disabled_reasons': [],
            'required_inputs': required_inputs,
            'detected_inputs': {
                'latest_snapshot': _snapshot_summary(latest),
                'ready_snapshot': _snapshot_summary(latest_ready),
                'same_case': True,
            },
            'next_action': 'launch_clinical_mlp_shadow',
        }

    detected_inputs = {
        'latest_snapshot': _snapshot_summary(latest),
        'ready_snapshot': _snapshot_summary(latest_ready),
        'same_case': True,
    }
    if latest is None:
        return {
            'branch_name': CLINICAL_BRANCH_NAME,
            'status': BRANCH_STATUS_UNAVAILABLE,
            'can_run': False,
            'disabled_reasons': ['missing_snapshot'],
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'create_controlled_clinical_snapshot',
        }

    validation_status = str(latest.validation_status or '').strip().lower()
    assessment_status = str(latest.current_assessment_status or '').strip().lower()
    reasons: list[str] = []
    if validation_status == 'schema_unverified' or assessment_status == 'schema_unverified':
        return {
            'branch_name': CLINICAL_BRANCH_NAME,
            'status': BRANCH_STATUS_SCHEMA_UNVERIFIED,
            'can_run': False,
            'disabled_reasons': ['clinical_schema_unverified'],
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'create_or_refresh_clinical_snapshot_validation',
        }
    if validation_status == 'insufficient_data_for_assessment' or assessment_status == 'insufficient_data_for_assessment':
        reasons.append('clinical_input_insufficient')
    if not bool(latest.not_for_diagnosis):
        reasons.append('not_for_diagnosis_false')
    if not bool(latest.runtime_stub):
        reasons.append('runtime_safety_not_ready')
    if not reasons:
        reasons.append('clinical_not_ready')
    return {
        'branch_name': CLINICAL_BRANCH_NAME,
        'status': BRANCH_STATUS_BLOCKED,
        'can_run': False,
        'disabled_reasons': reasons,
        'required_inputs': required_inputs,
        'detected_inputs': detected_inputs,
        'next_action': 'create_controlled_clinical_snapshot',
    }


def _imaging_branch(db: Session, case_id: UUID) -> dict[str, Any]:
    latest = _latest_imaging_input(db, case_id)
    latest_ready = _latest_ready_imaging_input(db, case_id)
    required_inputs = [
        'case_imaging_input',
        'deidentified=true',
        'not_for_diagnosis=true',
        'preprocessed_nifti_or_completed_preprocessing',
    ]
    if latest_ready is not None:
        return {
            'branch_name': IMAGING_BRANCH_NAME,
            'status': BRANCH_STATUS_READY,
            'can_run': True,
            'disabled_reasons': [],
            'required_inputs': required_inputs,
            'detected_inputs': {
                'latest_input': _imaging_summary(latest),
                'ready_input': _imaging_summary(latest_ready),
                'same_case': True,
            },
            'next_action': 'launch_imaging_resnet18_shadow',
        }

    detected_inputs = {
        'latest_input': _imaging_summary(latest),
        'ready_input': _imaging_summary(latest_ready),
        'same_case': True,
    }
    if latest is None:
        return {
            'branch_name': IMAGING_BRANCH_NAME,
            'status': BRANCH_STATUS_UNAVAILABLE,
            'can_run': False,
            'disabled_reasons': ['missing_imaging_input'],
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'register_or_preprocess_imaging_input',
        }

    state = imaging_preprocessing_state(latest)
    source_format = str(state.get('source_format') or '').strip().lower()
    preprocessing_status = str(state.get('preprocessing_status') or '').strip().lower()
    reasons: list[str] = []
    if not bool(latest.deidentified):
        reasons.append('source_not_deidentified')
    if not bool(latest.not_for_diagnosis):
        reasons.append('not_for_diagnosis_false')
    if source_format == 'dicom_series' and preprocessing_status != 'completed':
        return {
            'branch_name': IMAGING_BRANCH_NAME,
            'status': BRANCH_STATUS_PREPROCESSING_REQUIRED,
            'can_run': False,
            'disabled_reasons': ['imaging_preprocessing_required'],
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'run_dicom_preprocessing_preview',
        }
    if state.get('candidate_kind') == 'unsupported_reference' or (not _imaging_is_ready(latest) and preprocessing_status not in {'completed', 'already_preprocessed_candidate'}):
        reasons.append('imaging_input_not_ready')
    if reasons:
        return {
            'branch_name': IMAGING_BRANCH_NAME,
            'status': BRANCH_STATUS_BLOCKED,
            'can_run': False,
            'disabled_reasons': reasons,
            'required_inputs': required_inputs,
            'detected_inputs': detected_inputs,
            'next_action': 'repair_or_replace_imaging_input',
        }
    return {
        'branch_name': IMAGING_BRANCH_NAME,
        'status': BRANCH_STATUS_BLOCKED,
        'can_run': False,
        'disabled_reasons': ['imaging_input_not_ready'],
        'required_inputs': required_inputs,
        'detected_inputs': detected_inputs,
        'next_action': 'repair_or_replace_imaging_input',
    }


def _multimodal_branch(db: Session, case_id: UUID, clinical: dict[str, Any], imaging: dict[str, Any]) -> dict[str, Any]:
    required_inputs = [
        'clinical_mlp_branch_ready',
        'imaging_resnet18_branch_ready',
        'same_case_scope',
        'clinical_snapshot_ready_for_inference',
        'current_assessment_status=ready_for_inference',
        'not_for_diagnosis=true',
        'full_36_feature_payload',
        'Striated_shadow.1',
        'strict_artifact_order=clinical_tabular_standardization_v1.json',
    ]
    clinical_snapshot = _latest_ready_multimodal_snapshot(db, case_id)
    if clinical['can_run'] and imaging['can_run']:
        contract = _multimodal_clinical_payload_contract(clinical_snapshot)
        if not contract['ready']:
            reasons = list(contract['disabled_reasons'] or ['clinical_input_insufficient'])
            return {
                'branch_name': MULTIMODAL_BRANCH_NAME,
                'status': contract['status'] if contract['status'] in {BRANCH_STATUS_SCHEMA_UNVERIFIED, BRANCH_STATUS_BLOCKED, BRANCH_STATUS_UNAVAILABLE} else BRANCH_STATUS_BLOCKED,
                'can_run': False,
                'disabled_reasons': reasons,
                'required_inputs': required_inputs,
                'detected_inputs': {
                    'clinical': clinical['detected_inputs'],
                    'imaging': imaging['detected_inputs'],
                    'clinical_contract': contract['detected_inputs'],
                    'selected_multimodal_snapshot': _snapshot_summary(clinical_snapshot),
                    'fallback_ready_snapshot': _snapshot_summary(_latest_ready_snapshot(db, case_id)),
                    'same_case': True,
                },
                'next_action': contract['next_action'],
            }
        return {
            'branch_name': MULTIMODAL_BRANCH_NAME,
            'status': BRANCH_STATUS_READY,
            'can_run': True,
            'disabled_reasons': [],
            'required_inputs': required_inputs,
            'detected_inputs': {
                'clinical': clinical['detected_inputs'],
                'imaging': imaging['detected_inputs'],
                'clinical_contract': contract['detected_inputs'],
                'selected_multimodal_snapshot': _snapshot_summary(clinical_snapshot),
                'fallback_ready_snapshot': _snapshot_summary(_latest_ready_snapshot(db, case_id)),
                'same_case': True,
            },
            'next_action': 'launch_multimodal_resnet18_shadow',
        }

    reasons = sorted({*clinical['disabled_reasons'], *imaging['disabled_reasons']})
    status = BRANCH_STATUS_BLOCKED
    next_action = 'resolve_clinical_and_imaging_inputs'
    if clinical['status'] == BRANCH_STATUS_SCHEMA_UNVERIFIED:
        status = BRANCH_STATUS_SCHEMA_UNVERIFIED
        next_action = 'refresh_clinical_validation'
    elif imaging['status'] == BRANCH_STATUS_PREPROCESSING_REQUIRED:
        status = BRANCH_STATUS_PREPROCESSING_REQUIRED
        next_action = 'run_dicom_preprocessing_preview'
    elif clinical['status'] == BRANCH_STATUS_UNAVAILABLE or imaging['status'] == BRANCH_STATUS_UNAVAILABLE:
        status = BRANCH_STATUS_UNAVAILABLE
        next_action = 'create_missing_inputs'

    return {
        'branch_name': MULTIMODAL_BRANCH_NAME,
        'status': status,
        'can_run': False,
        'disabled_reasons': reasons or ['multimodal_not_ready'],
        'required_inputs': required_inputs,
        'detected_inputs': {
            'clinical': clinical['detected_inputs'],
            'imaging': imaging['detected_inputs'],
            'clinical_contract': _multimodal_clinical_payload_contract(clinical_snapshot)['detected_inputs'] if clinical_snapshot is not None else {},
            'selected_multimodal_snapshot': _snapshot_summary(clinical_snapshot),
            'fallback_ready_snapshot': _snapshot_summary(_latest_ready_snapshot(db, case_id)),
            'same_case': True,
        },
        'next_action': next_action,
    }


def build_cap_cop_shadow_workflow_readiness(db: Session, case_id: UUID, actor: Any) -> dict[str, Any]:
    case = require_case_access(db, actor, case_id, access_level='summary')
    clinical = _clinical_branch(db, case.id)
    imaging = _imaging_branch(db, case.id)
    multimodal = _multimodal_branch(db, case.id, clinical, imaging)
    branches = {
        CLINICAL_BRANCH_NAME: clinical,
        IMAGING_BRANCH_NAME: imaging,
        MULTIMODAL_BRANCH_NAME: multimodal,
    }
    ready_count = sum(1 for branch in branches.values() if branch['can_run'])
    if ready_count == 3:
        overall_status = WORKFLOW_OVERALL_READY_ALL
    elif ready_count > 0:
        overall_status = WORKFLOW_OVERALL_READY_PARTIAL
    else:
        overall_status = WORKFLOW_OVERALL_BLOCKED
    return {
        'overall_status': overall_status,
        'case_id': str(case.id),
        'patient_id': str(case.patient_id),
        'branches': branches,
        'checked_at': _now().isoformat(),
        'limitations': list(PREVIEW_LIMITATIONS),
    }
