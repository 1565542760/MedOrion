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

from app.db.enums import (
    QualityErrorAttribution,
    QualityReviewStatus,
    QualitySeverity,
    QualityTargetType,
    TraceActorType,
    TraceSeverity,
)
from app.db.models import User
from app.db.session import SessionLocal
from app.modules.auth.security import AuthError, auth_http_exception, decode_token
from app.modules.inference.persistence import resolve_case_context
from app.modules.quality.schemas import (
    QualityReviewCreateRequestV1,
    QualityReviewItemV1,
    QualityReviewListResponseV1,
    QualityReviewResponseV1,
)

router = APIRouter()
logger = logging.getLogger('app.quality')
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _actor_from_token(credentials: HTTPAuthorizationCredentials | None, db: Session) -> tuple[str, str | None, str | None]:
    if credentials is None or not credentials.credentials:
        return TraceActorType.QC_AGENT.value, 'stub_qc', 'stub'

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

    role = str(user.role)
    if role == 'doctor':
        return TraceActorType.DOCTOR.value, str(user.id), role
    if role in {'admin', 'super_admin'}:
        return TraceActorType.ADMIN.value, str(user.id), role
    if role in {'model_reviewer', 'qa_reviewer'}:
        return TraceActorType.QC_AGENT.value, str(user.id), role
    return TraceActorType.SYSTEM.value, str(user.id), role


def _case_context_or_404(db: Session, case_identifier: str) -> tuple[str, str]:
    try:
        return resolve_case_context(db, case_identifier)
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise


def _trace_exists(db: Session, trace_id: str) -> bool:
    trace_row = db.execute(
        text('''
            select 1 from trace_events where trace_id = :trace_id limit 1
        '''),
        {'trace_id': trace_id},
    ).first()
    if trace_row is not None:
        return True

    review_row = db.execute(
        text('''
            select 1 from quality_reviews where trace_id = :trace_id limit 1
        '''),
        {'trace_id': trace_id},
    ).first()
    return review_row is not None


def _feedback_or_404(db: Session, case_id: str, related_feedback_id: str) -> dict:
    try:
        feedback_uuid = UUID(related_feedback_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_related_feedback_id', 'message': 'related_feedback_id must be a valid UUID'}) from exc

    row = db.execute(
        text('''
            select
              id::text as feedback_id,
              case_id::text as case_id,
              trace_id,
              recommendation_id::text as recommendation_id,
              feedback_type::text as feedback_type,
              decision,
              rating,
              doctor_id
            from doctor_feedback
            where id = :feedback_id and case_id = :case_id
            limit 1
        '''),
        {'feedback_id': feedback_uuid, 'case_id': UUID(case_id)},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'feedback_not_found', 'message': 'Feedback not found'})
    return dict(row)


def _quality_review_item(row: dict) -> QualityReviewItemV1:
    return QualityReviewItemV1(
        review_id=row['review_id'],
        case_id=row['case_id'],
        trace_id=row['trace_id'],
        target_type=row['target_type'],
        target_id=row['target_id'],
        status=row['status'],
        attribution=row.get('attribution'),
        severity=row['severity'],
        summary=row['summary'],
        related_feedback_id=row.get('related_feedback_id'),
        actor_type=row['actor_type'],
        actor_id=row.get('actor_id'),
        attribution_confidence=row.get('attribution_confidence'),
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
        text('''
            insert into trace_events (
              id, trace_id, case_id, patient_id, event_type, actor_type, actor_id,
              source_module, source_record_type, source_record_id, event_time,
              payload_json, severity
            ) values (
              :id, :trace_id, :case_id, :patient_id, :event_type, :actor_type, :actor_id,
              :source_module, :source_record_type, :source_record_id, :event_time,
              cast(:payload_json as jsonb), :severity
            )
        '''),
        {
            'id': uuid4(),
            'trace_id': trace_id,
            'case_id': UUID(case_id),
            'patient_id': UUID(patient_id) if patient_id else None,
            'event_type': event_type,
            'actor_type': actor_type,
            'actor_id': actor_id,
            'source_module': 'quality',
            'source_record_type': source_record_type,
            'source_record_id': source_record_id,
            'event_time': datetime.now(UTC),
            'payload_json': json.dumps(payload),
            'severity': TraceSeverity.INFO.value,
        },
    )


def _list_reviews(db: Session, *, case_id: str | None = None, trace_id: str | None = None, review_status: str | None = None) -> list[dict]:
    if trace_id and not _trace_exists(db, trace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'trace_not_found', 'message': 'Trace not found'})

    conditions: list[str] = []
    params: dict[str, object] = {}
    if case_id:
        case_uuid, _ = _case_context_or_404(db, case_id)
        conditions.append('case_id = :case_id')
        params['case_id'] = UUID(case_uuid)
    if trace_id:
        conditions.append('trace_id = :trace_id')
        params['trace_id'] = trace_id
    if review_status:
        conditions.append('status = :status')
        params['status'] = review_status

    where_clause = f"where {' and '.join(conditions)}" if conditions else ''
    rows = db.execute(
        text(f'''
            select
              id::text as review_id,
              case_id::text as case_id,
              trace_id,
              review_target_type::text as target_type,
              review_target_id::text as target_id,
              status::text as status,
              error_attribution::text as attribution,
              severity::text as severity,
              reason as summary,
              related_refs_json->>'related_feedback_id' as related_feedback_id,
              opened_by_type::text as actor_type,
              opened_by_id as actor_id,
              attribution_confidence,
              created_at,
              updated_at
            from quality_reviews
            {where_clause}
            order by created_at desc, id desc
        '''),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


@router.get('/quality-reviews', response_model=QualityReviewListResponseV1)
@router.get('/quality-reviews/', response_model=QualityReviewListResponseV1, include_in_schema=False)
def list_quality_reviews(case_id: str | None = None, trace_id: str | None = None, review_status: str | None = None, db: Session = Depends(get_db)) -> QualityReviewListResponseV1:
    if review_status is not None:
        try:
            QualityReviewStatus(review_status)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_status', 'message': 'Unsupported status'}) from exc
    rows = _list_reviews(db, case_id=case_id, trace_id=trace_id, review_status=review_status)
    items = [_quality_review_item(row) for row in rows]
    return QualityReviewListResponseV1(items=items, total=len(items))


@router.get('/cases/{case_id}/quality-reviews', response_model=QualityReviewListResponseV1)
@router.get('/cases/{case_id}/quality-reviews/', response_model=QualityReviewListResponseV1, include_in_schema=False)
def list_case_quality_reviews(case_id: str, db: Session = Depends(get_db)) -> QualityReviewListResponseV1:
    rows = _list_reviews(db, case_id=case_id)
    items = [_quality_review_item(row) for row in rows]
    return QualityReviewListResponseV1(items=items, total=len(items))


@router.post('/quality-reviews', response_model=QualityReviewResponseV1)
@router.post('/quality-reviews/', response_model=QualityReviewResponseV1, include_in_schema=False)
def create_quality_review(
    payload: QualityReviewCreateRequestV1,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> QualityReviewResponseV1:
    case_id, patient_id = _case_context_or_404(db, payload.case_id)

    try:
        target_type = QualityTargetType(payload.target_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_target_type', 'message': 'Unsupported target_type'}) from exc

    try:
        review_status = QualityReviewStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_status', 'message': 'Unsupported status'}) from exc

    try:
        severity = QualitySeverity(payload.severity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_severity', 'message': 'Unsupported severity'}) from exc

    try:
        attribution = QualityErrorAttribution(payload.attribution)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_attribution', 'message': 'Unsupported attribution'}) from exc

    trace_id = payload.trace_id
    if payload.related_feedback_id:
        related_feedback = _feedback_or_404(db, case_id, payload.related_feedback_id)
        if trace_id is None:
            trace_id = related_feedback['trace_id']
        elif trace_id != related_feedback['trace_id']:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'trace_mismatch', 'message': 'trace_id does not match related feedback trace'})
    if trace_id is None:
        trace_id = f'trace_stub_{uuid4().hex[:12]}'
    if payload.trace_id and not _trace_exists(db, trace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'trace_not_found', 'message': 'Trace not found'})

    actor_type, actor_id, actor_role = _actor_from_token(credentials, db)
    review_id = uuid4()
    now = datetime.now(UTC)
    related_refs = {
        'runtime_stub': True,
        'case_id': case_id,
        'trace_id': trace_id,
        'related_feedback_id': payload.related_feedback_id,
        'target_type': target_type.value,
        'target_id': payload.target_id,
        'actor_type': actor_type,
        'actor_id': actor_id,
        'actor_role': actor_role,
    }
    findings = {
        'summary': payload.summary,
        'runtime_stub': True,
        'target_type': target_type.value,
        'target_id': payload.target_id,
        'attribution': attribution.value,
        'severity': severity.value,
        'related_feedback_id': payload.related_feedback_id,
        'actor_type': actor_type,
        'actor_id': actor_id,
        'actor_role': actor_role,
    }

    try:
        db.execute(
            text('''
                insert into quality_reviews (
                  id, trace_id, case_id, patient_id, review_target_type, review_target_id,
                  status, severity, opened_by_type, opened_by_id, reason, error_attribution,
                  attribution_confidence, findings_json, related_refs_json, created_at, updated_at
                ) values (
                  :id, :trace_id, :case_id, :patient_id, :review_target_type, :review_target_id,
                  :status, :severity, :opened_by_type, :opened_by_id, :reason, :error_attribution,
                  :attribution_confidence, cast(:findings_json as jsonb), cast(:related_refs_json as jsonb),
                  :created_at, :updated_at
                )
            '''),
            {
                'id': review_id,
                'trace_id': trace_id,
                'case_id': UUID(case_id),
                'patient_id': UUID(patient_id) if patient_id else None,
                'review_target_type': target_type.value,
                'review_target_id': payload.target_id,
                'status': review_status.value,
                'severity': severity.value,
                'opened_by_type': actor_type,
                'opened_by_id': actor_id,
                'reason': payload.summary,
                'error_attribution': attribution.value,
                'attribution_confidence': payload.attribution_confidence,
                'findings_json': json.dumps(findings),
                'related_refs_json': json.dumps(related_refs),
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
            event_type='quality_review_created',
            source_record_type='quality_review',
            source_record_id=str(review_id),
            payload={
                'case_id': case_id,
                'trace_id': trace_id,
                'quality_review_id': str(review_id),
                'target_type': target_type.value,
                'target_id': payload.target_id,
                'attribution': attribution.value,
                'severity': severity.value,
                'related_feedback_id': payload.related_feedback_id,
                'actor_type': actor_type,
                'actor_id': actor_id,
                'actor_role': actor_role,
                'runtime_stub': True,
            },
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception('quality review persistence failed')
        raise HTTPException(status_code=503, detail={'code': 'quality_review_storage_unavailable', 'message': 'Quality review storage is unavailable.'}) from exc

    item = QualityReviewItemV1(
        review_id=str(review_id),
        case_id=case_id,
        trace_id=trace_id,
        target_type=target_type.value,
        target_id=payload.target_id,
        status=review_status.value,
        attribution=attribution.value,
        severity=severity.value,
        summary=payload.summary,
        related_feedback_id=payload.related_feedback_id,
        actor_type=actor_type,
        actor_id=actor_id,
        attribution_confidence=payload.attribution_confidence,
        created_at=now,
        updated_at=now,
    )
    return QualityReviewResponseV1(route='/api/v1/quality-reviews', item=item)
