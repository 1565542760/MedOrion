from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import uuid4

from app.db.enums import PatientConsentStatus
from app.db.models import Patient
from app.db.session import SessionLocal
from app.modules.patients.schemas import PatientCreateRequestV1, PatientItemV1, PatientListResponseV1, PatientResponseV1

router = APIRouter()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _item(patient: Patient) -> PatientItemV1:
    return PatientItemV1(
        patient_id=str(patient.id),
        external_patient_id=patient.external_patient_id,
        display_name=patient.patient_display_id,
        sex=patient.sex,
        birth_date=patient.birth_date,
        consent_status=patient.consent_status.value if hasattr(patient.consent_status, 'value') else str(patient.consent_status),
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


@router.get('', response_model=PatientListResponseV1)
@router.get('/', response_model=PatientListResponseV1, include_in_schema=False)
def list_patients(db: Session = Depends(get_db)) -> PatientListResponseV1:
    rows = db.execute(select(Patient).order_by(Patient.created_at.desc(), Patient.id.desc())).scalars().all()
    items = [_item(row) for row in rows]
    return PatientListResponseV1(items=items, total=len(items))


@router.post('', response_model=PatientResponseV1)
@router.post('/', response_model=PatientResponseV1, include_in_schema=False)
def create_patient(payload: PatientCreateRequestV1, db: Session = Depends(get_db)) -> PatientResponseV1:
    display_name = payload.display_name or payload.name or payload.external_patient_id or 'Unnamed Patient'
    try:
        consent_status = PatientConsentStatus(payload.consent_status or 'unknown')
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_consent_status', 'message': 'Unsupported consent status'}) from exc

    patient_id = uuid4()

    try:
        db.execute(
            text(
                """
                insert into patients (
                  id, external_patient_id, patient_display_id, sex, birth_date, demographics_json, consent_status
                ) values (
                  :id, :external_patient_id, :patient_display_id, :sex, :birth_date, cast(:demographics_json as jsonb), :consent_status
                )
                """
            ),
            {
                'id': patient_id,
                'external_patient_id': payload.external_patient_id,
                'patient_display_id': display_name,
                'sex': payload.sex,
                'birth_date': payload.birth_date,
                'demographics_json': '{}',
                'consent_status': consent_status.value,
            },
        )
        db.commit()
        patient = db.execute(select(Patient).where(Patient.id == patient_id)).scalar_one()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'patient_conflict', 'message': 'Patient already exists or violates unique constraints'}) from exc

    return PatientResponseV1(route='/api/v1/patients', item=_item(patient))
