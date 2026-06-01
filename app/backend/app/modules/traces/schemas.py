from pydantic import BaseModel, Field


class TraceResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    trace_id: str


class TraceEventResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    trace_id: str


class TraceEventListResponseV1(BaseModel):
    items: list[TraceEventResponseV1] = Field(default_factory=list)
    total: int = 0


class EvidenceChainResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    trace_id: str
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
