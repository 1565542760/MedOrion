from pydantic import BaseModel, Field


class CaseInputCreateRequestV1(BaseModel):
    input_type: str | None = None


class CaseInputResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    case_id: str


class CaseInputListResponseV1(BaseModel):
    items: list[CaseInputResponseV1] = Field(default_factory=list)
    total: int = 0
