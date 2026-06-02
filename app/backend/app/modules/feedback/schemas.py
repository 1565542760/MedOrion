from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DoctorFeedbackCreateRequestV1(BaseModel):
    case_id: str
    recommendation_id: str
    trace_id: str | None = None
    feedback_type: str
    feedback_text: str | None = None
    doctor_decision: str | None = None
    rating: int | None = None
    learning_eligible: bool = True


class DoctorFeedbackItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feedback_id: str
    case_id: str
    trace_id: str
    recommendation_id: str | None = None
    feedback_type: str
    feedback_text: str | None = None
    doctor_decision: str | None = None
    rating: int | None = None
    doctor_id: str | None = None
    learning_eligible: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DoctorFeedbackResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: DoctorFeedbackItemV1


class DoctorFeedbackListResponseV1(BaseModel):
    items: list[DoctorFeedbackItemV1] = Field(default_factory=list)
    total: int = 0
