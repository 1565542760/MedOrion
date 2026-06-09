
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.auth.dependencies import require_roles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Case, ShadowInferenceOutput, ShadowInferenceRun, User
from app.db.session import SessionLocal
from app.modules.shadow_audit.schemas import (
    ControlledShadowClinicalMlpFold5OneShotRequestV1,
    ControlledShadowClinicalMlpFold5OneShotResponseV1,
    ControlledShadowImagingResNet18OneShotRequestV1,
    ControlledShadowImagingResNet18OneShotResponseV1,
    ControlledShadowClinicalMlpRequestV1,
    ControlledShadowClinicalMlpResponseV1,
    RuntimeSafetyConfigItemV1,
    ShadowEligibilityGateItemV1,
    ShadowAuditWriteRequestV1,
    ShadowInferenceOutputItemV1,
    ShadowInferenceOutputListResponseV1,
    ShadowInferenceRunDetailItemV1,
    ShadowInferenceRunDetailResponseV1,
    ShadowInferenceRunItemV1,
    ShadowInferenceRunListResponseV1,
)
from app.modules.shadow_audit.clinical_mlp import run_cap_cop_clinical_mlp_fold5_one_shot_shadow
from app.modules.shadow_audit.imaging_resnet18 import run_controlled_imaging_resnet18_one_shot_shadow
from app.modules.shadow_audit.service import create_shadow_audit_record, run_controlled_cap_cop_clinical_mlp_shadow

router = APIRouter()

ONE_SHOT_ROLES = ['doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin']
one_shot_guard = require_roles(ONE_SHOT_ROLES)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _run_item(row: ShadowInferenceRun) -> ShadowInferenceRunItemV1:
    return ShadowInferenceRunItemV1.model_validate(row)


def _output_item(row: ShadowInferenceOutput) -> ShadowInferenceOutputItemV1:
    return ShadowInferenceOutputItemV1.model_validate(row)


@router.post('/shadow-inference-runs/dev-record', response_model=ShadowInferenceRunDetailResponseV1)
def create_shadow_run_dev_record(payload: ShadowAuditWriteRequestV1, db: Session = Depends(get_db)) -> ShadowInferenceRunDetailResponseV1:
    result = create_shadow_audit_record(db, payload)
    db.commit()
    return ShadowInferenceRunDetailResponseV1(
        status='ok',
        route='/api/v1/shadow-inference-runs/dev-record',
        item=ShadowInferenceRunDetailItemV1.model_validate({**result.run.model_dump(), 'outputs': result.outputs}),
    )


@router.post('/cases/{case_id}/shadow-inference/clinical-mlp', response_model=ControlledShadowClinicalMlpResponseV1)
def run_controlled_shadow_clinical_mlp(
    case_id: str,
    payload: ControlledShadowClinicalMlpRequestV1,
    db: Session = Depends(get_db),
) -> ControlledShadowClinicalMlpResponseV1:
    result = run_controlled_cap_cop_clinical_mlp_shadow(db, case_id, payload)
    db.commit()
    return ControlledShadowClinicalMlpResponseV1(
        status=result.run.status,
        route=f'/api/v1/cases/{case_id}/shadow-inference/clinical-mlp',
        execution_mode=result.execution_mode,
        shadow_disabled=result.shadow_disabled,
        validation=result.validation,
        eligibility=ShadowEligibilityGateItemV1(
            status=result.eligibility.status,
            eligible=result.eligibility.eligible,
            reason=result.eligibility.reason,
            details=result.eligibility.details,
            canonical_adapter_code=result.eligibility.details.get('canonical_adapter_code'),
            runtime_adapter_code=result.eligibility.details.get('runtime_adapter_code'),
            accepted_adapter_codes=list(result.eligibility.details.get('accepted_adapter_codes', [])),
            adapter_match=bool(result.eligibility.details.get('adapter_match', False)),
            runtime_stub=result.eligibility.runtime_stub,
            not_for_diagnosis=result.eligibility.not_for_diagnosis,
            runtime_safety_config=RuntimeSafetyConfigItemV1.model_validate(result.runtime_safety_config),
        ),
        runtime_safety_config=RuntimeSafetyConfigItemV1.model_validate(result.runtime_safety_config),
        item=ShadowInferenceRunDetailItemV1.model_validate({**result.run.model_dump(), 'outputs': result.outputs}),
        limitations=list(result.limitations),
    )


@router.post('/cases/{case_id}/shadow-inference/clinical-mlp/fold5/one-shot', response_model=ControlledShadowClinicalMlpFold5OneShotResponseV1)
def run_fold5_one_shot_shadow_clinical_mlp(
    case_id: str,
    payload: ControlledShadowClinicalMlpFold5OneShotRequestV1,
    db: Session = Depends(get_db),
    actor: User = Depends(one_shot_guard),
) -> ControlledShadowClinicalMlpFold5OneShotResponseV1:
    result = run_cap_cop_clinical_mlp_fold5_one_shot_shadow(db, case_id, actor, payload)
    db.commit()
    output = result.outputs[0] if result.outputs else None
    limitations_json: dict = output.limitations_json if output is not None else {'items': [result.run.error_code or result.run.status]}
    return ControlledShadowClinicalMlpFold5OneShotResponseV1(
        status=result.run.status,
        route=f'/api/v1/cases/{case_id}/shadow-inference/clinical-mlp/fold5/one-shot',
        execution_mode=result.run.runtime_env_json.get('execution_mode', 'one_shot_fold5'),
        shadow_run_id=result.run.shadow_run_id,
        case_id=result.run.case_id,
        patient_id=result.run.patient_id,
        trace_id=result.run.trace_id,
        model_version_id=result.run.model_version_id,
        input_snapshot_id=payload.input_snapshot_id,
        not_for_diagnosis=result.run.not_for_diagnosis,
        runtime_stub=result.run.runtime_stub,
        candidate_label=output.candidate_label if output is not None else None,
        prediction_probability_json=output.prediction_probability_json if output is not None else {},
        confidence_json=output.confidence_json if output is not None else {},
        limitations_json=limitations_json,
        error_code=result.run.error_code,
    )




@router.post('/cases/{case_id}/shadow-inference/imaging-resnet18/one-shot', response_model=ControlledShadowImagingResNet18OneShotResponseV1)
def run_controlled_shadow_imaging_resnet18_one_shot(
    case_id: str,
    payload: ControlledShadowImagingResNet18OneShotRequestV1,
    db: Session = Depends(get_db),
    actor: User = Depends(one_shot_guard),
) -> ControlledShadowImagingResNet18OneShotResponseV1:
    result = run_controlled_imaging_resnet18_one_shot_shadow(db, case_id, actor, payload)
    return ControlledShadowImagingResNet18OneShotResponseV1(
        status=result.status,
        route=f'/api/v1/cases/{case_id}/shadow-inference/imaging-resnet18/one-shot',
        execution_mode=result.execution_mode,
        case_id=result.case_id,
        patient_id=result.patient_id,
        trace_id=result.trace_id,
        input_asset_id=result.input_asset_id,
        resource_type=result.resource_type,
        model_family=result.model_family,
        not_for_diagnosis=result.not_for_diagnosis,
        runtime_stub=result.runtime_stub,
        error_code=result.error_code,
        error_message=result.error_message,
        limitations=list(result.limitations or []),
    )

@router.get('/shadow-inference-runs/{shadow_run_id}', response_model=ShadowInferenceRunDetailResponseV1)
def get_shadow_run(shadow_run_id: str, db: Session = Depends(get_db)) -> ShadowInferenceRunDetailResponseV1:
    run = db.execute(select(ShadowInferenceRun).where(ShadowInferenceRun.shadow_run_id == shadow_run_id)).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'shadow_run_not_found', 'message': 'Shadow run not found'})

    outputs = db.execute(
        select(ShadowInferenceOutput)
        .where(ShadowInferenceOutput.shadow_run_id == shadow_run_id)
        .order_by(ShadowInferenceOutput.created_at.asc(), ShadowInferenceOutput.output_id.asc())
    ).scalars().all()

    return ShadowInferenceRunDetailResponseV1(
        status='ok',
        route='/api/v1/shadow-inference-runs/{shadow_run_id}',
        item=ShadowInferenceRunDetailItemV1.model_validate({**_run_item(run).model_dump(), 'outputs': [_output_item(output) for output in outputs]}),
    )


@router.get('/cases/{case_id}/shadow-inference-runs', response_model=ShadowInferenceRunListResponseV1)
def list_shadow_runs_by_case(case_id: str, db: Session = Depends(get_db)) -> ShadowInferenceRunListResponseV1:
    case_uuid = _parse_uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})

    runs = db.execute(
        select(ShadowInferenceRun)
        .where(ShadowInferenceRun.case_id == case_uuid)
        .order_by(ShadowInferenceRun.started_at.desc().nullslast(), ShadowInferenceRun.created_at.desc())
    ).scalars().all()
    return ShadowInferenceRunListResponseV1(items=[_run_item(run) for run in runs], total=len(runs))


@router.get('/traces/{trace_id}/shadow-inference-runs', response_model=ShadowInferenceRunListResponseV1)
def list_shadow_runs_by_trace(trace_id: str, db: Session = Depends(get_db)) -> ShadowInferenceRunListResponseV1:
    runs = db.execute(
        select(ShadowInferenceRun)
        .where(ShadowInferenceRun.trace_id == trace_id)
        .order_by(ShadowInferenceRun.started_at.desc().nullslast(), ShadowInferenceRun.created_at.desc())
    ).scalars().all()
    return ShadowInferenceRunListResponseV1(items=[_run_item(run) for run in runs], total=len(runs))


@router.get('/shadow-inference-runs/{shadow_run_id}/outputs', response_model=ShadowInferenceOutputListResponseV1)
def list_shadow_outputs(shadow_run_id: str, db: Session = Depends(get_db)) -> ShadowInferenceOutputListResponseV1:
    run = db.execute(select(ShadowInferenceRun).where(ShadowInferenceRun.shadow_run_id == shadow_run_id)).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'shadow_run_not_found', 'message': 'Shadow run not found'})

    outputs = db.execute(
        select(ShadowInferenceOutput)
        .where(ShadowInferenceOutput.shadow_run_id == shadow_run_id)
        .order_by(ShadowInferenceOutput.created_at.asc(), ShadowInferenceOutput.output_id.asc())
    ).scalars().all()
    return ShadowInferenceOutputListResponseV1(items=[_output_item(output) for output in outputs], total=len(outputs))
