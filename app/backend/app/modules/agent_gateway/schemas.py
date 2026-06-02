
from pydantic import BaseModel, Field


class AgentRegistryItemV1(BaseModel):
    agent_code: str
    agent_name: str
    contract_version: str
    supported_diseases: list[str] = Field(default_factory=list)
    supported_tasks: list[str] = Field(default_factory=list)
    supported_modalities: list[str] = Field(default_factory=list)
    status: str = 'stub_active'
    endpoint_url: str
    health_url: str
    default_model_version_id: str


class AgentRegistryListResponseV1(BaseModel):
    items: list[AgentRegistryItemV1] = Field(default_factory=list)
    total: int = 0


class AgentRegistryResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: AgentRegistryItemV1


class AgentGatewayValidateInputRequestV1(BaseModel):
    agent_code: str
    requested_task: str
    modalities: list[str] = Field(default_factory=list)
    model_version_policy: dict = Field(default_factory=dict)
    inputs: dict = Field(default_factory=dict)


class AgentGatewayValidateInputResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    agent_code: str
    valid: bool = True
    agent_status: str = 'stub_active'
    matched_model_version_id: str | None = None
    unsupported_reason: str | None = None
    runtime_stub: bool = True


class AgentGatewayInferRequestV1(BaseModel):
    trace_id: str
    case_id: str
    patient_id: str
    agent_code: str
    requested_task: str
    modalities: list[str] = Field(default_factory=list)
    model_version_policy: dict = Field(default_factory=dict)
    inputs: dict = Field(default_factory=dict)
    idempotency_key: str | None = None


class AgentGatewayInferResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    trace_id: str
    agent_invocation_id: str
    agent_code: str
    agent_status: str
    model_service_response: dict = Field(default_factory=dict)
    runtime_stub: bool = True
