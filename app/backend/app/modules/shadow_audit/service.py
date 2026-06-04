from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Case, ModelVersion, ShadowInferenceOutput, ShadowInferenceRun
from app.modules.shadow_audit.schemas import ShadowAuditWriteRequestV1, ShadowInferenceOutputItemV1, ShadowInferenceRunItemV1

_ALLOWED_STATUSES = {
    'shadow_success',
    'shadow_failed',
    'shadow_disabled',
    'shadow_timeout',
    'shadow_insufficient_input',
    'shadow_model_not_enabled',
}


@dataclass(frozen=True)
class ShadowAuditWriteResult:
    run: ShadowInferenceRunItemV1
    outputs: list[ShadowInferenceOutputItemV1]


def _parse_uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _require_case(db: Session, case_id: str) -> UUID:
    case_uuid = _parse_uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return case_uuid


def _require_model_version(db: Session, model_version_id: str) -> UUID:
    model_version_uuid = _parse_uuid(model_version_id, 'invalid_model_version_id', 'Invalid model version id')
    model_version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_uuid)).scalar_one_or_none()
    if model_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    return model_version_uuid


def create_shadow_audit_record(db: Session, payload: ShadowAuditWriteRequestV1) -> ShadowAuditWriteResult:
    if not payload.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_flag', 'message': 'not_for_diagnosis must be true'})
    if not payload.runtime_stub:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_flag', 'message': 'runtime_stub must be true'})

    if payload.status not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_shadow_status', 'message': 'Unsupported shadow status'})

    case_uuid = _require_case(db, payload.case_id)
    model_version_uuid = _require_model_version(db, payload.model_version_id)
    trace_id = payload.trace_id.strip()
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_trace_id', 'message': 'trace_id is required'})

    patient_uuid = _parse_uuid(payload.patient_id, 'invalid_patient_id', 'Invalid patient id') if payload.patient_id else db.execute(select(Case.patient_id).where(Case.id == case_uuid)).scalar_one()
    run = ShadowInferenceRun(
        shadow_run_id=f'shadow_{uuid4().hex[:16]}',
        trace_id=trace_id,
        case_id=case_uuid,
        patient_id=patient_uuid,
        model_version_id=model_version_uuid,
        artifact_hash=payload.artifact_hash,
        adapter_code=payload.adapter_code,
        model_input_schema_id=_parse_uuid(payload.model_input_schema_id, 'invalid_model_input_schema_id', 'Invalid model input schema id') if payload.model_input_schema_id else None,
        input_snapshot_id=_parse_uuid(payload.input_snapshot_id, 'invalid_input_snapshot_id', 'Invalid input snapshot id') if payload.input_snapshot_id else None,
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
            output_id=f'out_{uuid4().hex[:16]}',
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
