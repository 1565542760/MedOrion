from pydantic import BaseModel, Field


class DoctorFeedbackCreateRequestV1(BaseModel):
    case_id: str


class DoctorFeedbackResponseV1(BaseModel):
    status: str = 'stub'
    route: str


class DoctorFeedbackListResponseV1(BaseModel):
    items: list[DoctorFeedbackResponseV1] = Field(default_factory=list)
    total: int = 0
