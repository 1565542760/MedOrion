
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Case, ModelRegistry, ModelVersion, ShadowInferenceOutput, ShadowInferenceRun
from app.modules.model_input.router import build_model_input_assessment_from_schema, build_model_input_schema_for_version
from app.modules.shadow_audit.eligibility import ShadowEligibilityResult, evaluate_cap_cop_clinical_mlp_shadow_eligibility, runtime_safety_config_summary
from app.modules.shadow_audit.schemas import (
    ControlledShadowClinicalMlpRequestV1,
    ShadowAuditWriteRequestV1,
    ShadowInferenceOutputItemV1,
    ShadowInferenceRunItemV1,
)

_ALLOWED_STATUSES = {
    'shadow_success',
    'shadow_failed',
    'shadow_disabled',
    'shadow_timeout',
    'shadow_insufficient_input',
    'shadow_model_not_enabled',
}

_CONTROLLED_SHADOW_ADAPTER_CODE = settings.cap_cop_clinical_mlp_shadow_runtime_adapter_code


@dataclass(frozen=True)
class ShadowAuditWriteResult:
    run: ShadowInferenceRunItemV1
    outputs: list[ShadowInferenceOutputItemV1]


@dataclass(frozen=True)
class ControlledShadowClinicalMlpResult:
    run: ShadowInferenceRunItemV1
    outputs: list[ShadowInferenceOutputItemV1]
    validation: object
    eligibility: ShadowEligibilityResult
    runtime_safety_config: dict[str, Any]
    shadow_disabled: bool
    execution_mode: str
    limitations: list[str]


def _parse_uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _require_case(db: Session, case_id: str) -> tuple[UUID, Case]:
    case_uuid = _parse_uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return case_uuid, case


def _require_model_version(db: Session, model_version_id: UUID) -> tuple[ModelRegistry, ModelVersion]:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == version.model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    return model, version


def _artifact_hash_from_version(version: ModelVersion, *, allow_placeholder: bool) -> str | None:
    raw = version.artifact_ref_json
    if isinstance(raw, dict):
        artifact_hash = raw.get('artifact_hash')
        if isinstance(artifact_hash, str) and artifact_hash.strip():
            return artifact_hash.strip()
        artifact_uri = raw.get('artifact_uri')
        if isinstance(artifact_uri, str) and artifact_uri.strip() and allow_placeholder:
            return 'metadata_only'
    elif isinstance(raw, str) and raw.strip():
        return raw.strip()
    if allow_placeholder:
        return 'metadata_only'
    return None


def create_shadow_audit_record(db: Session, payload: ShadowAuditWriteRequestV1) -> ShadowAuditWriteResult:
    if not payload.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_flag', 'message': 'not_for_diagnosis must be true'})
    if not payload.runtime_stub:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_flag', 'message': 'runtime_stub must be true'})

    if payload.status not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_status', 'message': 'Unsupported shadow status'})

    case_uuid, _case = _require_case(db, payload.case_id)
    model_version_uuid = _parse_uuid(str(payload.model_version_id), 'invalid_model_version_id', 'Invalid model version id')
    model_version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_uuid)).scalar_one_or_none()
    if model_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    trace_id = payload.trace_id.strip()
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_trace_id', 'message': 'trace_id is required'})

    idempotency_seed = payload.idempotency_key or f'{trace_id}:{case_uuid}:{model_version_uuid}:{payload.adapter_code}'
    shadow_run_id = f'shadow_{uuid5(NAMESPACE_URL, idempotency_seed).hex[:16]}'
    existing_run = db.execute(select(ShadowInferenceRun).where(ShadowInferenceRun.shadow_run_id == shadow_run_id)).scalar_one_or_none()
    if existing_run is not None:
        existing_outputs = db.execute(
            select(ShadowInferenceOutput)
            .where(ShadowInferenceOutput.shadow_run_id == shadow_run_id)
            .order_by(ShadowInferenceOutput.created_at.asc(), ShadowInferenceOutput.output_id.asc())
        ).scalars().all()
        return ShadowAuditWriteResult(
            run=ShadowInferenceRunItemV1.model_validate(existing_run),
            outputs=[ShadowInferenceOutputItemV1.model_validate(output) for output in existing_outputs],
        )

    patient_uuid = _parse_uuid(payload.patient_id, 'invalid_patient_id', 'Invalid patient id') if payload.patient_id else db.execute(select(Case.patient_id).where(Case.id == case_uuid)).scalar_one()
    run = ShadowInferenceRun(
        shadow_run_id=shadow_run_id,
        trace_id=trace_id,
        case_id=case_uuid,
        patient_id=patient_uuid,
        model_version_id=model_version_uuid,
        artifact_hash=payload.artifact_hash,
        adapter_code=payload.adapter_code,
        model_input_schema_id=payload.model_input_schema_id,
        input_snapshot_id=payload.input_snapshot_id,
        status=payload.status,
        runtime_env_json=dict(payload.runtime_env_json or {}),
        runtime_stub=True,
        not_for_diagnosis=True,
        started_at=payload.started_at or datetime.now(UTC),
        completed_at=payload.completed_at,
        duration_ms=payload.duration_ms,
        error_code=payload.error_code,
        error_detail_json=dict(payload.error_detail_json or {}),
    )
    db.add(run)
    db.flush()

    output_items: list[ShadowInferenceOutputItemV1] = []
    if isinstance(payload.output, dict):
        output = ShadowInferenceOutput(
            output_id=f'out_{uuid5(NAMESPACE_URL, f"{trace_id}:{run.shadow_run_id}:{model_version_uuid}").hex[:16]}',
            shadow_run_id=run.shadow_run_id,
            trace_id=trace_id,
            case_id=case_uuid,
            model_version_id=model_version_uuid,
            prediction_raw_json=dict(payload.output.get('prediction_raw_json') or {}),
            prediction_probability_json=dict(payload.output.get('prediction_probability_json') or {}),
            candidate_label=payload.output.get('candidate_label'),
            confidence_json=dict(payload.output.get('confidence_json') or {}),
            uncertainty_json=dict(payload.output.get('uncertainty_json') or {}),
            limitations_json=dict(payload.output.get('limitations_json') or {}),
            input_quality_flags_json=dict(payload.output.get('input_quality_flags_json') or {}),
        )
        db.add(output)
        db.flush()
        output_items.append(ShadowInferenceOutputItemV1.model_validate(output))

    return ShadowAuditWriteResult(run=ShadowInferenceRunItemV1.model_validate(run), outputs=output_items)


def run_controlled_cap_cop_clinical_mlp_shadow(
    db: Session,
    case_id: str,
    payload: ControlledShadowClinicalMlpRequestV1,
) -> ControlledShadowClinicalMlpResult:
    if not payload.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_flag', 'message': 'not_for_diagnosis must be true'})
    if not payload.runtime_stub:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_flag', 'message': 'runtime_stub must be true'})

    case_uuid, case = _require_case(db, case_id)
    model, version = _require_model_version(db, payload.model_version_id)
    schema_item = build_model_input_schema_for_version(model, version)
    assessment = build_model_input_assessment_from_schema(schema_item, payload.provided_features)
    eligibility_preview = evaluate_cap_cop_clinical_mlp_shadow_eligibility(
        db,
        model_version_id=payload.model_version_id,
        provided_features=payload.provided_features,
        available_modalities=payload.available_modalities,
        respect_global_switch=False,
    )

    runtime_safety_config = runtime_safety_config_summary()
    adapter_governance = eligibility_preview.details if isinstance(eligibility_preview.details, dict) else {}
    limitations = [
        'shadow_audit_only',
        'not_for_diagnosis',
        'disabled_by_default',
        'no_real_model_loaded',
        'no_case_trace_write',
        'runtime_safety_config_skeleton',
    ]
    runtime_env = {
        'shadow_gate_enabled': bool(settings.enable_cap_cop_clinical_mlp_shadow),
        'execution_mode': 'disabled_by_default' if not settings.enable_cap_cop_clinical_mlp_shadow else 'controlled_shadow_stub',
        'shadow_candidate': 'cap_cop_clinical_mlp_fold5',
        'model_family': 'clinical_mlp',
        'disease_task': schema_item.disease_task,
        'feature_count': schema_item.feature_count,
        'mapped_feature_count': assessment.mapped_feature_count,
        'current_assessment_status': assessment.current_assessment_status,
        'missing_required_features': assessment.missing_required_features,
        'default_strategy_available': assessment.default_strategy_available,
        'runtime_stub': True,
        'not_for_diagnosis': True,
        'no_silent_fallback': True,
        'available_modalities': list(payload.available_modalities),
        'runtime_options_json': dict(payload.runtime_options_json or {}),
        'runtime_safety_config': runtime_safety_config,
        'canonical_adapter_code': adapter_governance.get('canonical_adapter_code'),
        'runtime_adapter_code': adapter_governance.get('runtime_adapter_code'),
        'accepted_adapter_codes': adapter_governance.get('accepted_adapter_codes', []),
        'adapter_match': adapter_governance.get('adapter_match', False),
        'eligibility_status': eligibility_preview.status,
        'eligibility_reason': eligibility_preview.reason,
        'eligibility_details': eligibility_preview.details,
    }
    started_at = datetime.now(UTC)
    completed_at = started_at
    base_detail = {
        'shadow_candidate': 'cap_cop_clinical_mlp_fold5',
        'model_input_schema_id': schema_item.model_input_schema_id,
        'disease_task_feature_set_id': schema_item.disease_task_feature_set_id,
        'current_assessment_status': assessment.current_assessment_status,
        'missing_required_features': assessment.missing_required_features,
        'default_strategy_available': assessment.default_strategy_available,
        'suggested_doctor_questions': assessment.suggested_doctor_questions,
        'runtime_stub': True,
        'not_for_diagnosis': True,
        'runtime_safety_config': runtime_safety_config,
        'eligibility_status': eligibility_preview.status,
        'eligibility_reason': eligibility_preview.reason,
        'eligibility_details': eligibility_preview.details,
    }

    if not settings.enable_cap_cop_clinical_mlp_shadow:
        artifact_hash = _artifact_hash_from_version(version, allow_placeholder=True) or 'metadata_only'
        status_code = 'shadow_disabled'
        error_code = 'shadow_disabled'
        error_detail = {
            **base_detail,
            'code': 'shadow_disabled',
            'message': 'CAP/COP clinical MLP shadow execution is disabled by backend configuration',
            'shadow_gate': 'ENABLE_CAP_COP_CLINICAL_MLP_SHADOW',
        }
        output_payload = None
        shadow_disabled = True
        execution_mode = 'disabled_by_default'
    elif eligibility_preview.status == 'input_insufficient':
        artifact_hash = _artifact_hash_from_version(version, allow_placeholder=True) or 'metadata_only'
        status_code = 'shadow_insufficient_input'
        error_code = 'insufficient_data_for_assessment'
        error_detail = {
            **base_detail,
            'code': 'insufficient_data_for_assessment',
            'message': 'Required inputs are insufficient for controlled shadow execution',
            'missing_required_features': assessment.missing_required_features,
        }
        output_payload = None
        shadow_disabled = False
        execution_mode = 'validation_only'
    elif eligibility_preview.status != 'eligible':
        artifact_hash = _artifact_hash_from_version(version, allow_placeholder=True) or 'metadata_only'
        status_code = 'shadow_model_not_enabled'
        error_code = eligibility_preview.status
        error_detail = {
            **base_detail,
            'code': eligibility_preview.status,
            'message': eligibility_preview.reason or 'Model is not eligible for controlled shadow execution',
            'eligibility_details': eligibility_preview.details,
        }
        output_payload = None
        shadow_disabled = False
        execution_mode = 'eligibility_blocked'
    else:
        artifact_hash = _artifact_hash_from_version(version, allow_placeholder=False)
        if artifact_hash is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={'code': 'shadow_model_not_enabled', 'message': 'No approved artifact hash is available for controlled shadow execution'},
            )
        score = round(assessment.mapped_feature_count / max(assessment.feature_count, 1), 3)
        status_code = 'shadow_success'
        error_code = None
        error_detail = {}
        output_payload = {
            'prediction_raw_json': {
                'shadow_execution': 'controlled_shadow_stub',
                'candidate_model_version_id': str(version.id),
                'model_input_schema_id': schema_item.model_input_schema_id,
                'disease_task_feature_set_id': schema_item.disease_task_feature_set_id,
                'feature_count': schema_item.feature_count,
                'mapped_feature_count': assessment.mapped_feature_count,
                'current_assessment_status': assessment.current_assessment_status,
                'runtime_stub': True,
                'not_for_diagnosis': True,
            },
            'prediction_probability_json': {'shadow_score': score},
            'candidate_label': 'shadow_stub_not_for_diagnosis',
            'confidence_json': {'score': score, 'source': 'shadow_stub'},
            'uncertainty_json': {'note': 'no real model loaded', 'source': 'shadow_stub'},
            'limitations_json': [
                'shadow_audit_only',
                'not_for_diagnosis',
                'controlled_shadow_stub',
                'no_real_model_loaded',
                'no_case_trace_write',
            ],
            'input_quality_flags_json': {
                'missing_required_features': assessment.missing_required_features,
                'default_strategy_available': assessment.default_strategy_available,
                'insufficient_data_for_assessment': assessment.insufficient_data_for_assessment,
            },
        }
        shadow_disabled = False
        execution_mode = 'controlled_shadow_stub'
        limitations = [
            'shadow_audit_only',
            'not_for_diagnosis',
            'controlled_shadow_stub',
            'no_real_model_loaded',
            'no_case_trace_write',
            'runtime_safety_config_skeleton',
        ]

    input_snapshot_text = f'{case_uuid}:{version.id}:{schema_item.model_input_schema_id}:{assessment.current_assessment_status}:{sorted(str(key) for key in payload.provided_features.keys())}'
    write_payload = ShadowAuditWriteRequestV1(
        trace_id=payload.trace_id,
        case_id=case_uuid,
        model_version_id=version.id,
        artifact_hash=artifact_hash,
        adapter_code=_CONTROLLED_SHADOW_ADAPTER_CODE,
        status=status_code,
        not_for_diagnosis=True,
        runtime_stub=True,
        patient_id=str(case.patient_id),
        model_input_schema_id=uuid5(NAMESPACE_URL, schema_item.model_input_schema_id),
        input_snapshot_id=uuid5(NAMESPACE_URL, input_snapshot_text),
        runtime_env_json=runtime_env,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=0,
        error_code=error_code,
        error_detail_json=error_detail,
        output=output_payload,
    )
    audit_result = create_shadow_audit_record(db, write_payload)
    return ControlledShadowClinicalMlpResult(
        run=audit_result.run,
        outputs=audit_result.outputs,
        validation=assessment,
        eligibility=eligibility_preview,
        runtime_safety_config=runtime_safety_config,
        shadow_disabled=shadow_disabled,
        execution_mode=execution_mode,
        limitations=limitations,
    )
