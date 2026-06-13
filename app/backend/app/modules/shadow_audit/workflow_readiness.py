from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import CaseImagingInput, CaseModelInputSnapshot
from app.modules.shadow_audit.imaging_contract import imaging_preprocessing_state

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
    state = imaging_preprocessing_state(row)
    if not bool(row.deidentified) or not bool(row.not_for_diagnosis):
        return False
    source_format = str(state.get('source_format') or '').strip().lower()
    preprocessed_format = str(state.get('preprocessed_format') or '').strip().lower()
    preprocessing_status = str(state.get('preprocessing_status') or '').strip().lower()
    storage_uri = str(state.get('storage_uri') or '').strip().lower()
    if source_format == 'dicom_series':
        return preprocessing_status == 'completed'
    if preprocessed_format == 'nifti_nii_gz':
        return storage_uri.endswith('.nii') or storage_uri.endswith('.nii.gz') or state.get('candidate_kind') == 'already_preprocessed_candidate'
    return False


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


def _multimodal_branch(clinical: dict[str, Any], imaging: dict[str, Any]) -> dict[str, Any]:
    required_inputs = [
        'clinical_mlp_branch_ready',
        'imaging_resnet18_branch_ready',
        'same_case_scope',
    ]
    if clinical['can_run'] and imaging['can_run']:
        return {
            'branch_name': MULTIMODAL_BRANCH_NAME,
            'status': BRANCH_STATUS_READY,
            'can_run': True,
            'disabled_reasons': [],
            'required_inputs': required_inputs,
            'detected_inputs': {
                'clinical': clinical['detected_inputs'],
                'imaging': imaging['detected_inputs'],
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
            'same_case': True,
        },
        'next_action': next_action,
    }


def build_cap_cop_shadow_workflow_readiness(db: Session, case_id: UUID, actor: Any) -> dict[str, Any]:
    case = require_case_access(db, actor, case_id, access_level='summary')
    clinical = _clinical_branch(db, case.id)
    imaging = _imaging_branch(db, case.id)
    multimodal = _multimodal_branch(clinical, imaging)
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
