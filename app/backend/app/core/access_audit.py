from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import AccessAuditEvent, User

logger = logging.getLogger('app.access_audit')
_BLOCKED_METADATA_KEYS = {
    'token',
    'authorization',
    'password',
    'secret',
    'mapped_features',
    'source_refs',
    'doctor_provided_features',
    'request_body',
    'raw_payload',
}
_MAX_METADATA_DEPTH = 4


def _is_blocked_metadata_key(key: str) -> bool:
    lowered = key.strip().lower()
    return any(blocked in lowered for blocked in _BLOCKED_METADATA_KEYS)


def _sanitize_metadata_value(value: Any, depth: int = 0) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if depth >= _MAX_METADATA_DEPTH:
        return {'redacted': True, 'type': type(value).__name__}
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_blocked_metadata_key(key_text):
                sanitized[key_text] = '[redacted]'
                continue
            sanitized[key_text] = _sanitize_metadata_value(item, depth + 1)
        return sanitized
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_metadata_value(item, depth + 1) for item in value]
    return {'redacted': True, 'type': type(value).__name__}


def sanitize_access_audit_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        return {'value': _sanitize_metadata_value(metadata)}
    return {
        str(key): _sanitize_metadata_value(value)
        for key, value in metadata.items()
        if not _is_blocked_metadata_key(str(key))
    }


def emit_access_audit_event(
    db: Session,
    *,
    actor_user: User | None,
    access_mode: str,
    resource_type: str,
    resource_id: str | None,
    decision: str,
    case_id: Any | None = None,
    patient_id: Any | None = None,
    trace_id: str | None = None,
    denial_reason: str | None = None,
    policy_source: str | None = None,
    request_id: str | None = None,
    route_path: str | None = None,
    method: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AccessAuditEvent | None:
    access_event_id = f'aae_{uuid4().hex[:16]}'
    event = AccessAuditEvent(
        access_event_id=access_event_id,
        actor_user_id=actor_user.id if actor_user else None,
        actor_type='user' if actor_user else 'system',
        actor_role=getattr(actor_user, 'role', None),
        access_mode=access_mode,
        resource_type=resource_type,
        resource_id=resource_id,
        case_id=case_id,
        patient_id=patient_id,
        trace_id=trace_id,
        decision=decision,
        denial_reason=denial_reason,
        policy_source=policy_source,
        request_id=request_id,
        route_path=route_path,
        method=method,
        metadata_json=sanitize_access_audit_metadata(metadata),
    )
    try:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception:
        db.rollback()
        logger.exception(
            'access audit emit failed access_event_id=%s resource_type=%s resource_id=%s decision=%s',
            access_event_id,
            resource_type,
            resource_id,
            decision,
        )
        return None
