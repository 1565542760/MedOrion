from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QualityReviewCreateRequestV1(BaseModel):
    case_id: str
    trace_id: str | None = None
    target_type: str
    target_id: str
    status: str = 'open'
    attribution: str
    severity: str = 'medium'
    summary: str
    related_feedback_id: str | None = None
    attribution_confidence: float | None = None


class QualityReviewItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    case_id: str
    trace_id: str
    target_type: str
    target_id: str
    status: str
    attribution: str | None = None
    severity: str
    summary: str
    related_feedback_id: str | None = None
    actor_type: str
    actor_id: str | None = None
    attribution_confidence: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class QualityReviewResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: QualityReviewItemV1


class QualityReviewListResponseV1(BaseModel):
    items: list[QualityReviewItemV1] = Field(default_factory=list)
    total: int = 0
