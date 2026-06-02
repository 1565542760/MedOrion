
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.enums import ModelApprovalState
from app.db.models import ModelRegistry, ModelVersion, User
from app.db.session import SessionLocal
from app.modules.auth.security import AuthError, auth_http_exception, decode_token
from app.modules.model_registry.schemas import (
    ModelRegistryCreateRequestV1,
    ModelRegistryDetailItemV1,
    ModelRegistryListResponseV1,
    ModelRegistryResponseV1,
    ModelRegistrySummaryItemV1,
    ModelVersionCreateRequestV1,
    ModelVersionEvaluationsItemV1,
    ModelVersionEvaluationsResponseV1,
    ModelVersionItemV1,
    ModelVersionPromoteRequestV1,
    ModelVersionResponseV1,
    ModelVersionRollbackRequestV1,
)

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)
router = APIRouter()
version_router = APIRouter()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, 'value') else str(value)


def _parse_uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _normalize_state(raw_state: str | None) -> ModelApprovalState:
    try:
        return ModelApprovalState(raw_state or ModelApprovalState.DRAFT.value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_approval_state', 'message': 'Unsupported model lifecycle state'}) from exc


def _maybe_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None

    try:
        payload = decode_token(credentials.credentials, expected_type='access')
    except AuthError as exc:
        raise auth_http_exception(exc) from exc

    try:
        user_id = UUID(str(payload.get('sub')))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'invalid_token', 'message': 'Token missing subject'}) from exc

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'user_inactive', 'message': 'User not active'})
    return user


def _notes(runtime_constraints: dict | str | None) -> str | None:
    if isinstance(runtime_constraints, dict):
        value = runtime_constraints.get('notes')
        return value if isinstance(value, str) else None
    return None


def _version_item(version: ModelVersion) -> ModelVersionItemV1:
    return ModelVersionItemV1(
        version_id=version.id,
        model_id=version.model_id,
        version_label=version.version_label,
        approval_state=_enum_value(version.approval_state),
        contract_version=version.contract_version,
        artifact_ref=version.artifact_ref_json,
        input_schema=version.input_schema_json,
        output_schema=version.output_schema_json,
        metrics=version.metrics_json,
        runtime_constraints=version.runtime_constraints_json,
        notes=_notes(version.runtime_constraints_json),
        approved_by=version.approved_by,
        approved_at=version.approved_at,
        promoted_by=version.promoted_by,
        promoted_at=version.promoted_at,
        archived_at=version.archived_at,
        rollback_from_version_id=version.rollback_from_version_id,
        published_at=version.published_at,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def _registry_summary_item(model: ModelRegistry) -> ModelRegistrySummaryItemV1:
    return ModelRegistrySummaryItemV1(
        model_id=model.id,
        model_name=model.model_name,
        disease_agent=model.disease_agent,
        task_type=model.task_type,
        modality_scope=list(model.modality_scope_json or []),
        owner_team=model.owner_team,
        description=model.description,
        is_active=bool(model.is_active),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _registry_detail_item(db: Session, model: ModelRegistry) -> ModelRegistryDetailItemV1:
    versions = db.execute(
        select(ModelVersion)
        .where(ModelVersion.model_id == model.id)
        .order_by(ModelVersion.created_at.desc(), ModelVersion.id.desc())
    ).scalars().all()
    return ModelRegistryDetailItemV1(**_registry_summary_item(model).model_dump(), versions=[_version_item(row) for row in versions])


def _ensure_mutable(version: ModelVersion) -> None:
    if _enum_value(version.approval_state) == ModelApprovalState.ARCHIVED.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'version_archived', 'message': 'Archived versions cannot be changed'})


def _downgrade_existing_defaults(db: Session, model_id: UUID, exclude_version_id: UUID | None = None) -> None:
    statement = select(ModelVersion).where(
        ModelVersion.model_id == model_id,
        ModelVersion.approval_state == ModelApprovalState.DEFAULT.value,
    )
    if exclude_version_id is not None:
        statement = statement.where(ModelVersion.id != exclude_version_id)
    defaults = db.execute(statement).scalars().all()
    for row in defaults:
        row.approval_state = ModelApprovalState.APPROVED.value
    if defaults:
        db.flush()


@router.get('', response_model=ModelRegistryListResponseV1)
@router.get('/', response_model=ModelRegistryListResponseV1, include_in_schema=False)
def list_models(db: Session = Depends(get_db)) -> ModelRegistryListResponseV1:
    rows = db.execute(select(ModelRegistry).order_by(ModelRegistry.created_at.desc(), ModelRegistry.id.desc())).scalars().all()
    return ModelRegistryListResponseV1(items=[_registry_summary_item(row) for row in rows], total=len(rows))


@router.post('', response_model=ModelRegistryResponseV1)
@router.post('/', response_model=ModelRegistryResponseV1, include_in_schema=False)
def register_model(payload: ModelRegistryCreateRequestV1, db: Session = Depends(get_db), actor: User | None = Depends(_maybe_current_user)) -> ModelRegistryResponseV1:
    model = ModelRegistry(
        id=uuid4(),
        model_name=payload.model_name,
        disease_agent=payload.disease_agent,
        task_type=payload.task_type,
        modality_scope_json=list(payload.modality_scope or []),
        owner_team=payload.owner_team,
        description=payload.description,
        is_active=payload.is_active,
    )
    try:
        db.add(model)
        db.commit()
        db.refresh(model)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'model_registry_conflict', 'message': 'Model registry already exists or violates constraints'}) from exc

    logger.info('model_registry_created model_id=%s actor=%s', model.id, actor.id if actor else 'system')
    return ModelRegistryResponseV1(route='/api/v1/model-registry', item=_registry_detail_item(db, model))


@router.get('/{model_id}', response_model=ModelRegistryResponseV1)
def get_model(model_id: UUID, db: Session = Depends(get_db)) -> ModelRegistryResponseV1:
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_not_found', 'message': 'Model registry entry not found'})
    return ModelRegistryResponseV1(route=f'/api/v1/model-registry/{model_id}', item=_registry_detail_item(db, model))


@router.post('/{model_id}/versions', response_model=ModelVersionResponseV1)
def create_version(
    model_id: UUID,
    payload: ModelVersionCreateRequestV1,
    db: Session = Depends(get_db),
    actor: User | None = Depends(_maybe_current_user),
) -> ModelVersionResponseV1:
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_not_found', 'message': 'Model registry entry not found'})

    approval_state = _normalize_state(payload.approval_state)
    version_id = uuid4()
    now = datetime.now(UTC)

    try:
        if approval_state.value == ModelApprovalState.DEFAULT.value:
            _downgrade_existing_defaults(db, model_id)

        version = ModelVersion(
            id=version_id,
            model_id=model.id,
            version_label=payload.version_label,
            approval_state=approval_state.value,
            contract_version=payload.contract_version,
            artifact_ref_json=payload.artifact_ref,
            input_schema_json=payload.input_schema,
            output_schema_json=payload.output_schema,
            metrics_json=payload.metrics,
            runtime_constraints_json=payload.runtime_constraints,
            published_at=now if approval_state.value in {ModelApprovalState.APPROVED.value, ModelApprovalState.DEFAULT.value, ModelApprovalState.SHADOW.value, ModelApprovalState.CANARY.value, ModelApprovalState.ARCHIVED.value} else None,
        )
        if isinstance(version.runtime_constraints_json, dict) and payload.notes is not None:
            version.runtime_constraints_json = {**version.runtime_constraints_json, 'notes': payload.notes}
        elif payload.notes is not None:
            version.runtime_constraints_json = {'notes': payload.notes}

        if approval_state.value == ModelApprovalState.APPROVED.value:
            version.approved_by = actor.id if actor else None
            version.approved_at = now
        elif approval_state.value in {ModelApprovalState.SHADOW.value, ModelApprovalState.CANARY.value, ModelApprovalState.DEFAULT.value}:
            version.promoted_by = actor.id if actor else None
            version.promoted_at = now
        elif approval_state.value == ModelApprovalState.ARCHIVED.value:
            version.archived_at = now

        db.add(version)
        db.commit()
        db.refresh(version)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'model_version_conflict', 'message': 'Model version already exists or violates constraints'}) from exc

    logger.info('model_version_created model_id=%s version_id=%s actor=%s approval_state=%s', model.id, version.id, actor.id if actor else 'system', approval_state.value)
    return ModelVersionResponseV1(route=f'/api/v1/model-registry/{model_id}/versions', item=_version_item(version))


@version_router.post('/model-versions/{version_id}/approve', response_model=ModelVersionResponseV1)
def approve_version(version_id: UUID, db: Session = Depends(get_db), actor: User | None = Depends(_maybe_current_user)) -> ModelVersionResponseV1:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'version_not_found', 'message': 'Model version not found'})
    _ensure_mutable(version)

    now = datetime.now(UTC)
    version.approval_state = ModelApprovalState.APPROVED.value
    version.approved_at = now
    version.approved_by = actor.id if actor else None
    if version.published_at is None:
        version.published_at = now
    db.commit()
    db.refresh(version)

    logger.info('model_version_approved model_id=%s version_id=%s actor=%s', version.model_id, version.id, actor.id if actor else 'system')
    return ModelVersionResponseV1(route=f'/api/v1/model-versions/{version_id}/approve', item=_version_item(version))


@version_router.post('/model-versions/{version_id}/promote', response_model=ModelVersionResponseV1)
def promote_version(
    version_id: UUID,
    payload: ModelVersionPromoteRequestV1,
    db: Session = Depends(get_db),
    actor: User | None = Depends(_maybe_current_user),
) -> ModelVersionResponseV1:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'version_not_found', 'message': 'Model version not found'})
    _ensure_mutable(version)

    try:
        target_state = ModelApprovalState(payload.target_state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_target_state', 'message': 'Unsupported promote target state'}) from exc

    if target_state.value not in {ModelApprovalState.SHADOW.value, ModelApprovalState.CANARY.value, ModelApprovalState.DEFAULT.value}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_target_state', 'message': 'Promote only supports shadow, canary, or default'})
    if _enum_value(version.approval_state) == ModelApprovalState.DRAFT.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'version_not_promotable', 'message': 'Draft versions must be approved before promotion'})

    now = datetime.now(UTC)
    if target_state.value == ModelApprovalState.DEFAULT.value:
        _downgrade_existing_defaults(db, version.model_id, exclude_version_id=version.id)
    version.approval_state = target_state.value
    version.promoted_at = now
    version.promoted_by = actor.id if actor else None
    if version.published_at is None:
        version.published_at = now
    db.commit()
    db.refresh(version)

    logger.info('model_version_promoted model_id=%s version_id=%s target_state=%s actor=%s', version.model_id, version.id, target_state.value, actor.id if actor else 'system')
    return ModelVersionResponseV1(route=f'/api/v1/model-versions/{version_id}/promote', item=_version_item(version))


@version_router.post('/model-versions/{version_id}/rollback', response_model=ModelVersionResponseV1)
def rollback_version(
    version_id: UUID,
    payload: ModelVersionRollbackRequestV1,
    db: Session = Depends(get_db),
    actor: User | None = Depends(_maybe_current_user),
) -> ModelVersionResponseV1:
    target = db.execute(select(ModelVersion).where(ModelVersion.id == version_id)).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'version_not_found', 'message': 'Model version not found'})
    _ensure_mutable(target)

    rollback_to = db.execute(select(ModelVersion).where(ModelVersion.id == payload.rollback_to_version_id)).scalar_one_or_none()
    if rollback_to is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'rollback_target_not_found', 'message': 'Rollback target version not found'})
    if rollback_to.model_id != target.model_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'code': 'rollback_model_mismatch', 'message': 'Rollback target must belong to the same model'})
    _ensure_mutable(rollback_to)

    current_default = db.execute(
        select(ModelVersion).where(
            ModelVersion.model_id == target.model_id,
            ModelVersion.approval_state == ModelApprovalState.DEFAULT.value,
            ModelVersion.id != target.id,
        )
    ).scalar_one_or_none()

    now = datetime.now(UTC)
    if current_default is not None:
        current_default.approval_state = ModelApprovalState.APPROVED.value
        db.flush()
    target.approval_state = ModelApprovalState.DEFAULT.value
    target.rollback_from_version_id = current_default.id if current_default is not None else rollback_to.id
    target.promoted_at = now
    target.promoted_by = actor.id if actor else None
    if target.published_at is None:
        target.published_at = now
    db.commit()
    db.refresh(target)

    logger.info('model_version_rollback model_id=%s version_id=%s rollback_to=%s actor=%s', target.model_id, target.id, rollback_to.id, actor.id if actor else 'system')
    return ModelVersionResponseV1(route=f'/api/v1/model-versions/{version_id}/rollback', item=_version_item(target))


@version_router.get('/model-versions/{version_id}/evaluations', response_model=ModelVersionEvaluationsResponseV1)
def get_version_evaluations(version_id: UUID, db: Session = Depends(get_db)) -> ModelVersionEvaluationsResponseV1:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'version_not_found', 'message': 'Model version not found'})
    return ModelVersionEvaluationsResponseV1(
        route=f'/api/v1/model-versions/{version_id}/evaluations',
        item=ModelVersionEvaluationsItemV1(
            version_id=version.id,
            model_id=version.model_id,
            approval_state=_enum_value(version.approval_state),
            artifact_ref=version.artifact_ref_json,
            metrics=version.metrics_json,
            runtime_constraints=version.runtime_constraints_json,
            notes=_notes(version.runtime_constraints_json),
            published_at=version.published_at,
            created_at=version.created_at,
            updated_at=version.updated_at,
        ),
    )
