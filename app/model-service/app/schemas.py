from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class ModelVersionPolicy(BaseModel):
    mode: str = 'latest_approved'
    pinned_version: str | None = None
    allow_fallback_to_cpu: bool = True
    allow_fallback_to_rule_baseline: bool = True
    no_silent_fallback: bool = True


class ModelInferenceRequestV1(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    trace_id: str | None = None
    inference_task_id: str
    case_id: str
    patient_id: str | None = None
    disease_agent: str
    requested_task: str
    model_version_policy: ModelVersionPolicy
    inputs: dict[str, Any]
    clinical_context_refs: dict[str, Any]
    modality_refs: dict[str, Any]
    missing_value_context: dict[str, Any]
    runtime_options: dict[str, Any]
    idempotency_key: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    retryable: bool = False
    suggested_action: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ModelInferenceResponseV1(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    trace_id: str
    inference_task_id: str
    model_invocation_id: str
    model_id: str
    model_version_id: str
    disease_agent: str
    task_type: str
    status: str
    outputs: dict[str, Any]
    confidence: dict[str, Any]
    uncertainty: dict[str, Any]
    limitations: list[str]
    evidence_nodes_to_create: list[dict[str, Any]]
    evidence_edges_to_create: list[dict[str, Any]]
    trace_events_to_emit: list[dict[str, Any]]
    error: ErrorPayload | None = None
