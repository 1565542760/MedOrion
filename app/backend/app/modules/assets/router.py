from fastapi import APIRouter

from app.modules.assets.schemas import CaseInputCreateRequestV1, CaseInputListResponseV1, CaseInputResponseV1

router = APIRouter()


@router.get('/cases/{case_id}/inputs', response_model=CaseInputListResponseV1)
def list_case_inputs(case_id: str) -> CaseInputListResponseV1:
    return CaseInputListResponseV1(items=[CaseInputResponseV1(route=f'/api/v1/cases/{case_id}/inputs', case_id=case_id)])


@router.post('/cases/{case_id}/inputs', response_model=CaseInputResponseV1)
def create_case_input(case_id: str, payload: CaseInputCreateRequestV1) -> CaseInputResponseV1:
    _ = payload
    return CaseInputResponseV1(route=f'/api/v1/cases/{case_id}/inputs', case_id=case_id)
