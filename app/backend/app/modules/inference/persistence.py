import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def now_utc() -> datetime:
    return datetime.now(UTC)


def ensure_stub_case(db: Session, case_no: str, patient_token: str | None) -> tuple[str, str]:
    row = db.execute(
        text("select id::text as id, patient_id::text as patient_id from cases where case_no = :case_no limit 1"),
        {'case_no': case_no},
    ).first()
    if row:
        return row.id, row.patient_id

    row = db.execute(text("select id::text as id, patient_id::text as patient_id from cases limit 1")).first()
    if row:
        return row.id, row.patient_id

    patient_id = str(uuid.uuid4())
    case_id = str(uuid.uuid4())

    db.execute(
        text(
            """
            insert into patients (id, external_patient_id, patient_display_id, demographics_json, consent_status)
            values (:id, :external_patient_id, :patient_display_id, cast(:demographics_json as jsonb), :consent_status)
            """
        ),
        {
            'id': patient_id,
            'external_patient_id': patient_token or 'patient-001',
            'patient_display_id': patient_token or 'patient-001',
            'demographics_json': '{}',
            'consent_status': 'unknown',
        },
    )

    db.execute(
        text(
            """
            insert into cases (id, patient_id, case_no, disease_domain_code, title, status, context_json, opened_at)
            values (:id, :patient_id, :case_no, :disease_domain_code, :title, :status, cast(:context_json as jsonb), now())
            """
        ),
        {
            'id': case_id,
            'patient_id': patient_id,
            'case_no': case_no,
            'disease_domain_code': 'CAPCOP',
            'title': 'stub case anchor',
            'status': 'open',
            'context_json': '{}',
        },
    )

    db.commit()
    return case_id, patient_id


def write_success_bundle(
    db: Session,
    *,
    trace_id: str,
    case_id: str,
    patient_id: str,
    disease_agent: str,
    requested_task: str,
    model_version_policy: dict[str, Any],
    inputs: dict[str, Any],
    missing_value_context: dict[str, Any],
    idempotency_key: str,
    model_response: dict[str, Any],
) -> dict[str, str]:
    ts = now_utc().isoformat()
    inference_task_id = str(uuid.uuid4())
    recommendation_id = str(uuid.uuid4())
    model_node_id = str(uuid.uuid4())
    recommendation_node_id = str(uuid.uuid4())
    edge_id = str(uuid.uuid4())
    evidence_chain_id = trace_id

    db.execute(
        text(
            """
            insert into inference_tasks (
              id, trace_id, case_id, patient_id, disease_agent, task_type, status,
              requested_modalities_json, model_version_policy_json, input_refs_json, missing_value_summary_json,
              idempotency_key, started_at, completed_at
            ) values (
              :id, :trace_id, :case_id, :patient_id, :disease_agent, :task_type, :status,
              cast(:requested_modalities_json as jsonb), cast(:model_version_policy_json as jsonb),
              cast(:input_refs_json as jsonb), cast(:missing_value_summary_json as jsonb),
              :idempotency_key, :started_at, :completed_at
            )
            """
        ),
        {
            'id': inference_task_id,
            'trace_id': trace_id,
            'case_id': case_id,
            'patient_id': patient_id,
            'disease_agent': disease_agent,
            'task_type': requested_task,
            'status': 'succeeded',
            'requested_modalities_json': '[]',
            'model_version_policy_json': json.dumps(model_version_policy),
            'input_refs_json': json.dumps([inputs]),
            'missing_value_summary_json': json.dumps(missing_value_context),
            'idempotency_key': idempotency_key,
            'started_at': ts,
            'completed_at': ts,
        },
    )

    db.execute(
        text(
            """
            insert into recommendations (
              id, case_id, inference_task_id, trace_id, evidence_chain_id, recommendation_version,
              recommendation_type, status, candidate_label, confidence_score, uncertainty_json,
              limitations_json, evidence_refs_json, content_json, created_by_type
            ) values (
              :id, :case_id, :inference_task_id, :trace_id, :evidence_chain_id, 1,
              :recommendation_type, :status, :candidate_label, :confidence_score,
              cast(:uncertainty_json as jsonb), cast(:limitations_json as jsonb),
              cast(:evidence_refs_json as jsonb), cast(:content_json as jsonb), :created_by_type
            )
            """
        ),
        {
            'id': recommendation_id,
            'case_id': case_id,
            'inference_task_id': inference_task_id,
            'trace_id': trace_id,
            'evidence_chain_id': evidence_chain_id,
            'recommendation_type': 'stub_inference_result',
            'status': 'active',
            'candidate_label': (model_response.get('outputs') or {}).get('candidate_label'),
            'confidence_score': (model_response.get('confidence') or {}).get('score'),
            'uncertainty_json': json.dumps(model_response.get('uncertainty') or {}),
            'limitations_json': json.dumps(model_response.get('limitations') or []),
            'evidence_refs_json': json.dumps([{'node_id': model_node_id, 'node_type': 'model_output'}]),
            'content_json': json.dumps({'model_service': model_response}),
            'created_by_type': 'system',
        },
    )

    db.execute(
        text(
            """
            insert into evidence_nodes (
              id, trace_id, case_id, patient_id, evidence_chain_id, node_type, source_module,
              source_record_type, source_record_id, label, summary, payload_json, confidence,
              uncertainty_json, status
            ) values (
              :id, :trace_id, :case_id, :patient_id, :evidence_chain_id, :node_type, :source_module,
              :source_record_type, :source_record_id, :label, :summary, cast(:payload_json as jsonb), :confidence,
              cast(:uncertainty_json as jsonb), :status
            )
            """
        ),
        {
            'id': model_node_id,
            'trace_id': trace_id,
            'case_id': case_id,
            'patient_id': patient_id,
            'evidence_chain_id': evidence_chain_id,
            'node_type': 'model_output',
            'source_module': 'model_service',
            'source_record_type': 'model_invocation',
            'source_record_id': model_response.get('model_invocation_id'),
            'label': 'stub_model_output',
            'summary': 'model-service stub output',
            'payload_json': json.dumps(model_response),
            'confidence': (model_response.get('confidence') or {}).get('score'),
            'uncertainty_json': json.dumps(model_response.get('uncertainty') or {}),
            'status': 'active',
        },
    )

    db.execute(
        text(
            """
            insert into evidence_nodes (
              id, trace_id, case_id, patient_id, evidence_chain_id, node_type, source_module,
              source_record_type, source_record_id, label, summary, payload_json, confidence,
              uncertainty_json, status
            ) values (
              :id, :trace_id, :case_id, :patient_id, :evidence_chain_id, :node_type, :source_module,
              :source_record_type, :source_record_id, :label, :summary, cast(:payload_json as jsonb), :confidence,
              cast(:uncertainty_json as jsonb), :status
            )
            """
        ),
        {
            'id': recommendation_node_id,
            'trace_id': trace_id,
            'case_id': case_id,
            'patient_id': patient_id,
            'evidence_chain_id': evidence_chain_id,
            'node_type': 'recommendation',
            'source_module': 'backend',
            'source_record_type': 'recommendation',
            'source_record_id': recommendation_id,
            'label': 'stub_recommendation',
            'summary': 'backend generated stub recommendation',
            'payload_json': json.dumps({'recommendation_id': recommendation_id, 'inference_task_id': inference_task_id}),
            'confidence': (model_response.get('confidence') or {}).get('score'),
            'uncertainty_json': json.dumps(model_response.get('uncertainty') or {}),
            'status': 'active',
        },
    )

    db.execute(
        text(
            """
            insert into evidence_edges (
              id, trace_id, case_id, evidence_chain_id, source_node_id, target_node_id,
              edge_type, weight, rationale, payload_json
            ) values (
              :id, :trace_id, :case_id, :evidence_chain_id, :source_node_id, :target_node_id,
              :edge_type, :weight, :rationale, cast(:payload_json as jsonb)
            )
            """
        ),
        {
            'id': edge_id,
            'trace_id': trace_id,
            'case_id': case_id,
            'evidence_chain_id': evidence_chain_id,
            'source_node_id': model_node_id,
            'target_node_id': recommendation_node_id,
            'edge_type': 'supports',
            'weight': 1.0,
            'rationale': 'stub model output supports recommendation',
            'payload_json': '{}',
        },
    )

    for event_type, payload in [
        ('inference_task_created', {'inference_task_id': inference_task_id}),
        ('model_invoked', {'inference_task_id': inference_task_id}),
        ('model_result_received', {'inference_task_id': inference_task_id, 'model_invocation_id': model_response.get('model_invocation_id')}),
        ('recommendation_generated', {'inference_task_id': inference_task_id, 'recommendation_id': recommendation_id}),
    ]:
        db.execute(
            text(
                """
                insert into trace_events (
                  id, trace_id, case_id, patient_id, event_type, actor_type, actor_id,
                  source_module, source_record_type, source_record_id, event_time, payload_json, severity
                ) values (
                  :id, :trace_id, :case_id, :patient_id, :event_type, :actor_type, :actor_id,
                  :source_module, :source_record_type, :source_record_id, :event_time, cast(:payload_json as jsonb), :severity
                )
                """
            ),
            {
                'id': str(uuid.uuid4()),
                'trace_id': trace_id,
                'case_id': case_id,
                'patient_id': patient_id,
                'event_type': event_type,
                'actor_type': 'orchestrator',
                'actor_id': 'backend_stub',
                'source_module': 'backend',
                'source_record_type': 'inference',
                'source_record_id': inference_task_id,
                'event_time': ts,
                'payload_json': json.dumps(payload),
                'severity': 'info',
            },
        )

    db.commit()

    return {
        'inference_task_id': inference_task_id,
        'recommendation_id': recommendation_id,
        'model_node_id': model_node_id,
        'recommendation_node_id': recommendation_node_id,
        'edge_id': edge_id,
    }


def write_failure_event(db: Session, *, trace_id: str, case_id: str, patient_id: str, error_payload: dict[str, Any]) -> None:
    db.execute(
        text(
            """
            insert into trace_events (
              id, trace_id, case_id, patient_id, event_type, actor_type, actor_id,
              source_module, source_record_type, source_record_id, event_time, payload_json, severity
            ) values (
              :id, :trace_id, :case_id, :patient_id, :event_type, :actor_type, :actor_id,
              :source_module, :source_record_type, :source_record_id, :event_time, cast(:payload_json as jsonb), :severity
            )
            """
        ),
        {
            'id': str(uuid.uuid4()),
            'trace_id': trace_id,
            'case_id': case_id,
            'patient_id': patient_id,
            'event_type': 'model_result_received',
            'actor_type': 'orchestrator',
            'actor_id': 'backend_stub',
            'source_module': 'backend',
            'source_record_type': 'inference',
            'source_record_id': None,
            'event_time': now_utc().isoformat(),
            'payload_json': json.dumps({'status': 'failed', 'error': error_payload}),
            'severity': 'error',
        },
    )
    db.commit()
