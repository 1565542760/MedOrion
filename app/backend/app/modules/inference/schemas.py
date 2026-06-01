from pydantic import BaseModel, Field


class ModelInferenceRequestV1(BaseModel):
    case_id: str
    disease_agent: str | None = None
    input_refs: list[dict] = Field(default_factory=list)


class ModelInferenceResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    task_id: str | None = None
    trace_id: str | None = None


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
