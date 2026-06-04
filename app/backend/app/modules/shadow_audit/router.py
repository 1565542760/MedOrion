from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Case, ShadowInferenceOutput, ShadowInferenceRun
from app.db.session import SessionLocal
from app.modules.shadow_audit.schemas import (
    ShadowInferenceOutputItemV1,
    ShadowInferenceOutputListResponseV1,
    ShadowInferenceRunDetailItemV1,
    ShadowInferenceRunDetailResponseV1,
    ShadowInferenceRunItemV1,
    ShadowInferenceRunListResponseV1,
)

router = APIRouter()


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


@router.get('/shadow-inference-runs/{shadow_run_id}', response_model=ShadowInferenceRunDetailResponseV1)
def get_shadow_run(shadow_run_id: str, db: Session = Depends(get_db)) -> ShadowInferenceRunDetailResponseV1:
    run = db.execute(
        select(ShadowInferenceRun).where(ShadowInferenceRun.shadow_run_id == shadow_run_id)
    ).scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'shadow_run_not_found', 'message': 'Shadow run not found'},
        )

    outputs = db.execute(
        select(ShadowInferenceOutput)
        .where(ShadowInferenceOutput.shadow_run_id == shadow_run_id)
        .order_by(ShadowInferenceOutput.created_at.asc(), ShadowInferenceOutput.output_id.asc())
    ).scalars().all()

    return ShadowInferenceRunDetailResponseV1(
        route='/api/v1/shadow-inference-runs/{shadow_run_id}',
        item=ShadowInferenceRunDetailItemV1.model_validate({
            **_run_item(run).model_dump(),
            'outputs': [_output_item(output) for output in outputs],
        }),
    )


@router.get('/cases/{case_id}/shadow-inference-runs', response_model=ShadowInferenceRunListResponseV1)
def list_shadow_runs_by_case(case_id: str, db: Session = Depends(get_db)) -> ShadowInferenceRunListResponseV1:
    case_uuid = _parse_uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'case_not_found', 'message': 'Case not found'},
        )

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
    run = db.execute(
        select(ShadowInferenceRun).where(ShadowInferenceRun.shadow_run_id == shadow_run_id)
    ).scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'shadow_run_not_found', 'message': 'Shadow run not found'},
        )

    outputs = db.execute(
        select(ShadowInferenceOutput)
        .where(ShadowInferenceOutput.shadow_run_id == shadow_run_id)
        .order_by(ShadowInferenceOutput.created_at.asc(), ShadowInferenceOutput.output_id.asc())
    ).scalars().all()
    return ShadowInferenceOutputListResponseV1(items=[_output_item(output) for output in outputs], total=len(outputs))
