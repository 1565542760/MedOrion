from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.enums import CaseStatus
from app.db.models import Case, InferenceTask, Patient
from app.db.session import SessionLocal
from app.modules.cases.schemas import CaseCreateRequestV1, CaseItemV1, CaseListResponseV1, CaseResponseV1

router = APIRouter()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _latest_trace_id(db: Session, case_id: UUID) -> str:
    trace_id = db.execute(
        select(InferenceTask.trace_id)
        .where(InferenceTask.case_id == case_id)
        .order_by(InferenceTask.created_at.desc(), InferenceTask.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return trace_id or ''


def _item(db: Session, case: Case) -> CaseItemV1:
    return CaseItemV1(
        case_id=str(case.id),
        patient_id=str(case.patient_id),
        case_no=case.case_no or '',
        disease_task=case.disease_domain_code or 'UNSPECIFIED',
        status=case.status.value if hasattr(case.status, 'value') else str(case.status),
        trace_id=_latest_trace_id(db, case.id),
        chief_complaint=case.chief_complaint,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def _resolve_case(db: Session, case_identifier: str) -> Case | None:
    try:
        case_uuid = UUID(case_identifier)
    except ValueError:
        case_uuid = None

    if case_uuid is not None:
        case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
        if case is not None:
            return case

    return db.execute(select(Case).where(Case.case_no == case_identifier)).scalar_one_or_none()


@router.get('', response_model=CaseListResponseV1)
@router.get('/', response_model=CaseListResponseV1, include_in_schema=False)
def list_cases(db: Session = Depends(get_db)) -> CaseListResponseV1:
    rows = db.execute(select(Case).order_by(Case.created_at.desc(), Case.id.desc())).scalars().all()
    items = [_item(db, row) for row in rows]
    return CaseListResponseV1(items=items, total=len(items))


@router.post('', response_model=CaseResponseV1)
@router.post('/', response_model=CaseResponseV1, include_in_schema=False)
def create_case(payload: CaseCreateRequestV1, db: Session = Depends(get_db)) -> CaseResponseV1:
    try:
        patient_uuid = UUID(payload.patient_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_patient_id', 'message': 'patient_id must be a valid UUID'}) from exc

    patient = db.execute(select(Patient).where(Patient.id == patient_uuid)).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'patient_not_found', 'message': 'Patient not found'})

    case_no = payload.case_no or f'MO-CASE-{uuid4().hex[:8].upper()}'
    disease_task = payload.disease_task or 'UNSPECIFIED'
    try:
        case_status = CaseStatus(payload.status or 'open')
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_case_status', 'message': 'Unsupported case status'}) from exc

    case_id = uuid4()

    try:
        db.execute(
            text(
                """
                insert into cases (
                  id, patient_id, case_no, disease_domain_code, title, status, chief_complaint, context_json, opened_at
                ) values (
                  :id, :patient_id, :case_no, :disease_domain_code, :title, :status, :chief_complaint, cast(:context_json as jsonb), :opened_at
                )
                """
            ),
            {
                'id': case_id,
                'patient_id': patient.id,
                'case_no': case_no,
                'disease_domain_code': disease_task,
                'title': payload.chief_complaint or case_no,
                'status': case_status.value,
                'chief_complaint': payload.chief_complaint,
                'context_json': '{}',
                'opened_at': datetime.now(UTC),
            },
        )
        db.commit()
        case = db.execute(select(Case).where(Case.id == case_id)).scalar_one()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'case_conflict', 'message': 'Case already exists or violates unique constraints'}) from exc

    return CaseResponseV1(route='/api/v1/cases', item=_item(db, case))


@router.get('/{case_id}', response_model=CaseResponseV1)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CaseResponseV1:
    case = _resolve_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return CaseResponseV1(route=f'/api/v1/cases/{case_id}', item=_item(db, case))


@router.get('/{case_id}/traces', response_model=CaseResponseV1)
def list_case_traces(case_id: str, db: Session = Depends(get_db)) -> CaseResponseV1:
    case = _resolve_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return CaseResponseV1(route=f'/api/v1/cases/{case_id}/traces', item=_item(db, case))
