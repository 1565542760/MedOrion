import json
import logging
import uuid
from collections.abc import Callable
from typing import Any, Mapping
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.auth.security import AuthError, decode_token
from app.modules.cases.schemas import CaseResponseV1
from app.modules.clinical.schemas import (
    MissingValueQueryAnswerRequestV1,
    MissingValueQueryCreateRequestV1,
    MissingValueQueryDefaultRequestV1,
    MissingValueQueryItemV1,
    MissingValueQueryListResponseV1,
    MissingValueQueryResponseV1,
)
from app.modules.inference.persistence import resolve_case_context

logger = logging.getLogger('app.clinical')
router = APIRouter()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _actor_from_request(request: Request) -> tuple[str, str]:
    auth_header = request.headers.get('authorization', '')
    if not auth_header.lower().startswith('bearer '):
        return 'orchestrator', 'backend_stub'
    token = auth_header.split(' ', 1)[1].strip()
    try:
        payload = decode_token(token, expected_type='access')
    except AuthError:
        return 'orchestrator', 'backend_stub'
    role = payload.get('role')
    actor_id = payload.get('sub') or 'backend_stub'
    if role == 'doctor':
        return 'doctor', actor_id
    if role == 'admin':
        return 'admin', actor_id
    return 'system', actor_id


def _generate_trace_id() -> str:
    return f'trace_mv_{uuid.uuid4().hex[:12]}'


def _resolve_case_uuid_and_patient_uuid(db: Session, case_identifier: str) -> tuple[UUID, UUID]:
    case_id_text, patient_id_text = resolve_case_context(db, case_identifier)
    return UUID(case_id_text), UUID(patient_id_text)


def _question_meta(row: Mapping[str, Any]) -> dict:
    meta = row.get('doctor_response_json') if isinstance(row.get('doctor_response_json'), dict) else {}
    return meta.get('question_meta') if isinstance(meta.get('question_meta'), dict) else {}


def _query_item(row: Mapping[str, Any]) -> MissingValueQueryItemV1:
    meta = _question_meta(row)
    answer_payload = row.get('doctor_response_json') if isinstance(row.get('doctor_response_json'), dict) else {}
    return MissingValueQueryItemV1(
        query_id=str(row['query_id']),
        case_id=str(row['case_id']),
        patient_id=str(row['patient_id']) if row.get('patient_id') is not None else None,
        field_name=row['field_name'],
        field_label=row.get('field_label'),
        modality=meta.get('modality'),
        reason=meta.get('reason'),
        question_text=row['question_text'],
        status=row['status'],
        trace_id=row['trace_id'],
        policy_version=row['policy_version'],
        value_source=row['value_source'],
        doctor_answer_text=answer_payload.get('doctor_answer_text'),
        doctor_answer_json=answer_payload.get('doctor_answer_json'),
        default_strategy_code=row.get('default_strategy_code'),
        default_reason=row.get('default_reason'),
        default_value_json=row.get('default_value_json'),
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


def _write_trace_event(
    db: Session,
    *,
    trace_id: str,
    case_id: UUID,
    patient_id: UUID,
    event_type: str,
    actor_type: str,
    actor_id: str,
    source_record_type: str,
    source_record_id: str,
    payload: dict,
) -> None:
    db.execute(
        text(
            """
            insert into trace_events (
              id, trace_id, case_id, patient_id, event_type, actor_type, actor_id,
              source_module, source_record_type, source_record_id, event_time, payload_json, severity
            ) values (
              :id, :trace_id, :case_id, :patient_id, :event_type, :actor_type, :actor_id,
              :source_module, :source_record_type, :source_record_id, :event_time,
              cast(:payload_json as jsonb), :severity
            )
            """
        ),
        {
            'id': uuid.uuid4(),
            'trace_id': trace_id,
            'case_id': case_id,
            'patient_id': patient_id,
            'event_type': event_type,
            'actor_type': actor_type,
            'actor_id': actor_id,
            'source_module': 'backend',
            'source_record_type': source_record_type,
            'source_record_id': source_record_id,
            'event_time': _now(),
            'payload_json': json.dumps(payload),
            'severity': 'info',
        },
    )


def _resolve_query_or_404(db: Session, case_id_text: str, query_id_text: str) -> tuple[UUID, UUID, dict[str, Any]]:
    try:
        case_uuid, patient_uuid = _resolve_case_uuid_and_patient_uuid(db, case_id_text)
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise

    try:
        query_uuid = UUID(query_id_text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_query_id', 'message': 'query_id must be a valid UUID'}) from exc

    row = db.execute(
        text(
            """
            select
              id::text as query_id,
              case_id::text as case_id,
              patient_id::text as patient_id,
              field_path as field_name,
              field_label,
              doctor_response_json,
              question_text,
              status::text as status,
              trace_id,
              policy_version,
              value_source::text as value_source,
              default_strategy_code,
              default_value_json,
              default_reason,
              created_at,
              updated_at
            from case_missing_value_queries
            where id = :query_id and case_id = :case_id
            """
        ),
        {'query_id': query_uuid, 'case_id': case_uuid},
    ).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'query_not_found', 'message': 'Missing value query not found'})
    return case_uuid, patient_uuid, dict(row)


@router.get('/cases/{case_id}/missing-values', response_model=MissingValueQueryListResponseV1)
def list_missing_values(case_id: str) -> MissingValueQueryListResponseV1:
    db = SessionLocal()
    try:
        case_uuid, _ = _resolve_case_uuid_and_patient_uuid(db, case_id)
        rows = db.execute(
            text(
                """
                select
                  id::text as query_id,
                  case_id::text as case_id,
                  patient_id::text as patient_id,
                  field_path as field_name,
                  field_label,
                  doctor_response_json,
                  question_text,
                  status::text as status,
                  trace_id,
                  policy_version,
                  value_source::text as value_source,
                  default_strategy_code,
                  default_value_json,
                  default_reason,
                  created_at,
                  updated_at
                from case_missing_value_queries
                where case_id = :case_id
                order by created_at desc, id desc
                """
            ),
            {'case_id': case_uuid},
        ).mappings().all()
        items = [_query_item(dict(row)) for row in rows]
        return MissingValueQueryListResponseV1(items=items, total=len(items))
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise
    finally:
        db.close()


@router.post('/cases/{case_id}/missing-values', response_model=MissingValueQueryResponseV1)
def create_missing_value_query(case_id: str, payload: MissingValueQueryCreateRequestV1, request: Request) -> MissingValueQueryResponseV1:
    request_id = getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')
    actor_type, actor_id = _actor_from_request(request)
    db = SessionLocal()
    try:
        case_uuid, patient_uuid = _resolve_case_uuid_and_patient_uuid(db, case_id)
        trace_id = payload.trace_id or getattr(request.state, 'trace_id', '-')
        if not trace_id or trace_id == '-':
            trace_id = _generate_trace_id()

        query_id = uuid.uuid4()
        meta = {'modality': payload.modality, 'reason': payload.reason}
        db.execute(
            text(
                """
                insert into case_missing_value_queries (
                  id, case_id, patient_id, inference_task_id, trace_id, field_path, field_label,
                  clinical_importance, blocking_level, question_text, status, doctor_id,
                  doctor_response_json, value_source, default_strategy_code, default_value_json,
                  default_reason, policy_version, expires_at
                ) values (
                  :id, :case_id, :patient_id, :inference_task_id, :trace_id, :field_path, :field_label,
                  :clinical_importance, :blocking_level, :question_text, :status, :doctor_id,
                  cast(:doctor_response_json as jsonb), :value_source, :default_strategy_code,
                  cast(:default_value_json as jsonb), :default_reason, :policy_version, :expires_at
                )
                """
            ),
            {
                'id': query_id,
                'case_id': case_uuid,
                'patient_id': patient_uuid,
                'inference_task_id': None,
                'trace_id': trace_id,
                'field_path': payload.field_name,
                'field_label': payload.field_label,
                'clinical_importance': 'recommended',
                'blocking_level': 'informational',
                'question_text': payload.question_text,
                'status': 'pending',
                'doctor_id': actor_id if actor_type == 'doctor' else None,
                'doctor_response_json': json.dumps({'question_meta': meta}),
                'value_source': 'unknown',
                'default_strategy_code': None,
                'default_value_json': None,
                'default_reason': None,
                'policy_version': payload.policy_version or 'v1',
                'expires_at': None,
            },
        )
        _write_trace_event(
            db,
            trace_id=trace_id,
            case_id=case_uuid,
            patient_id=patient_uuid,
            event_type='missing_value_detected',
            actor_type=actor_type,
            actor_id=actor_id,
            source_record_type='case_missing_value_query',
            source_record_id=str(query_id),
            payload={
                'runtime_stub': True,
                'case_id': str(case_uuid),
                'query_id': str(query_id),
                'field_name': payload.field_name,
                'field_label': payload.field_label,
                'modality': payload.modality,
                'reason': payload.reason,
                'status': 'pending',
                'policy_version': payload.policy_version or 'v1',
            },
        )
        _write_trace_event(
            db,
            trace_id=trace_id,
            case_id=case_uuid,
            patient_id=patient_uuid,
            event_type='doctor_question_asked',
            actor_type=actor_type,
            actor_id=actor_id,
            source_record_type='case_missing_value_query',
            source_record_id=str(query_id),
            payload={
                'runtime_stub': True,
                'case_id': str(case_uuid),
                'query_id': str(query_id),
                'field_name': payload.field_name,
                'question_text': payload.question_text,
                'status': 'pending',
                'policy_version': payload.policy_version or 'v1',
            },
        )
        db.commit()
        row = db.execute(
            text(
                """
                select
                  id::text as query_id,
                  case_id::text as case_id,
                  patient_id::text as patient_id,
                  field_path as field_name,
                  field_label,
                  doctor_response_json,
                  question_text,
                  status::text as status,
                  trace_id,
                  policy_version,
                  value_source::text as value_source,
                  default_strategy_code,
                  default_value_json,
                  default_reason,
                  created_at,
                  updated_at
                from case_missing_value_queries
                where id = :query_id
                """
            ),
            {'query_id': query_id},
        ).mappings().one()
        return MissingValueQueryResponseV1(route=f'/api/v1/cases/{case_id}/missing-values', item=_query_item(dict(row)))
    except RuntimeError as exc:
        db.rollback()
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise
    except Exception as exc:
        db.rollback()
        logger.exception('create missing value query failed request_id=%s', request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'code': 'missing_value_query_failed', 'message': 'Failed to create missing value query'}) from exc
    finally:
        db.close()


@router.post('/cases/{case_id}/missing-values/{query_id}/answer', response_model=MissingValueQueryResponseV1)
def answer_missing_value_query(case_id: str, query_id: str, payload: MissingValueQueryAnswerRequestV1, request: Request) -> MissingValueQueryResponseV1:
    request_id = getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')
    actor_type, actor_id = _actor_from_request(request)
    db = SessionLocal()
    try:
        case_uuid, patient_uuid, row = _resolve_query_or_404(db, case_id, query_id)
        if row['status'] in {'answered', 'default_applied'}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'query_already_resolved', 'message': 'Missing value query already resolved'})

        meta = _question_meta(row)
        response_json = {
            'question_meta': meta,
            'doctor_answer_text': payload.doctor_answer_text,
            'doctor_answer_json': payload.doctor_answer_json,
        }
        db.execute(
            text(
                """
                update case_missing_value_queries
                set status = :status,
                    doctor_id = :doctor_id,
                    doctor_response_json = cast(:doctor_response_json as jsonb),
                    value_source = :value_source
                where id = :query_id and case_id = :case_id
                """
            ),
            {
                'status': 'answered',
                'doctor_id': actor_id if actor_type == 'doctor' else None,
                'doctor_response_json': json.dumps(response_json),
                'value_source': 'doctor_provided',
                'query_id': UUID(query_id),
                'case_id': case_uuid,
            },
        )
        _write_trace_event(
            db,
            trace_id=row['trace_id'],
            case_id=case_uuid,
            patient_id=patient_uuid,
            event_type='doctor_answer_received',
            actor_type=actor_type,
            actor_id=actor_id,
            source_record_type='case_missing_value_query',
            source_record_id=str(row['query_id']),
            payload={
                'runtime_stub': True,
                'case_id': str(case_uuid),
                'query_id': str(row['query_id']),
                'field_name': row['field_name'],
                'status': 'answered',
                'doctor_answer_text': payload.doctor_answer_text,
                'doctor_answer_json': payload.doctor_answer_json,
            },
        )
        db.commit()
        updated = db.execute(
            text(
                """
                select
                  id::text as query_id,
                  case_id::text as case_id,
                  patient_id::text as patient_id,
                  field_path as field_name,
                  field_label,
                  doctor_response_json,
                  question_text,
                  status::text as status,
                  trace_id,
                  policy_version,
                  value_source::text as value_source,
                  default_strategy_code,
                  default_value_json,
                  default_reason,
                  created_at,
                  updated_at
                from case_missing_value_queries
                where id = :query_id
                """
            ),
            {'query_id': UUID(query_id)},
        ).mappings().one()
        return MissingValueQueryResponseV1(route=f'/api/v1/cases/{case_id}/missing-values/{query_id}/answer', item=_query_item(dict(updated)))
    except HTTPException:
        db.rollback()
        raise
    except RuntimeError as exc:
        db.rollback()
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise
    except Exception as exc:
        db.rollback()
        logger.exception('answer missing value query failed request_id=%s', request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'code': 'missing_value_answer_failed', 'message': 'Failed to answer missing value query'}) from exc
    finally:
        db.close()


@router.post('/cases/{case_id}/missing-values/{query_id}/apply-default', response_model=MissingValueQueryResponseV1)
def apply_default_missing_value_query(case_id: str, query_id: str, payload: MissingValueQueryDefaultRequestV1, request: Request) -> MissingValueQueryResponseV1:
    request_id = getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')
    actor_type, actor_id = _actor_from_request(request)
    db = SessionLocal()
    try:
        case_uuid, patient_uuid, row = _resolve_query_or_404(db, case_id, query_id)
        if row['status'] in {'answered', 'default_applied'}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'query_already_resolved', 'message': 'Missing value query already resolved'})

        meta = _question_meta(row)
        question_node_id = uuid.uuid4()
        default_node_id = uuid.uuid4()
        edge_id = uuid.uuid4()
        default_value_json = payload.default_value_json or {}
        db.execute(
            text(
                """
                update case_missing_value_queries
                set status = :status,
                    doctor_id = :doctor_id,
                    value_source = :value_source,
                    default_strategy_code = :default_strategy_code,
                    default_value_json = cast(:default_value_json as jsonb),
                    default_reason = :default_reason
                where id = :query_id and case_id = :case_id
                """
            ),
            {
                'status': 'default_applied',
                'doctor_id': actor_id if actor_type == 'doctor' else None,
                'value_source': 'default_applied',
                'default_strategy_code': payload.default_strategy_code,
                'default_value_json': json.dumps(default_value_json),
                'default_reason': payload.default_reason,
                'query_id': UUID(query_id),
                'case_id': case_uuid,
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
                'id': question_node_id,
                'trace_id': row['trace_id'],
                'case_id': case_uuid,
                'patient_id': patient_uuid,
                'evidence_chain_id': row['trace_id'],
                'node_type': 'input',
                'source_module': 'backend',
                'source_record_type': 'case_missing_value_query',
                'source_record_id': str(row['query_id']),
                'label': f'missing_value_question_{row['field_name']}',
                'summary': row['question_text'],
                'payload_json': json.dumps({
                    'runtime_stub': True,
                    'value_source': 'unknown',
                    'field_name': row['field_name'],
                    'field_label': row.get('field_label'),
                    'modality': meta.get('modality'),
                    'reason': meta.get('reason'),
                    'question_text': row['question_text'],
                    'policy_version': row['policy_version'],
                }),
                'confidence': None,
                'uncertainty_json': None,
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
                'id': default_node_id,
                'trace_id': row['trace_id'],
                'case_id': case_uuid,
                'patient_id': patient_uuid,
                'evidence_chain_id': row['trace_id'],
                'node_type': 'input',
                'source_module': 'backend',
                'source_record_type': 'case_missing_value_query',
                'source_record_id': str(row['query_id']),
                'label': f'defaulted_{row['field_name']}',
                'summary': f'Default strategy applied for {row['field_name']}',
                'payload_json': json.dumps({
                    'runtime_stub': True,
                    'value_source': 'default_applied',
                    'field_name': row['field_name'],
                    'field_label': row.get('field_label'),
                    'modality': meta.get('modality'),
                    'reason': meta.get('reason'),
                    'default_strategy_code': payload.default_strategy_code,
                    'default_reason': payload.default_reason,
                    'default_value_json': default_value_json,
                    'policy_version': row['policy_version'],
                }),
                'confidence': None,
                'uncertainty_json': None,
                'status': 'defaulted',
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
                'trace_id': row['trace_id'],
                'case_id': case_uuid,
                'evidence_chain_id': row['trace_id'],
                'source_node_id': question_node_id,
                'target_node_id': default_node_id,
                'edge_type': 'missing_value_defaulted',
                'weight': 1.0,
                'rationale': 'default applied after doctor did not answer',
                'payload_json': json.dumps({
                    'runtime_stub': True,
                    'value_source': 'default_applied',
                    'field_name': row['field_name'],
                    'default_strategy_code': payload.default_strategy_code,
                }),
            },
        )
        _write_trace_event(
            db,
            trace_id=row['trace_id'],
            case_id=case_uuid,
            patient_id=patient_uuid,
            event_type='default_strategy_applied',
            actor_type=actor_type,
            actor_id=actor_id,
            source_record_type='case_missing_value_query',
            source_record_id=str(row['query_id']),
            payload={
                'runtime_stub': True,
                'case_id': str(case_uuid),
                'query_id': str(row['query_id']),
                'field_name': row['field_name'],
                'status': 'default_applied',
                'value_source': 'default_applied',
                'default_strategy_code': payload.default_strategy_code,
                'default_reason': payload.default_reason,
                'default_value_json': default_value_json,
            },
        )
        db.commit()
        updated = db.execute(
            text(
                """
                select
                  id::text as query_id,
                  case_id::text as case_id,
                  patient_id::text as patient_id,
                  field_path as field_name,
                  field_label,
                  doctor_response_json,
                  question_text,
                  status::text as status,
                  trace_id,
                  policy_version,
                  value_source::text as value_source,
                  default_strategy_code,
                  default_value_json,
                  default_reason,
                  created_at,
                  updated_at
                from case_missing_value_queries
                where id = :query_id
                """
            ),
            {'query_id': UUID(query_id)},
        ).mappings().one()
        return MissingValueQueryResponseV1(route=f'/api/v1/cases/{case_id}/missing-values/{query_id}/apply-default', item=_query_item(dict(updated)))
    except HTTPException:
        db.rollback()
        raise
    except RuntimeError as exc:
        db.rollback()
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise
    except Exception as exc:
        db.rollback()
        logger.exception('apply default missing value query failed request_id=%s', request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'code': 'missing_value_default_failed', 'message': 'Failed to apply default missing value strategy'}) from exc
    finally:
        db.close()
