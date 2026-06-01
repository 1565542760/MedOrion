from pydantic import BaseModel, Field


class QualityReviewCreateRequestV1(BaseModel):
    trace_id: str | None = None


class QualityReviewResponseV1(BaseModel):
    status: str = 'stub'
    route: str


class QualityReviewListResponseV1(BaseModel):
    items: list[QualityReviewResponseV1] = Field(default_factory=list)
    total: int = 0
