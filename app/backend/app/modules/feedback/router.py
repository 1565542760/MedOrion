from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.enums import FeedbackType, TraceActorType, TraceSeverity
from app.db.models import User
from app.db.session import SessionLocal
from app.modules.auth.security import AuthError, auth_http_exception, decode_token
from app.modules.feedback.schemas import (
    DoctorFeedbackCreateRequestV1,
    DoctorFeedbackItemV1,
    DoctorFeedbackListResponseV1,
    DoctorFeedbackResponseV1,
)
from app.modules.inference.persistence import resolve_case_context

router = APIRouter()
logger = logging.getLogger('app.feedback')
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _optional_actor(credentials: HTTPAuthorizationCredentials | None, db: Session) -> tuple[str, str | None, str | None]:
    if credentials is None or not credentials.credentials:
        return TraceActorType.DOCTOR.value, 'stub_doctor', 'stub'

    try:
        payload = decode_token(credentials.credentials, expected_type='access')
    except AuthError as exc:
        raise auth_http_exception(exc) from exc

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'invalid_token', 'message': 'Token missing subject'})

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'user_inactive', 'message': 'User not active'})

    return TraceActorType.DOCTOR.value, str(user.id), user.role


def _case_context_or_404(db: Session, case_identifier: str) -> tuple[str, str]:
    try:
        return resolve_case_context(db, case_identifier)
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise


def _recommendation_context_or_404(db: Session, case_id: str, recommendation_id: str) -> dict:
    try:
        recommendation_uuid = UUID(recommendation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_recommendation_id', 'message': 'recommendation_id must be a valid UUID'}) from exc

    row = db.execute(
        text(
            '''
            select
              id::text as recommendation_id,
              case_id::text as case_id,
              inference_task_id::text as inference_task_id,
              trace_id,
              evidence_chain_id,
              recommendation_version,
              recommendation_type,
              status::text as status,
              candidate_label,
              confidence_score,
              uncertainty_json,
              limitations_json,
              evidence_refs_json,
              content_json,
              created_by_type
            from recommendations
            where id = :recommendation_id and case_id = :case_id
            limit 1
            '''
        ),
        {'recommendation_id': recommendation_uuid, 'case_id': UUID(case_id)},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'recommendation_not_found', 'message': 'Recommendation not found'})
    return dict(row)


def _trace_exists(db: Session, trace_id: str) -> bool:
    trace_row = db.execute(
        text(
            '''
            select 1
            from trace_events
            where trace_id = :trace_id
            limit 1
            '''
        ),
        {'trace_id': trace_id},
    ).first()
    if trace_row is not None:
        return True

    rec_row = db.execute(
        text(
            '''
            select 1
            from recommendations
            where trace_id = :trace_id
            limit 1
            '''
        ),
        {'trace_id': trace_id},
    ).first()
    return rec_row is not None


def _feedback_item_from_row(row: dict) -> DoctorFeedbackItemV1:
    return DoctorFeedbackItemV1(
        feedback_id=row['feedback_id'],
        case_id=row['case_id'],
        trace_id=row['trace_id'],
        recommendation_id=row.get('recommendation_id'),
        feedback_type=row['feedback_type'],
        feedback_text=row.get('feedback_text'),
        doctor_decision=row.get('doctor_decision'),
        rating=row.get('rating'),
        doctor_id=row.get('doctor_id'),
        learning_eligible=row.get('learning_eligible', True),
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


def _write_trace_event(
    db: Session,
    *,
    trace_id: str,
    case_id: str,
    patient_id: str | None,
    actor_type: str,
    actor_id: str | None,
    event_type: str,
    source_record_type: str,
    source_record_id: str,
    payload: dict,
) -> None:
    db.execute(
        text(
            '''
            insert into trace_events (
              id, trace_id, case_id, patient_id, event_type, actor_type, actor_id,
              source_module, source_record_type, source_record_id, event_time,
              payload_json, severity
            ) values (
              :id, :trace_id, :case_id, :patient_id, :event_type, :actor_type, :actor_id,
              :source_module, :source_record_type, :source_record_id, :event_time,
              cast(:payload_json as jsonb), :severity
            )
            '''
        ),
        {
            'id': uuid4(),
            'trace_id': trace_id,
            'case_id': UUID(case_id),
            'patient_id': UUID(patient_id) if patient_id else None,
            'event_type': event_type,
            'actor_type': actor_type,
            'actor_id': actor_id,
            'source_module': 'feedback',
            'source_record_type': source_record_type,
            'source_record_id': source_record_id,
            'event_time': datetime.now(UTC),
            'payload_json': json.dumps(payload),
            'severity': TraceSeverity.INFO.value,
        },
    )


def _list_feedback_rows(db: Session, case_id: str | None = None, trace_id: str | None = None) -> list[dict]:
    conditions: list[str] = []
    params: dict[str, object] = {}
    if case_id:
        case_uuid, _ = _case_context_or_404(db, case_id)
        conditions.append('case_id = :case_id')
        params['case_id'] = UUID(case_uuid)
    if trace_id:
        if not _trace_exists(db, trace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'trace_not_found', 'message': 'Trace not found'})
        conditions.append('trace_id = :trace_id')
        params['trace_id'] = trace_id

    where_clause = f"where {' and '.join(conditions)}" if conditions else ''
    rows = db.execute(
        text(
            f'''
            select
              id::text as feedback_id,
              case_id::text as case_id,
              trace_id,
              recommendation_id::text as recommendation_id,
              feedback_type::text as feedback_type,
              clinical_rationale as feedback_text,
              decision as doctor_decision,
              rating,
              doctor_id,
              learning_eligible,
              created_at,
              updated_at
            from doctor_feedback
            {where_clause}
            order by created_at desc, id desc
            '''
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


@router.get('', response_model=DoctorFeedbackListResponseV1)
@router.get('/', response_model=DoctorFeedbackListResponseV1, include_in_schema=False)
def list_feedback(
    case_id: str | None = None,
    trace_id: str | None = None,
    db: Session = Depends(get_db),
) -> DoctorFeedbackListResponseV1:
    rows = _list_feedback_rows(db, case_id=case_id, trace_id=trace_id)
    items = [_feedback_item_from_row(row) for row in rows]
    return DoctorFeedbackListResponseV1(items=items, total=len(items))


@router.post('', response_model=DoctorFeedbackResponseV1)
@router.post('/', response_model=DoctorFeedbackResponseV1, include_in_schema=False)
def create_feedback(
    payload: DoctorFeedbackCreateRequestV1,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> DoctorFeedbackResponseV1:
    case_id, patient_id = _case_context_or_404(db, payload.case_id)
    recommendation = _recommendation_context_or_404(db, case_id, payload.recommendation_id)

    trace_id = payload.trace_id or recommendation['trace_id']
    if payload.trace_id and payload.trace_id != recommendation['trace_id']:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'trace_mismatch', 'message': 'trace_id does not match recommendation trace'})
    if not _trace_exists(db, trace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'trace_not_found', 'message': 'Trace not found'})

    try:
        feedback_type = FeedbackType(payload.feedback_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_feedback_type', 'message': 'Unsupported feedback_type'}) from exc

    actor_type, actor_id, actor_role = _optional_actor(credentials, db)
    feedback_id = uuid4()
    now = datetime.now(UTC)
    correction_payload = {
        'runtime_stub': True,
        'actor_type': actor_type,
        'actor_id': actor_id,
        'actor_role': actor_role,
        'source': 'doctor_feedback_api',
        'feedback_type': feedback_type.value,
        'doctor_decision': payload.doctor_decision,
        'learning_eligible': payload.learning_eligible,
        'trace_id': trace_id,
        'recommendation_id': recommendation['recommendation_id'],
    }

    try:
        db.execute(
            text(
                '''
                insert into doctor_feedback (
                  id, case_id, recommendation_id, inference_task_id, trace_id, doctor_id,
                  feedback_type, decision, rating, clinical_rationale, correction_payload_json,
                  learning_eligible, created_at, updated_at
                ) values (
                  :id, :case_id, :recommendation_id, :inference_task_id, :trace_id, :doctor_id,
                  :feedback_type, :decision, :rating, :clinical_rationale, cast(:correction_payload_json as jsonb),
                  :learning_eligible, :created_at, :updated_at
                )
                '''
            ),
            {
                'id': feedback_id,
                'case_id': UUID(case_id),
                'recommendation_id': UUID(recommendation['recommendation_id']),
                'inference_task_id': UUID(recommendation['inference_task_id']) if recommendation.get('inference_task_id') else None,
                'trace_id': trace_id,
                'doctor_id': actor_id,
                'feedback_type': feedback_type.value,
                'decision': payload.doctor_decision,
                'rating': payload.rating,
                'clinical_rationale': payload.feedback_text,
                'correction_payload_json': json.dumps(correction_payload),
                'learning_eligible': payload.learning_eligible,
                'created_at': now,
                'updated_at': now,
            },
        )

        _write_trace_event(
            db,
            trace_id=trace_id,
            case_id=case_id,
            patient_id=patient_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type='doctor_feedback_recorded',
            source_record_type='doctor_feedback',
            source_record_id=str(feedback_id),
            payload={
                'case_id': case_id,
                'trace_id': trace_id,
                'feedback_id': str(feedback_id),
                'recommendation_id': recommendation['recommendation_id'],
                'feedback_type': feedback_type.value,
                'doctor_decision': payload.doctor_decision,
                'rating': payload.rating,
                'learning_eligible': payload.learning_eligible,
                'actor_type': actor_type,
                'actor_id': actor_id,
                'actor_role': actor_role,
                'runtime_stub': True,
            },
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception('doctor feedback persistence failed')
        raise HTTPException(status_code=503, detail={'code': 'feedback_storage_unavailable', 'message': 'Feedback storage is unavailable.'}) from exc

    row = {
        'feedback_id': str(feedback_id),
        'case_id': case_id,
        'trace_id': trace_id,
        'recommendation_id': recommendation['recommendation_id'],
        'feedback_type': feedback_type.value,
        'feedback_text': payload.feedback_text,
        'doctor_decision': payload.doctor_decision,
        'rating': payload.rating,
        'doctor_id': actor_id,
        'learning_eligible': payload.learning_eligible,
        'created_at': now,
        'updated_at': now,
    }
    return DoctorFeedbackResponseV1(route='/api/v1/feedback', item=_feedback_item_from_row(row))
