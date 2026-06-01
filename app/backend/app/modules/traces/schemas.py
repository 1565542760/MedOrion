from pydantic import BaseModel, Field


class TraceResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    trace_id: str
    case_id: str | None = None
    patient_id: str | None = None
    event_count: int = 0
    evidence_node_count: int = 0
    evidence_edge_count: int = 0


class TraceEventResponseV1(BaseModel):
    event_id: str
    trace_id: str
    event_type: str
    event_time: str
    actor_type: str
    source_module: str
    payload: dict = Field(default_factory=dict)


class TraceEventListResponseV1(BaseModel):
    items: list[TraceEventResponseV1] = Field(default_factory=list)
    total: int = 0


class EvidenceChainResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    trace_id: str
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
