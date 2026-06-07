from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import AccessAuditEvent, Case, User
from app.db.session import SessionLocal
from app.modules.auth.dependencies import require_roles
from .schemas import AccessAuditEventItemV1, AccessAuditEventListResponseV1

router = APIRouter()
ACCESS_AUDIT_READ_ROLES = ['doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin']
ADMIN_ACCESS_ROLES = {'admin', 'super_admin'}
audit_read_guard = require_roles(ACCESS_AUDIT_READ_ROLES)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _resolve_case(db: Session, case_identifier: str) -> Case | None:
    try:
        case_uuid = UUID(str(case_identifier))
    except ValueError:
        case_uuid = None

    if case_uuid is not None:
        case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
        if case is not None:
            return case

    return db.execute(select(Case).where(Case.case_no == case_identifier)).scalar_one_or_none()


def _event_item(row: AccessAuditEvent) -> AccessAuditEventItemV1:
    return AccessAuditEventItemV1(
        access_event_id=row.access_event_id,
        actor_user_id=row.actor_user_id,
        actor_type=row.actor_type,
        actor_role=row.actor_role,
        access_mode=row.access_mode,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        decision=row.decision,
        denial_reason=row.denial_reason,
        policy_source=row.policy_source,
        request_id=row.request_id,
        route_path=row.route_path,
        method=row.method,
        metadata_json=dict(row.metadata_json or {}),
        created_at=row.created_at,
    )


def _list_response(items: list[AccessAuditEventItemV1], total: int, limit: int, offset: int) -> AccessAuditEventListResponseV1:
    return AccessAuditEventListResponseV1(items=items, total=total, limit=limit, offset=offset)


def _apply_filters(rows: list[AccessAuditEvent], *, decision: str | None = None, resource_type: str | None = None, access_mode: str | None = None) -> list[AccessAuditEvent]:
    filtered: list[AccessAuditEvent] = []
    for row in rows:
        if decision is not None and row.decision != decision:
            continue
        if resource_type is not None and row.resource_type != resource_type:
            continue
        if access_mode is not None and row.access_mode != access_mode:
            continue
        filtered.append(row)
    return filtered


def _case_scoped_accessible_rows(db: Session, actor: User, rows: list[AccessAuditEvent]) -> list[AccessAuditEvent]:
    accessible: list[AccessAuditEvent] = []
    for row in rows:
        if row.case_id is not None:
            try:
                require_case_access(db, actor, row.case_id, access_level='summary')
            except HTTPException as exc:
                if exc.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND):
                    continue
                raise
            accessible.append(row)
            continue
        if actor.role in ADMIN_ACCESS_ROLES:
            accessible.append(row)
    return accessible


@router.get('/access-audit-events/{access_event_id}', response_model=AccessAuditEventItemV1)
def get_access_audit_event(access_event_id: str, db: Session = Depends(get_db), actor: User = Depends(audit_read_guard)) -> AccessAuditEventItemV1:
    row = db.execute(select(AccessAuditEvent).where(AccessAuditEvent.access_event_id == access_event_id)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'access_audit_event_not_found', 'message': 'Access audit event not found'})

    if row.case_id is not None:
        require_case_access(db, actor, row.case_id, access_level='summary')
    elif actor.role not in ADMIN_ACCESS_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code': 'access_denied', 'message': 'Insufficient role'})

    return _event_item(row)


@router.get('/cases/{case_id}/access-audit-events', response_model=AccessAuditEventListResponseV1)
def list_case_access_audit_events(
    case_id: str,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    decision: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    access_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: User = Depends(audit_read_guard),
) -> AccessAuditEventListResponseV1:
    case = _resolve_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})

    require_case_access(db, actor, case.id, access_level='summary')

    rows = db.execute(
        select(AccessAuditEvent)
        .where(AccessAuditEvent.case_id == case.id)
        .order_by(AccessAuditEvent.created_at.desc(), AccessAuditEvent.id.desc())
    ).scalars().all()
    filtered = _apply_filters(rows, decision=decision, resource_type=resource_type, access_mode=access_mode)
    total = len(filtered)
    paged = filtered[offset:offset + limit]
    return _list_response([_event_item(row) for row in paged], total, limit, offset)


@router.get('/traces/{trace_id}/access-audit-events', response_model=AccessAuditEventListResponseV1)
def list_trace_access_audit_events(
    trace_id: str,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    decision: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    access_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: User = Depends(audit_read_guard),
) -> AccessAuditEventListResponseV1:
    rows = db.execute(
        select(AccessAuditEvent)
        .where(AccessAuditEvent.trace_id == trace_id)
        .order_by(AccessAuditEvent.created_at.desc(), AccessAuditEvent.id.desc())
    ).scalars().all()
    accessible = _case_scoped_accessible_rows(db, actor, rows)
    filtered = _apply_filters(accessible, decision=decision, resource_type=resource_type, access_mode=access_mode)
    total = len(filtered)
    paged = filtered[offset:offset + limit]
    return _list_response([_event_item(row) for row in paged], total, limit, offset)
