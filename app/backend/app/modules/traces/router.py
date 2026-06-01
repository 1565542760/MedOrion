from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal
from app.modules.traces.schemas import (
    EvidenceChainResponseV1,
    TraceEventListResponseV1,
    TraceEventResponseV1,
    TraceResponseV1,
)

router = APIRouter()


@router.get('/traces/{trace_id}', response_model=TraceResponseV1)
def get_trace(trace_id: str) -> TraceResponseV1:
    db = SessionLocal()
    try:
        first_event = db.execute(
            text("select case_id::text as case_id, patient_id::text as patient_id from trace_events where trace_id = :trace_id order by event_time asc limit 1"),
            {'trace_id': trace_id},
        ).first()
        event_count = db.execute(text("select count(*) from trace_events where trace_id = :trace_id"), {'trace_id': trace_id}).scalar_one()
        node_count = db.execute(text("select count(*) from evidence_nodes where trace_id = :trace_id"), {'trace_id': trace_id}).scalar_one()
        edge_count = db.execute(text("select count(*) from evidence_edges where trace_id = :trace_id"), {'trace_id': trace_id}).scalar_one()

        return TraceResponseV1(
            route=f'/api/v1/traces/{trace_id}',
            trace_id=trace_id,
            case_id=first_event.case_id if first_event else None,
            patient_id=first_event.patient_id if first_event else None,
            event_count=int(event_count),
            evidence_node_count=int(node_count),
            evidence_edge_count=int(edge_count),
        )
    finally:
        db.close()


@router.get('/traces/{trace_id}/events', response_model=TraceEventListResponseV1)
def list_trace_events(trace_id: str) -> TraceEventListResponseV1:
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                select id::text as event_id, trace_id, event_type, event_time::text as event_time,
                       actor_type::text as actor_type, source_module, payload_json
                from trace_events
                where trace_id = :trace_id
                order by event_time asc
                """
            ),
            {'trace_id': trace_id},
        ).mappings().all()

        items = [
            TraceEventResponseV1(
                event_id=r['event_id'],
                trace_id=r['trace_id'],
                event_type=r['event_type'],
                event_time=r['event_time'],
                actor_type=r['actor_type'],
                source_module=r['source_module'],
                payload=r['payload_json'] or {},
            )
            for r in rows
        ]
        return TraceEventListResponseV1(items=items, total=len(items))
    finally:
        db.close()


@router.get('/traces/{trace_id}/evidence-chain', response_model=EvidenceChainResponseV1)
def get_evidence_chain(trace_id: str) -> EvidenceChainResponseV1:
    db = SessionLocal()
    try:
        node_rows = db.execute(
            text(
                """
                select id::text as node_id, node_type::text as node_type, label, summary, source_module,
                       source_record_type, source_record_id, confidence
                from evidence_nodes
                where trace_id = :trace_id
                order by created_at asc
                """
            ),
            {'trace_id': trace_id},
        ).mappings().all()

        edge_rows = db.execute(
            text(
                """
                select id::text as edge_id, edge_type::text as edge_type,
                       source_node_id::text as source_node_id,
                       target_node_id::text as target_node_id,
                       rationale, weight
                from evidence_edges
                where trace_id = :trace_id
                order by created_at asc
                """
            ),
            {'trace_id': trace_id},
        ).mappings().all()

        return EvidenceChainResponseV1(
            route=f'/api/v1/traces/{trace_id}/evidence-chain',
            trace_id=trace_id,
            nodes=[dict(r) for r in node_rows],
            edges=[dict(r) for r in edge_rows],
        )
    finally:
        db.close()
