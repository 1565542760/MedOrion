from pydantic import BaseModel, Field


class RecommendationCreateRequestV1(BaseModel):
    recommendation_type: str | None = None


class RecommendationResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    case_id: str
    trace_id: str | None = None
    confidence: float | None = None
    uncertainty: dict = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[dict] = Field(default_factory=list)


class RecommendationListResponseV1(BaseModel):
    items: list[RecommendationResponseV1] = Field(default_factory=list)
    total: int = 0
