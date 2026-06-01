from fastapi import APIRouter

from app.modules.traces.schemas import (
    EvidenceChainResponseV1,
    TraceEventListResponseV1,
    TraceEventResponseV1,
    TraceResponseV1,
)

router = APIRouter()


@router.get('/traces/{trace_id}', response_model=TraceResponseV1)
def get_trace(trace_id: str) -> TraceResponseV1:
    return TraceResponseV1(route=f'/api/v1/traces/{trace_id}', trace_id=trace_id)


@router.get('/traces/{trace_id}/events', response_model=TraceEventListResponseV1)
def list_trace_events(trace_id: str) -> TraceEventListResponseV1:
    return TraceEventListResponseV1(items=[TraceEventResponseV1(route=f'/api/v1/traces/{trace_id}/events', trace_id=trace_id)])


@router.get('/traces/{trace_id}/evidence-chain', response_model=EvidenceChainResponseV1)
def get_evidence_chain(trace_id: str) -> EvidenceChainResponseV1:
    return EvidenceChainResponseV1(route=f'/api/v1/traces/{trace_id}/evidence-chain', trace_id=trace_id)
