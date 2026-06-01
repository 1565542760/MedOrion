from fastapi import APIRouter

from app.modules.clinical.schemas import (
    MissingValueQueryCreateRequestV1,
    MissingValueQueryListResponseV1,
    MissingValueQueryResponseV1,
)

router = APIRouter()


@router.get('/cases/{case_id}/missing-values', response_model=MissingValueQueryListResponseV1)
def list_missing_values(case_id: str) -> MissingValueQueryListResponseV1:
    return MissingValueQueryListResponseV1(
        items=[MissingValueQueryResponseV1(route=f'/api/v1/cases/{case_id}/missing-values', case_id=case_id)]
    )


@router.post('/cases/{case_id}/missing-values', response_model=MissingValueQueryResponseV1)
def create_missing_value_query(case_id: str, payload: MissingValueQueryCreateRequestV1) -> MissingValueQueryResponseV1:
    _ = payload
    return MissingValueQueryResponseV1(route=f'/api/v1/cases/{case_id}/missing-values', case_id=case_id)
