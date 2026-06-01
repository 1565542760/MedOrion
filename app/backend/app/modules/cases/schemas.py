from pydantic import BaseModel, Field


class CaseCreateRequestV1(BaseModel):
    patient_id: str
    disease_task: str | None = None
    case_no: str | None = None


class CaseItemV1(BaseModel):
    case_id: str
    patient_id: str
    case_no: str
    disease_task: str
    status: str
    trace_id: str
    created_at: str
    updated_at: str


class CaseResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    item: CaseItemV1


class CaseListResponseV1(BaseModel):
    items: list[CaseItemV1] = Field(default_factory=list)
    total: int = 0
