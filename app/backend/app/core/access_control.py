from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Case, CaseModelInputSnapshot, User

SUMMARY_ACCESS_ROLES = {'doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin'}
DETAIL_ACCESS_ROLES = {'doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin'}
ADMIN_ACCESS_ROLES = {'admin', 'super_admin'}

_ACCESS_LEVEL_ROLES = {
    'summary': SUMMARY_ACCESS_ROLES,
    'detail': DETAIL_ACCESS_ROLES,
    'admin': ADMIN_ACCESS_ROLES,
}


def _normalize_case_id(case_id: UUID | str) -> UUID:
    if isinstance(case_id, UUID):
        return case_id
    try:
        return UUID(str(case_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'case_not_found', 'message': 'Case not found'},
        ) from exc


def _require_role(user: User, access_level: str) -> None:
    allowed_roles = _ACCESS_LEVEL_ROLES.get(access_level)
    if allowed_roles is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'invalid_access_level', 'message': f'Unknown access level: {access_level}'},
        )
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'code': 'access_denied', 'message': 'Insufficient role'},
        )


def require_case_access(db: Session, user: User, case_id: UUID | str, access_level: str = 'summary') -> Case:
    case_uuid = _normalize_case_id(case_id)
    _require_role(user, access_level)

    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'case_not_found', 'message': 'Case not found'},
        )

    # TODO(stage 105+): enforce ownership / assignment / care-team membership when those fields exist.
    #   - case_owner_user_id
    #   - assigned_doctor_ids
    #   - care_team_ids
    return case


def require_snapshot_access(db: Session, user: User, snapshot: CaseModelInputSnapshot, mode: str = 'summary') -> CaseModelInputSnapshot:
    access_level = 'detail' if mode == 'detail' else 'summary'
    require_case_access(db, user, snapshot.case_id, access_level=access_level)

    # TODO(stage 105+): snapshot-specific ACLs if snapshot-level ownership / visibility controls are introduced.
    return snapshot
