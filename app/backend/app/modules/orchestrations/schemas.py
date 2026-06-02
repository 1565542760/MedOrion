
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OrchestrationMode(str, Enum):
    single_agent = 'single_agent'
    parallel_agents = 'parallel_agents'
    serial_agents = 'serial_agents'
    triage_then_specialist = 'triage_then_specialist'
    conflict_aware_summary = 'conflict_aware_summary'


class OrchestrationStepStatus(str, Enum):
    planned = 'planned'
    running = 'running'
    completed = 'completed'
    failed = 'failed'
    skipped = 'skipped'


class OrchestrationRequestBaseV1(BaseModel):
    trace_id: str
    case_id: str
    patient_id: str
    orchestration_mode: OrchestrationMode
    requested_task: str
    candidate_agents: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    clinical_context_refs: dict[str, Any] = Field(default_factory=dict)
    modality_refs: dict[str, Any] = Field(default_factory=dict)
    runtime_options: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class OrchestrationValidatePlanRequestV1(OrchestrationRequestBaseV1):
    pass


class OrchestrationRunRequestV1(OrchestrationRequestBaseV1):
    pass


class OrchestrationStepV1(BaseModel):
    step_id: str
    step_type: str
    step_index: int | None = None
    agent_code: str | None = None
    model_version_id: str | None = None
    status: OrchestrationStepStatus = OrchestrationStepStatus.planned
    duration_ms: int | None = None
    agent_invocation_id: str | None = None
    model_invocation_id: str | None = None
    summary: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class OrchestrationAgentInvocationV1(BaseModel):
    step_id: str
    agent_code: str
    agent_invocation_id: str
    model_version_id: str | None = None
    status: str = 'pending'
    duration_ms: int | None = None
    model_service_response: dict[str, Any] = Field(default_factory=dict)


class OrchestrationConflictV1(BaseModel):
    conflict_id: str
    trace_id: str | None = None
    case_id: str | None = None
    patient_id: str | None = None
    orchestration_run_id: str | None = None
    step_id: str | None = None
    conflict_type: str = 'stub'
    agents: list[str] = Field(default_factory=list)
    reason: str
    resolution: str | None = None
    status: str = 'stub'
    payload_json: dict[str, Any] = Field(default_factory=dict)
    result_json: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_detail_json: dict[str, Any] = Field(default_factory=dict)
    runtime_stub: bool = True


class OrchestrationStubSummaryV1(BaseModel):
    title: str
    body: str
    rationale: list[str] = Field(default_factory=list)
    runtime_stub: bool = True


class OrchestrationValidatePlanResponseV1(BaseModel):
    status: str = 'validated'
    route: str
    trace_id: str
    orchestration_run_id: str
    mode: OrchestrationMode
    requested_task: str
    steps: list[OrchestrationStepV1] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    runtime_stub: bool = True


class OrchestrationRunResponseV1(BaseModel):
    status: str = 'completed'
    route: str
    trace_id: str
    orchestration_run_id: str
    mode: OrchestrationMode
    requested_task: str
    steps: list[OrchestrationStepV1] = Field(default_factory=list)
    agent_invocations: list[OrchestrationAgentInvocationV1] = Field(default_factory=list)
    conflicts: list[OrchestrationConflictV1] = Field(default_factory=list)
    llm_summary_stub: OrchestrationStubSummaryV1
    recommendation_stub: OrchestrationStubSummaryV1
    runtime_stub: bool = True
    limitations: list[str] = Field(default_factory=list)



class OrchestrationRunItemV1(BaseModel):
    orchestration_run_id: str
    trace_id: str
    case_id: str
    patient_id: str
    mode: str
    status: str
    requested_task: str
    candidate_agents: list[str] = Field(default_factory=list)
    clinical_context_refs: dict[str, Any] = Field(default_factory=dict)
    modality_refs: dict[str, Any] = Field(default_factory=dict)
    runtime_options: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)
    result_json: dict[str, Any] = Field(default_factory=dict)
    runtime_stub: bool = True
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict[str, Any] = Field(default_factory=dict)


class OrchestrationStepItemV1(BaseModel):
    step_id: str
    trace_id: str
    case_id: str
    patient_id: str
    orchestration_run_id: str
    parent_step_id: str | None = None
    step_type: str
    step_name: str | None = None
    step_index: int
    agent_code: str | None = None
    agent_version: str | None = None
    model_version_id: str | None = None
    status: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    result_json: dict[str, Any] = Field(default_factory=dict)
    runtime_stub: bool = True
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict[str, Any] = Field(default_factory=dict)


class OrchestrationAgentInvocationItemV1(BaseModel):
    agent_invocation_id: str
    trace_id: str
    case_id: str
    patient_id: str
    orchestration_run_id: str
    step_id: str
    agent_code: str
    agent_version: str | None = None
    endpoint_id: str | None = None
    endpoint_url: str | None = None
    model_version_id: str | None = None
    status: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    response_json: dict[str, Any] = Field(default_factory=dict)
    runtime_stub: bool = True
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict[str, Any] = Field(default_factory=dict)


class OrchestrationConflictItemV1(BaseModel):
    conflict_id: str
    trace_id: str
    case_id: str
    patient_id: str
    orchestration_run_id: str
    step_id: str | None = None
    conflict_type: str
    status: str
    summary_text: str | None = None
    resolution_strategy: str | None = None
    resolution_summary: str | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)
    result_json: dict[str, Any] = Field(default_factory=dict)
    runtime_stub: bool = True
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict[str, Any] = Field(default_factory=dict)


class OrchestrationLlmSummaryItemV1(BaseModel):
    summary_id: str
    trace_id: str
    case_id: str
    patient_id: str
    orchestration_run_id: str
    step_id: str | None = None
    agent_invocation_id: str | None = None
    model_version_id: str | None = None
    summary_type: str
    status: str
    summary_text: str | None = None
    summary_json: dict[str, Any] = Field(default_factory=dict)
    payload_json: dict[str, Any] = Field(default_factory=dict)
    runtime_stub: bool = True
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict[str, Any] = Field(default_factory=dict)


class OrchestrationRunDetailResponseV1(BaseModel):
    run: OrchestrationRunItemV1
    steps: list[OrchestrationStepItemV1] = Field(default_factory=list)
    agent_invocations: list[OrchestrationAgentInvocationItemV1] = Field(default_factory=list)
    conflicts: list[OrchestrationConflictItemV1] = Field(default_factory=list)
    llm_summaries: list[OrchestrationLlmSummaryItemV1] = Field(default_factory=list)
    runtime_stub: bool = True


class OrchestrationStepListResponseV1(BaseModel):
    items: list[OrchestrationStepItemV1] = Field(default_factory=list)
    total: int = 0


class OrchestrationAgentInvocationListResponseV1(BaseModel):
    items: list[OrchestrationAgentInvocationItemV1] = Field(default_factory=list)
    total: int = 0


class OrchestrationConflictListResponseV1(BaseModel):
    items: list[OrchestrationConflictItemV1] = Field(default_factory=list)
    total: int = 0


class OrchestrationLlmSummaryListResponseV1(BaseModel):
    items: list[OrchestrationLlmSummaryItemV1] = Field(default_factory=list)
    total: int = 0

