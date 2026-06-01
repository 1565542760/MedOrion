from pydantic import BaseModel, Field


class ModelInferenceRequestV1(BaseModel):
    case_id: str | None = None
    patient_id: str | None = None
    disease_agent: str = 'capcop_agent'
    requested_task: str = 'risk_assessment'
    model_version_policy: dict = Field(default_factory=lambda: {'mode': 'latest_approved', 'pinned_version': 'capcop_stub_v1'})
    inputs: dict = Field(default_factory=dict)
    missing_value_context: dict = Field(default_factory=dict)
    idempotency_key: str | None = None


class RecommendationStubV1(BaseModel):
    trace_id: str
    inference_task_id: str
    model_version_id: str
    confidence: dict = Field(default_factory=dict)
    uncertainty: dict = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[dict] = Field(default_factory=list)


class ModelInferenceResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    task_id: str
    trace_id: str
    model_invocation_id: str | None = None
    model_version_id: str | None = None
    confidence: dict = Field(default_factory=dict)
    uncertainty: dict = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    recommendation: RecommendationStubV1 | None = None
    model_service: dict = Field(default_factory=dict)


class InferenceTaskResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    task_id: str


class ReassessmentJobCreateRequestV1(BaseModel):
    case_id: str


class ReassessmentJobResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    job_id: str | None = None
