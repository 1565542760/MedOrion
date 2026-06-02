from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CaseCreateRequestV1(BaseModel):
    patient_id: str
    case_no: str | None = None
    disease_task: str | None = None
    status: str | None = None
    chief_complaint: str | None = None


class CaseItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    patient_id: str
    case_no: str
    disease_task: str
    status: str
    trace_id: str = ''
    chief_complaint: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CaseResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: CaseItemV1


class CaseListResponseV1(BaseModel):
    items: list[CaseItemV1] = Field(default_factory=list)
    total: int = 0
