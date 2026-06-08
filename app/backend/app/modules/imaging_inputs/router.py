
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import CaseImagingInput
from app.db.session import SessionLocal
from app.modules.auth.dependencies import require_roles
from app.modules.inference.persistence import resolve_case_context
from app.modules.imaging_inputs.schemas import (
    ImagingInputCreateRequestV1,
    ImagingInputCreateResponseV1,
    ImagingInputDetailResponseV1,
    ImagingInputListResponseV1,
    ImagingInputSummaryItemV1,
    ImagingInputItemV1,
)

router = APIRouter()
logger = logging.getLogger('app.imaging_inputs')

IMAGING_INPUT_READ_ROLES = ['doctor', 'admin', 'super_admin']
IMAGING_INPUT_WRITE_ROLES = ['doctor', 'admin', 'super_admin']
imaging_input_read_guard = require_roles(IMAGING_INPUT_READ_ROLES)
imaging_input_write_guard = require_roles(IMAGING_INPUT_WRITE_ROLES)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _resolve_case_context_or_404(db: Session, case_identifier: str) -> tuple[UUID, UUID]:
    try:
        case_id_text, patient_id_text = resolve_case_context(db, case_identifier)
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'code': 'case_not_found', 'message': 'Case not found'},
            ) from exc
        raise
    return UUID(case_id_text), UUID(patient_id_text)


def _normalize_text(value: str | None) -> str:
    return (value or '').strip()


def _summary_item(row: CaseImagingInput) -> ImagingInputSummaryItemV1:
    return ImagingInputSummaryItemV1(
        id=row.id,
        input_asset_id=row.input_asset_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        modality=row.modality,
        source_type=row.source_type,
        deidentified=row.deidentified,
        not_for_diagnosis=row.not_for_diagnosis,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _detail_item(row: CaseImagingInput) -> ImagingInputItemV1:
    return ImagingInputItemV1(
        id=row.id,
        input_asset_id=row.input_asset_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        modality=row.modality,
        source_type=row.source_type,
        storage_uri=row.storage_uri,
        deidentified=row.deidentified,
        not_for_diagnosis=row.not_for_diagnosis,
        provenance_json=dict(row.provenance_json or {}),
        quality_flags_json=dict(row.quality_flags_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post('/cases/{case_id}/imaging-inputs', response_model=ImagingInputCreateResponseV1)
def create_imaging_input(
    case_id: str,
    payload: ImagingInputCreateRequestV1,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_write_guard),
) -> ImagingInputCreateResponseV1:
    resolved_case_id, resolved_patient_id = _resolve_case_context_or_404(db, case_id)
    if payload.patient_id != resolved_patient_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'patient_mismatch', 'message': 'Patient does not match the case'},
        )

    require_case_access(db, user, str(resolved_case_id), access_level='detail')

    input_asset_id = f'img_{uuid4().hex}'
    row = CaseImagingInput(
        input_asset_id=input_asset_id,
        case_id=resolved_case_id,
        patient_id=resolved_patient_id,
        trace_id=_normalize_text(payload.trace_id),
        modality=payload.modality,
        source_type=payload.source_type,
        storage_uri=_normalize_text(payload.storage_uri),
        deidentified=True,
        not_for_diagnosis=True,
        provenance_json=dict(payload.provenance_json or {}),
        quality_flags_json=dict(payload.quality_flags_json or {}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ImagingInputCreateResponseV1(
        status='created',
        route='/cases/{case_id}/imaging-inputs',
        item=_detail_item(row),
    )


@router.get('/cases/{case_id}/imaging-inputs', response_model=ImagingInputListResponseV1)
def list_imaging_inputs(
    case_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(imaging_input_read_guard),
) -> ImagingInputListResponseV1:
    resolved_case_id, _resolved_patient_id = _resolve_case_context_or_404(db, case_id)
    require_case_access(db, user, str(resolved_case_id), access_level='summary')

    base_query = select(CaseImagingInput).where(CaseImagingInput.case_id == resolved_case_id)
    total = db.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    rows = db.execute(
        base_query.order_by(CaseImagingInput.created_at.desc(), CaseImagingInput.id.desc()).offset(offset).limit(limit)
    ).scalars().all()
    return ImagingInputListResponseV1(
        status='ok',
        route='/cases/{case_id}/imaging-inputs',
        total=total,
        limit=limit,
        offset=offset,
        items=[_summary_item(row) for row in rows],
    )


@router.get('/imaging-inputs/{input_asset_id}', response_model=ImagingInputDetailResponseV1)
def get_imaging_input(
    input_asset_id: str,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_read_guard),
) -> ImagingInputDetailResponseV1:
    row = db.execute(
        select(CaseImagingInput).where(CaseImagingInput.input_asset_id == input_asset_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'imaging_input_not_found', 'message': 'Imaging input not found'},
        )
    require_case_access(db, user, str(row.case_id), access_level='detail')
    return ImagingInputDetailResponseV1(
        status='ok',
        route='/imaging-inputs/{input_asset_id}',
        item=_detail_item(row),
    )
