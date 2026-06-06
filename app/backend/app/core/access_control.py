from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Case, CaseAssignment, CaseModelInputSnapshot, User

SUMMARY_ACCESS_ROLES = {'doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin'}
DETAIL_ACCESS_ROLES = {'doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin'}
ADMIN_ACCESS_ROLES = {'admin', 'super_admin'}

CASE_ASSIGNMENT_ACCESS_LEVELS = {
    'owner': {'summary', 'detail'},
    'primary_doctor': {'summary', 'detail'},
    'consulting_doctor': {'summary', 'detail'},
    'qc_reviewer': {'summary'},
    'auditor': {'summary'},
    'admin_delegate': {'summary', 'detail', 'admin'},
}

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


def _has_case_ownership_policy(db: Session, case_uuid: UUID) -> bool:
    case_policy = db.execute(
        select(Case.owner_user_id, Case.primary_doctor_id).where(Case.id == case_uuid)
    ).first()
    if case_policy is None:
        return False
    owner_user_id, primary_doctor_id = case_policy
    if owner_user_id is not None or primary_doctor_id is not None:
        return True
    active_assignment_exists = db.execute(
        select(CaseAssignment.id)
        .where(CaseAssignment.case_id == case_uuid)
        .where(CaseAssignment.assignment_status == 'active')
        .limit(1)
    ).scalar_one_or_none()
    return active_assignment_exists is not None


def _assignment_allows_access(role_on_case: str | None, access_level: str) -> bool:
    normalized_role = (role_on_case or '').strip().lower()
    allowed_levels = CASE_ASSIGNMENT_ACCESS_LEVELS.get(normalized_role)
    if allowed_levels is None:
        return False
    return access_level in allowed_levels


def require_case_access(db: Session, user: User, case_id: UUID | str, access_level: str = 'summary') -> Case:
    case_uuid = _normalize_case_id(case_id)

    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'case_not_found', 'message': 'Case not found'},
        )

    if access_level not in _ACCESS_LEVEL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'invalid_access_level', 'message': f'Unknown access level: {access_level}'},
        )

    if user.role in ADMIN_ACCESS_ROLES:
        # TODO(stage 105+): add tenant / org scope checks before treating admin as global.
        return case

    # Ownership-aware path: once a case has explicit ownership or active assignments,
    # stop relying on dev fallback and evaluate the case-level policy.
    if case.owner_user_id == user.id or case.primary_doctor_id == user.id:
        if access_level == 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={'code': 'access_denied', 'message': 'Insufficient role'},
            )
        return case

    ownership_policy_present = _has_case_ownership_policy(db, case_uuid)
    if ownership_policy_present:
        active_assignment_roles = db.execute(
            select(CaseAssignment.role_on_case)
            .where(CaseAssignment.case_id == case_uuid)
            .where(CaseAssignment.user_id == user.id)
            .where(CaseAssignment.assignment_status == 'active')
        ).scalars().all()
        for role_on_case in active_assignment_roles:
            if _assignment_allows_access(role_on_case, access_level):
                return case
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'code': 'access_denied', 'message': 'Insufficient case ownership or assignment'},
        )

    # Dev/stub fallback: preserve current stage-104 compatibility for cases that do not yet
    # have production ownership policy rows. This must not be treated as the final policy.
    _require_role(user, access_level)
    return case


def require_snapshot_access(db: Session, user: User, snapshot: CaseModelInputSnapshot, mode: str = 'summary') -> CaseModelInputSnapshot:
    access_level = 'detail' if mode == 'detail' else 'summary'
    require_case_access(db, user, snapshot.case_id, access_level=access_level)

    # TODO(stage 105+): snapshot-specific ACLs if snapshot-level ownership / visibility controls are introduced.
    return snapshot


def resolve_case_access_policy_source(db: Session, user: User, case_id: UUID | str, access_level: str = 'summary') -> str:
    case_uuid = _normalize_case_id(case_id)

    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'case_not_found', 'message': 'Case not found'},
        )

    if access_level not in _ACCESS_LEVEL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'invalid_access_level', 'message': f'Unknown access level: {access_level}'},
        )

    if user.role in ADMIN_ACCESS_ROLES:
        return 'admin_override'

    if case.owner_user_id == user.id:
        return 'owner'
    if case.primary_doctor_id == user.id:
        return 'primary_doctor'

    ownership_policy_present = _has_case_ownership_policy(db, case_uuid)
    if ownership_policy_present:
        active_assignment_roles = db.execute(
            select(CaseAssignment.role_on_case)
            .where(CaseAssignment.case_id == case_uuid)
            .where(CaseAssignment.user_id == user.id)
            .where(CaseAssignment.assignment_status == 'active')
        ).scalars().all()
        for role_on_case in active_assignment_roles:
            normalized_role = (role_on_case or '').strip().lower()
            if _assignment_allows_access(role_on_case, access_level):
                if normalized_role == 'admin_delegate':
                    return 'admin_override'
                if normalized_role == 'qc_reviewer':
                    return 'assignment'
                if normalized_role == 'auditor':
                    return 'assignment'
                if normalized_role == 'consulting_doctor':
                    return 'assignment'
                if normalized_role == 'primary_doctor':
                    return 'primary_doctor'
                return 'assignment'
        return 'denied_no_policy'

    return 'dev_fallback'
