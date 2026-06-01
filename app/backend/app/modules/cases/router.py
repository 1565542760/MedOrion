from fastapi import APIRouter

from app.modules.cases.schemas import CaseCreateRequestV1, CaseItemV1, CaseListResponseV1, CaseResponseV1

router = APIRouter()


_DEMO_CASES = [
    CaseItemV1(
        case_id='case-001',
        patient_id='patient-001',
        case_no='MO-CASE-001',
        disease_task='CAP',
        status='open',
        trace_id='trace-demo',
        created_at='2026-06-01T08:00:00Z',
        updated_at='2026-06-01T08:30:00Z',
    )
]


@router.get('', response_model=CaseListResponseV1)
@router.get('/', response_model=CaseListResponseV1, include_in_schema=False)
def list_cases() -> CaseListResponseV1:
    return CaseListResponseV1(items=_DEMO_CASES, total=len(_DEMO_CASES))


@router.post('', response_model=CaseResponseV1)
@router.post('/', response_model=CaseResponseV1, include_in_schema=False)
def create_case(payload: CaseCreateRequestV1) -> CaseResponseV1:
    item = CaseItemV1(
        case_id='case-stub-created',
        patient_id=payload.patient_id,
        case_no=payload.case_no or 'MO-CASE-STUB',
        disease_task=payload.disease_task or 'UNSPECIFIED',
        status='draft',
        trace_id='trace-stub-created',
        created_at='2026-06-01T09:00:00Z',
        updated_at='2026-06-01T09:00:00Z',
    )
    return CaseResponseV1(route='/api/v1/cases', item=item)


@router.get('/{case_id}/traces', response_model=CaseResponseV1)
def list_case_traces(case_id: str) -> CaseResponseV1:
    item = CaseItemV1(
        case_id=case_id,
        patient_id='patient-001',
        case_no='MO-CASE-TRACE',
        disease_task='CAP',
        status='open',
        trace_id='trace-demo',
        created_at='2026-06-01T08:00:00Z',
        updated_at='2026-06-01T08:30:00Z',
    )
    return CaseResponseV1(route=f'/api/v1/cases/{case_id}/traces', item=item)
