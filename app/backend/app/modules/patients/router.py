from fastapi import APIRouter

from app.modules.patients.schemas import PatientCreateRequestV1, PatientListResponseV1, PatientResponseV1

router = APIRouter()


@router.get('/', response_model=PatientListResponseV1)
def list_patients() -> PatientListResponseV1:
    return PatientListResponseV1()


@router.post('/', response_model=PatientResponseV1)
def create_patient(payload: PatientCreateRequestV1) -> PatientResponseV1:
    return PatientResponseV1(route='/api/v1/patients', patient_id=payload.patient_display_id)
