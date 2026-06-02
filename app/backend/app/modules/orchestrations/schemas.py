
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
    agent_code: str | None = None
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
    status: str = 'pending'
    duration_ms: int | None = None
    model_service_response: dict[str, Any] = Field(default_factory=dict)


class OrchestrationConflictV1(BaseModel):
    conflict_id: str
    agents: list[str] = Field(default_factory=list)
    reason: str
    resolution: str | None = None
    status: str = 'stub'


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
