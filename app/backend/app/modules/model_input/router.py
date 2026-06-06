from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CaseModelInputSnapshot, ModelRegistry, ModelVersion, User
from app.db.session import SessionLocal
from app.core.access_audit import emit_access_audit_event
from app.core.access_control import require_case_access, require_snapshot_access, resolve_case_access_policy_source
from app.modules.auth.dependencies import require_roles
from app.modules.inference.persistence import resolve_case_context
from app.modules.model_input.catalog import DISEASE_TASK_SCHEMA_ORDER, FEATURE_SETS, MODEL_INPUT_SCHEMA_PROFILES, TASK_MODEL_FILTERS
from app.modules.model_input.schemas import (
    ModelFeatureRequirementItemV1,
    ModelFeatureRequirementsResponseV1,
    ModelInputAssessmentItemV1,
    ModelInputPreviewRequestV1,
    ModelInputPreviewResponseV1,
    ModelInputSchemaItemV1,
    ModelInputValidationRequestV1,
    ModelInputValidationResponseV1,
    ModelInputSnapshotCreateRequestV1,
    ModelInputSnapshotItemV1,
    ModelInputSnapshotListResponseV1,
    ModelInputSnapshotSummaryItemV1,
    ModelMissingRequiredFeatureItemV1,
    ModelSelectionCandidateItemV1,
    ModelSelectionPreviewRequestV1,
    ModelSelectionPreviewResponseV1,
)

router = APIRouter()
logger = logging.getLogger('app.model_input')

SNAPSHOT_READ_ROLES = ['doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin']
SNAPSHOT_WRITE_ROLES = ['doctor', 'admin', 'super_admin']
snapshot_read_guard = require_roles(SNAPSHOT_READ_ROLES)
snapshot_write_guard = require_roles(SNAPSHOT_WRITE_ROLES)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _lower(value: str | None) -> str:
    return (value or '').strip().lower()


def _normalize_disease_task(value: str | None) -> str:
    normalized = _lower(value).replace(' ', '_')
    if normalized in {'capcop', 'cap_cop', 'cap/cop', 'cap-cop', 'cap_cop_classification'}:
        return 'cap_cop'
    if normalized in {'pulmonary_triage', 'pulmonarytriage'}:
        return 'pulmonary_triage'
    return normalized or 'unknown'


def _is_missing(value: Any) -> bool:
    return value is None or value == '' or value == [] or value == {}


def _feature_requirement_item(feature: dict[str, Any]) -> ModelFeatureRequirementItemV1:
    return ModelFeatureRequirementItemV1(
        feature_order=int(feature['feature_order']),
        source_clinical_field=str(feature['source_clinical_field']),
        model_feature_name=str(feature['model_feature_name']),
        feature_type=str(feature['feature_type']),
        required=bool(feature['required']),
        optional=bool(feature['optional']),
        defaultable=bool(feature['defaultable']),
        default_strategy=feature.get('default_strategy'),
        missing_value_policy=feature.get('missing_value_policy'),
        unit=feature.get('unit'),
        value_range=feature.get('value_range'),
        enum_mapping=feature.get('enum_mapping'),
        notes=feature.get('notes'),
    )


def _schema_profile_for_disease_task(disease_task: str) -> dict[str, Any] | None:
    normalized = _normalize_disease_task(disease_task)
    profile_ids = DISEASE_TASK_SCHEMA_ORDER.get(normalized, [])
    if not profile_ids:
        return None
    return MODEL_INPUT_SCHEMA_PROFILES[profile_ids[0]]


def _profile_for_model(model: ModelRegistry, version: ModelVersion) -> dict[str, Any] | None:
    disease_agent = _lower(model.disease_agent)
    task_type = _normalize_disease_task(model.task_type)
    if disease_agent == 'pulmonary_triage' or task_type == 'pulmonary_triage':
        return MODEL_INPUT_SCHEMA_PROFILES['clinical_mlp_pulmonary_triage_input_schema_v1']
    if disease_agent in {'capcop_agent', 'cap_cop'} or task_type == 'cap_cop':
        model_name = _lower(model.model_name)
        version_label = _lower(version.version_label)
        modality_scope = {str(item).lower() for item in (model.modality_scope_json or [])}
        if 'multimodal' in model_name or 'multimodal' in version_label or {'ct_image', 'mri_image', 'clinical_table'}.issubset(modality_scope):
            return MODEL_INPUT_SCHEMA_PROFILES['multimodal_resnet18_cap_cop_input_schema_v1']
        if 'image' in model_name or 'resnet' in model_name or ({'ct_image', 'mri_image'} & modality_scope and 'clinical_table' not in modality_scope):
            return MODEL_INPUT_SCHEMA_PROFILES['imaging_resnet18_cap_cop_input_schema_v1']
        return MODEL_INPUT_SCHEMA_PROFILES['clinical_mlp_cap_cop_input_schema_v1']
    return None


def _model_version_row(db: Session, model_version_id: UUID) -> tuple[ModelRegistry, ModelVersion]:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_input_schema_not_found', 'message': 'Model input schema not found'})
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == version.model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_input_schema_not_found', 'message': 'Model input schema not found'})
    return model, version


def _schema_item(db: Session, model_version_id: UUID) -> ModelInputSchemaItemV1:
    model, version = _model_version_row(db, model_version_id)
    profile = _profile_for_model(model, version)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_input_schema_not_found', 'message': 'Model input schema not found'})
    feature_set = FEATURE_SETS[profile['feature_set_id']]
    requirements = [_feature_requirement_item(feature) for feature in profile['feature_requirements']]
    return ModelInputSchemaItemV1(
        model_version_id=version.id,
        model_id=model.id,
        model_name=model.model_name,
        version_label=version.version_label,
        model_input_schema_id=profile['schema_id'],
        model_input_schema_key=profile['schema_key'],
        model_input_schema_name=profile['schema_name'],
        schema_version=profile['schema_version'],
        disease_task=profile['disease_task'],
        disease_task_feature_set_id=feature_set['feature_set_id'],
        disease_task_feature_set_key=feature_set['feature_set_key'],
        disease_task_feature_set_name=feature_set['feature_set_name'],
        supported_disease_tasks=list(profile['supported_disease_tasks']),
        supported_modalities=list(profile['supported_modalities']),
        lifecycle_status=profile['lifecycle_status'],
        model_family=profile.get('model_family'),
        preprocess_artifact_ref=profile.get('preprocess_artifact_ref'),
        feature_count=len(requirements),
        feature_requirements=requirements,
        limitations=list(profile.get('limitations') or []),
        runtime_stub=True,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def build_model_input_schema_for_version(model: ModelRegistry, version: ModelVersion) -> ModelInputSchemaItemV1:
    profile = _profile_for_model(model, version)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_input_schema_not_found', 'message': 'Model input schema not found'})
    if profile['schema_id'] != 'clinical_mlp_cap_cop_input_schema_v1':
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'unsupported_disease_task', 'message': 'Only CAP/COP clinical MLP controlled shadow execution is supported'})
    return _schema_item_from_profile(model, version, profile)


def build_model_input_assessment_from_schema(schema_item: ModelInputSchemaItemV1, provided_features: dict[str, Any] | None = None) -> ModelInputAssessmentItemV1:
    return _assessment_item(schema_item, provided_features)


def _resolve_case(db: Session, case_identifier: str) -> tuple[UUID, UUID]:
    try:
        case_id_text, patient_id_text = resolve_case_context(db, case_identifier)
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'}) from exc
        raise
    return UUID(case_id_text), UUID(patient_id_text)


def _assessment_item(schema_item: ModelInputSchemaItemV1, provided_features: dict[str, Any] | None = None) -> ModelInputAssessmentItemV1:
    provided = {str(key): value for key, value in (provided_features or {}).items()}
    mapped_features: dict[str, Any] = {}
    missing_features: list[str] = []
    missing_required_features: list[str] = []
    missing_required_details: list[ModelMissingRequiredFeatureItemV1] = []
    defaultable_features: list[str] = []
    suggested_doctor_questions: list[str] = []

    for feature in schema_item.feature_requirements:
        key = feature.model_feature_name
        value = provided.get(key)
        if _is_missing(value):
            missing_features.append(key)
            if feature.required:
                missing_required_features.append(key)
                question = f'Please provide {key}.'
                suggested_doctor_questions.append(question)
                missing_required_details.append(
                    ModelMissingRequiredFeatureItemV1(
                        model_feature_name=key,
                        source_clinical_field=feature.source_clinical_field,
                        why_required=feature.notes or f'{key} is required for this model input schema.',
                        default_strategy=feature.default_strategy,
                        missing_value_policy=feature.missing_value_policy,
                        suggested_doctor_question=question,
                    )
                )
                if feature.defaultable:
                    defaultable_features.append(key)
            continue
        mapped_features[key] = value

    default_strategy_available = bool(defaultable_features)
    if missing_required_features and not default_strategy_available:
        current_status = 'insufficient_data_for_assessment'
        insufficient = True
        requires_doctor_confirmation = False
    elif missing_required_features:
        current_status = 'awaiting_default_or_doctor_confirmation'
        insufficient = False
        requires_doctor_confirmation = True
    else:
        current_status = 'ready_for_inference'
        insufficient = False
        requires_doctor_confirmation = False

    return ModelInputAssessmentItemV1(
        model_version_id=schema_item.model_version_id,
        model_input_schema_id=schema_item.model_input_schema_id,
        model_input_schema_key=schema_item.model_input_schema_key,
        disease_task_feature_set_id=schema_item.disease_task_feature_set_id,
        disease_task_feature_set_key=schema_item.disease_task_feature_set_key,
        disease_task=schema_item.disease_task,
        mapped_features=mapped_features,
        missing_features=missing_features,
        missing_required_features=missing_required_features,
        missing_required_details=missing_required_details,
        defaultable_features=defaultable_features,
        suggested_doctor_questions=suggested_doctor_questions,
        current_assessment_status=current_status,
        insufficient_data_for_assessment=insufficient,
        default_strategy_available=default_strategy_available,
        requires_doctor_confirmation=requires_doctor_confirmation,
        feature_count=schema_item.feature_count,
        mapped_feature_count=len(mapped_features),
        runtime_stub=True,
        limitations=list(schema_item.limitations),
    )


def _candidate_versions(db: Session, disease_task: str) -> list[tuple[ModelRegistry, ModelVersion]]:
    normalized = _normalize_disease_task(disease_task)
    filters = TASK_MODEL_FILTERS.get(normalized)
    if not filters:
        return []
    rows = db.execute(
        select(ModelRegistry, ModelVersion)
        .join(ModelVersion, ModelVersion.model_id == ModelRegistry.id)
        .where(ModelRegistry.disease_agent == filters['disease_agent'])
        .where(ModelRegistry.task_type == filters['task_type'])
        .order_by(ModelRegistry.id.asc(), ModelVersion.created_at.desc(), ModelVersion.id.desc())
    ).all()
    unique: list[tuple[ModelRegistry, ModelVersion]] = []
    seen: set[str] = set()
    for model, version in rows:
        model_id = str(model.id)
        if model_id in seen:
            continue
        seen.add(model_id)
        unique.append((model, version))
    return unique


def _candidate_profiles(disease_task: str) -> list[dict[str, Any]]:
    normalized = _normalize_disease_task(disease_task)
    profile_ids = DISEASE_TASK_SCHEMA_ORDER.get(normalized)
    if not profile_ids:
        return []
    return [MODEL_INPUT_SCHEMA_PROFILES[profile_id] for profile_id in profile_ids]


def _lifecycle_rank(status: str) -> float:
    return {
        'default': 1.0,
        'approved': 0.95,
        'canary': 0.9,
        'shadow': 0.8,
        'offline_evaluated': 0.7,
        'draft': 0.2,
        'deprecated': 0.15,
        'archived': 0.0,
    }.get(status, 0.5)


def _modality_score(candidate_modalities: list[str], requested_modalities: list[str]) -> float:
    requested = {str(value).lower() for value in requested_modalities if value}
    if not requested:
        return 1.0
    supported = {str(value).lower() for value in candidate_modalities if value}
    return 1.0 if requested.intersection(supported) else 0.2


def _candidate_item(
    model: ModelRegistry,
    version: ModelVersion,
    profile: dict[str, Any],
    provided_features: dict[str, Any] | None,
    available_modalities: list[str] | None,
) -> ModelSelectionCandidateItemV1:
    schema_item = _schema_item_from_profile(model, version, profile)
    assessment = _assessment_item(schema_item, provided_features)
    completeness = 0.0 if assessment.feature_count == 0 else round(assessment.mapped_feature_count / assessment.feature_count, 3)
    modality = _modality_score(list(profile.get('supported_modalities') or []), available_modalities or [])
    lifecycle = _lifecycle_rank(_lower(assessment.current_assessment_status) if assessment.current_assessment_status else _lower(profile['lifecycle_status']))
    score = round((completeness * 0.6) + (modality * 0.2) + (lifecycle * 0.2), 3)
    if assessment.current_assessment_status == 'insufficient_data_for_assessment':
        reason = 'candidate lacks required features and cannot be selected without consultation or defaults'
    elif assessment.missing_required_features:
        reason = 'candidate needs default or doctor confirmation for missing required inputs'
    elif modality < 1.0:
        reason = 'candidate has a partial modality mismatch but still matches the disease_task filter'
    else:
        reason = 'candidate supports the disease_task and meets the current input availability'
    return ModelSelectionCandidateItemV1(
        model_version_id=version.id,
        model_id=model.id,
        model_name=model.model_name,
        version_label=version.version_label,
        model_input_schema_id=profile['schema_id'],
        model_input_schema_key=profile['schema_key'],
        lifecycle_status=_lower(_enum_to_text(version.approval_state)) or profile['lifecycle_status'],
        supported_modalities=list(profile.get('supported_modalities') or []),
        feature_completeness=score,
        missing_fields=assessment.missing_features,
        missing_required_features=assessment.missing_required_features,
        defaultable_features=assessment.defaultable_features,
        suitability_reason=reason,
        current_assessment_status=assessment.current_assessment_status,
        insufficient_data_for_assessment=assessment.insufficient_data_for_assessment,
        runtime_stub=True,
    )


def _enum_to_text(value: Any) -> str:
    return value.value if hasattr(value, 'value') else str(value)


def _schema_item_from_profile(model: ModelRegistry, version: ModelVersion, profile: dict[str, Any]) -> ModelInputSchemaItemV1:
    feature_set = FEATURE_SETS[profile['feature_set_id']]
    requirements = [_feature_requirement_item(feature) for feature in profile['feature_requirements']]
    return ModelInputSchemaItemV1(
        model_version_id=version.id,
        model_id=model.id,
        model_name=model.model_name,
        version_label=version.version_label,
        model_input_schema_id=profile['schema_id'],
        model_input_schema_key=profile['schema_key'],
        model_input_schema_name=profile['schema_name'],
        schema_version=profile['schema_version'],
        disease_task=profile['disease_task'],
        disease_task_feature_set_id=feature_set['feature_set_id'],
        disease_task_feature_set_key=feature_set['feature_set_key'],
        disease_task_feature_set_name=feature_set['feature_set_name'],
        supported_disease_tasks=list(profile['supported_disease_tasks']),
        supported_modalities=list(profile['supported_modalities']),
        lifecycle_status=profile['lifecycle_status'],
        model_family=profile.get('model_family'),
        preprocess_artifact_ref=profile.get('preprocess_artifact_ref'),
        feature_count=len(requirements),
        feature_requirements=requirements,
        limitations=list(profile.get('limitations') or []),
        runtime_stub=True,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.get('/model-input-schemas/{model_version_id}', response_model=ModelInputSchemaItemV1)
def get_model_input_schema(model_version_id: UUID, db: Session = Depends(get_db)) -> ModelInputSchemaItemV1:
    model, version = _model_version_row(db, model_version_id)
    profile = _profile_for_model(model, version)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_input_schema_not_found', 'message': 'Model input schema not found'})
    return _schema_item_from_profile(model, version, profile)


@router.get('/model-input-schemas/{model_version_id}/feature-requirements', response_model=ModelFeatureRequirementsResponseV1)
def get_feature_requirements(model_version_id: UUID, db: Session = Depends(get_db)) -> ModelFeatureRequirementsResponseV1:
    schema_item = get_model_input_schema(model_version_id, db)
    return ModelFeatureRequirementsResponseV1(
        route=f'/api/v1/model-input-schemas/{model_version_id}/feature-requirements',
        model_version_id=schema_item.model_version_id,
        model_input_schema_id=schema_item.model_input_schema_id,
        model_input_schema_key=schema_item.model_input_schema_key,
        disease_task_feature_set_id=schema_item.disease_task_feature_set_id,
        disease_task_feature_set_key=schema_item.disease_task_feature_set_key,
        feature_count=schema_item.feature_count,
        required_count=sum(1 for item in schema_item.feature_requirements if item.required),
        optional_count=sum(1 for item in schema_item.feature_requirements if item.optional),
        defaultable_count=sum(1 for item in schema_item.feature_requirements if item.defaultable),
        feature_requirements=schema_item.feature_requirements,
        runtime_stub=True,
        limitations=list(schema_item.limitations),
    )


@router.post('/cases/{case_id}/model-input-preview', response_model=ModelInputPreviewResponseV1)
def model_input_preview(case_id: str, payload: ModelInputPreviewRequestV1, db: Session = Depends(get_db)) -> ModelInputPreviewResponseV1:
    _resolve_case(db, case_id)
    schema_item = get_model_input_schema(payload.model_version_id, db)
    if _normalize_disease_task(payload.disease_task) not in {_normalize_disease_task(task) for task in schema_item.supported_disease_tasks}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'unsupported_disease_task', 'message': 'The requested disease_task is not supported by this model input schema'})
    assessment = _assessment_item(schema_item, payload.provided_features)
    return ModelInputPreviewResponseV1(route=f'/api/v1/cases/{case_id}/model-input-preview', item=assessment)


@router.post('/cases/{case_id}/model-input-validation', response_model=ModelInputValidationResponseV1)
def model_input_validation(case_id: str, payload: ModelInputValidationRequestV1, db: Session = Depends(get_db)) -> ModelInputValidationResponseV1:
    _resolve_case(db, case_id)
    schema_item = get_model_input_schema(payload.model_version_id, db)
    if _normalize_disease_task(payload.disease_task) not in {_normalize_disease_task(task) for task in schema_item.supported_disease_tasks}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'unsupported_disease_task', 'message': 'The requested disease_task is not supported by this model input schema'})
    assessment = _assessment_item(schema_item, payload.provided_features)
    if assessment.insufficient_data_for_assessment:
        assessment.current_assessment_status = 'insufficient_data_for_assessment'
    elif assessment.default_strategy_available and assessment.missing_required_features:
        assessment.current_assessment_status = 'awaiting_default_or_doctor_confirmation'
        assessment.requires_doctor_confirmation = True
    elif assessment.missing_required_features:
        assessment.current_assessment_status = 'insufficient_data_for_assessment'
        assessment.insufficient_data_for_assessment = True
    return ModelInputValidationResponseV1(route=f'/api/v1/cases/{case_id}/model-input-validation', item=assessment)


@router.post('/cases/{case_id}/model-selection-preview', response_model=ModelSelectionPreviewResponseV1)
def model_selection_preview(case_id: str, payload: ModelSelectionPreviewRequestV1, db: Session = Depends(get_db)) -> ModelSelectionPreviewResponseV1:
    _resolve_case(db, case_id)
    disease_task = _normalize_disease_task(payload.disease_task)
    profiles = _candidate_profiles(disease_task)
    if not profiles:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'unsupported_disease_task', 'message': 'No model input schema is configured for this disease_task'})
    candidates = _candidate_versions(db, disease_task)
    if not candidates:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'unsupported_disease_task', 'message': 'No models support the requested disease_task'})
    if len(candidates) == 1:
        model, version = candidates[0]
        profile = profiles[0]
        validation = _assessment_item(_schema_item_from_profile(model, version, profile), payload.provided_features)
        selected_candidate = _candidate_item(model, version, profile, payload.provided_features, payload.available_modalities)
        return ModelSelectionPreviewResponseV1(
            route=f'/api/v1/cases/{case_id}/model-selection-preview',
            disease_task=disease_task,
            selection_required=False,
            selection_reason='single_candidate',
            candidate_count=1,
            selected_candidate=selected_candidate,
            validation=validation,
            candidates=[selected_candidate],
            runtime_stub=True,
            limitations=['metadata_only', 'no_live_inference', 'single_candidate_disease_task'],
        )
    candidate_items: list[ModelSelectionCandidateItemV1] = []
    for index, (model, version) in enumerate(candidates):
        profile = profiles[index % len(profiles)]
        candidate_items.append(_candidate_item(model, version, profile, payload.provided_features, payload.available_modalities))
    candidate_items.sort(key=lambda item: item.feature_completeness, reverse=True)
    return ModelSelectionPreviewResponseV1(
        route=f'/api/v1/cases/{case_id}/model-selection-preview',
        disease_task=disease_task,
        selection_required=True,
        selection_reason='multiple_candidates',
        candidate_count=len(candidate_items),
        selected_candidate=None,
        validation=None,
        candidates=candidate_items,
        runtime_stub=True,
        limitations=['metadata_only', 'no_live_inference', 'llm_only_explains_not_decides'],
    )


SNAPSHOT_STATUS_VALUES = {
    'ready_for_inference',
    'insufficient_data_for_assessment',
    'missing_required_features',
    'default_applied',
    'doctor_confirmation_required',
    'validation_failed',
}


def _snapshot_summary_item_from_row(row: CaseModelInputSnapshot) -> ModelInputSnapshotSummaryItemV1:
    mapped_features = row.mapped_features_json or {}
    missing_features = list(row.missing_features_json or [])
    defaulted_features = list(row.defaulted_features_json or [])
    doctor_provided_features = list(row.doctor_provided_features_json or [])
    source_refs = list(row.source_refs_json or [])
    return ModelInputSnapshotSummaryItemV1(
        id=row.id,
        input_snapshot_id=row.input_snapshot_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        model_version_id=row.model_version_id,
        model_input_schema_id=row.model_input_schema_id,
        disease_task_feature_set_id=row.disease_task_feature_set_id,
        validation_status=row.validation_status,
        current_assessment_status=row.current_assessment_status,
        insufficient_data_for_assessment=bool(row.insufficient_data_for_assessment),
        runtime_stub=bool(row.runtime_stub),
        not_for_diagnosis=bool(row.not_for_diagnosis),
        mapped_feature_count=len(mapped_features) if isinstance(mapped_features, dict) else 0,
        missing_feature_count=len(missing_features),
        defaulted_feature_count=len(defaulted_features),
        doctor_provided_feature_count=len(doctor_provided_features),
        source_ref_count=len(source_refs),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _snapshot_item_from_row(row: CaseModelInputSnapshot) -> ModelInputSnapshotItemV1:
    return ModelInputSnapshotItemV1(
        id=row.id,
        input_snapshot_id=row.input_snapshot_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        model_version_id=row.model_version_id,
        model_input_schema_id=row.model_input_schema_id,
        disease_task_feature_set_id=row.disease_task_feature_set_id,
        preprocess_artifact_ref=row.preprocess_artifact_ref,
        mapped_features=row.mapped_features_json or {},
        missing_features=list(row.missing_features_json or []),
        defaulted_features=list(row.defaulted_features_json or []),
        doctor_provided_features=list(row.doctor_provided_features_json or []),
        source_refs=list(row.source_refs_json or []),
        validation_status=row.validation_status,
        current_assessment_status=row.current_assessment_status,
        insufficient_data_for_assessment=bool(row.insufficient_data_for_assessment),
        runtime_stub=bool(row.runtime_stub),
        not_for_diagnosis=bool(row.not_for_diagnosis),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _ensure_json_compatible(value: Any, field_name: str) -> None:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'invalid_snapshot_payload', 'message': f'{field_name} must be JSON-compatible'},
        ) from exc


def _snapshot_model_version_row(db: Session, model_version_id: UUID) -> tuple[ModelRegistry, ModelVersion]:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == version.model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    return model, version


def _snapshot_list_response(route: str, items: list[ModelInputSnapshotSummaryItemV1], total: int, limit: int, offset: int) -> ModelInputSnapshotListResponseV1:
    return ModelInputSnapshotListResponseV1(route=route, items=items, total=total, limit=limit, offset=offset)


def _request_audit_id(request: Request) -> str | None:
    return request.headers.get('x-request-id') or request.headers.get('x-correlation-id')


def _snapshot_audit_metadata(snapshot: CaseModelInputSnapshot, *, reason: str | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        'model_input_schema_id': snapshot.model_input_schema_id,
        'disease_task_feature_set_id': snapshot.disease_task_feature_set_id,
        'validation_status': snapshot.validation_status,
        'current_assessment_status': snapshot.current_assessment_status,
        'insufficient_data_for_assessment': snapshot.insufficient_data_for_assessment,
        'runtime_stub': snapshot.runtime_stub,
        'not_for_diagnosis': snapshot.not_for_diagnosis,
        'mapped_feature_count': len(snapshot.mapped_features_json or {}),
        'missing_feature_count': len(snapshot.missing_features_json or []),
        'defaulted_feature_count': len(snapshot.defaulted_features_json or []),
        'doctor_provided_feature_count': len(snapshot.doctor_provided_features_json or []),
        'source_ref_count': len(snapshot.source_refs_json or []),
    }
    if reason:
        metadata['reason'] = reason
    return metadata


@router.post('/cases/{case_id}/model-input-snapshots', response_model=ModelInputSnapshotItemV1)
def create_model_input_snapshot(case_id: str, payload: ModelInputSnapshotCreateRequestV1, db: Session = Depends(get_db), actor: User = Depends(snapshot_write_guard)) -> ModelInputSnapshotItemV1:
    resolved_case_id, resolved_patient_id = _resolve_case(db, case_id)
    require_case_access(db, actor, resolved_case_id, access_level='detail')
    _snapshot_model_version_row(db, payload.model_version_id)
    schema_item = _schema_item(db, payload.model_version_id)
    if payload.model_input_schema_id.strip() != schema_item.model_input_schema_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_model_input_schema', 'message': 'model_input_schema_id does not match the selected model_version'})
    if payload.disease_task_feature_set_id.strip() != schema_item.disease_task_feature_set_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_disease_task_feature_set', 'message': 'disease_task_feature_set_id does not match the selected model_version'})

    snapshot_payloads = [
        ('mapped_features', payload.mapped_features),
        ('missing_features', payload.missing_features),
        ('defaulted_features', payload.defaulted_features),
        ('doctor_provided_features', payload.doctor_provided_features),
        ('source_refs', payload.source_refs),
    ]
    for field_name, value in snapshot_payloads:
        _ensure_json_compatible(value, field_name)

    snapshot = CaseModelInputSnapshot(
        input_snapshot_id=f'snap_{uuid4().hex[:16]}',
        case_id=resolved_case_id,
        patient_id=resolved_patient_id,
        trace_id=payload.trace_id.strip(),
        model_version_id=payload.model_version_id,
        model_input_schema_id=payload.model_input_schema_id.strip(),
        disease_task_feature_set_id=payload.disease_task_feature_set_id.strip(),
        preprocess_artifact_ref=payload.preprocess_artifact_ref.strip() if payload.preprocess_artifact_ref else None,
        mapped_features_json=dict(payload.mapped_features),
        missing_features_json=list(payload.missing_features),
        defaulted_features_json=list(payload.defaulted_features),
        doctor_provided_features_json=list(payload.doctor_provided_features),
        source_refs_json=list(payload.source_refs),
        validation_status=payload.validation_status,
        current_assessment_status=payload.current_assessment_status,
        insufficient_data_for_assessment=payload.insufficient_data_for_assessment,
        runtime_stub=True,
        not_for_diagnosis=True,
    )

    try:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
    except Exception:
        db.rollback()
        raise
    return _snapshot_item_from_row(snapshot)


@router.get('/model-input-snapshots/{input_snapshot_id}', response_model=ModelInputSnapshotItemV1)
def get_model_input_snapshot(input_snapshot_id: str, request: Request, db: Session = Depends(get_db), actor: User = Depends(snapshot_read_guard)) -> ModelInputSnapshotItemV1:
    row = db.execute(select(CaseModelInputSnapshot).where(CaseModelInputSnapshot.input_snapshot_id == input_snapshot_id)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'input_snapshot_not_found', 'message': 'Input snapshot not found'})
    try:
        require_snapshot_access(db, actor, row, mode='detail')
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            emit_access_audit_event(
                db,
                actor_user=actor,
                access_mode='detail',
                resource_type='model_input_snapshot',
                resource_id=row.input_snapshot_id,
                decision='denied',
                case_id=row.case_id,
                patient_id=row.patient_id,
                trace_id=row.trace_id,
                denial_reason=_http_detail_code(exc),
                policy_source='denied_no_policy',
                request_id=_request_audit_id(request),
                route_path=str(request.url.path),
                method=request.method,
                metadata=_snapshot_audit_metadata(row, reason='access_denied'),
            )
        raise
    response = _snapshot_item_from_row(row)
    try:
        policy_source = resolve_case_access_policy_source(db, actor, row.case_id, access_level='detail')
    except HTTPException:
        policy_source = 'unknown_policy'
    emit_access_audit_event(
        db,
        actor_user=actor,
        access_mode='detail',
        resource_type='model_input_snapshot',
        resource_id=row.input_snapshot_id,
        decision='allowed',
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        policy_source=policy_source,
        request_id=_request_audit_id(request),
        route_path=str(request.url.path),
        method=request.method,
        metadata=_snapshot_audit_metadata(row),
    )
    return response


@router.get('/cases/{case_id}/model-input-snapshots', response_model=ModelInputSnapshotListResponseV1)
def list_case_model_input_snapshots(case_id: str, limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), model_version_id: UUID | None = Query(default=None), db: Session = Depends(get_db), actor: User = Depends(snapshot_read_guard)) -> ModelInputSnapshotListResponseV1:
    resolved_case_id, _ = _resolve_case(db, case_id)
    require_case_access(db, actor, resolved_case_id, access_level='summary')
    filters = [CaseModelInputSnapshot.case_id == resolved_case_id]
    if model_version_id is not None:
        filters.append(CaseModelInputSnapshot.model_version_id == model_version_id)
    total = db.execute(select(func.count()).select_from(CaseModelInputSnapshot).where(*filters)).scalar_one()
    rows = db.execute(
        select(CaseModelInputSnapshot)
        .where(*filters)
        .order_by(CaseModelInputSnapshot.created_at.desc(), CaseModelInputSnapshot.id.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    items = [_snapshot_summary_item_from_row(row) for row in rows]
    return _snapshot_list_response(f'/api/v1/cases/{case_id}/model-input-snapshots', items, total, limit, offset)


@router.get('/traces/{trace_id}/model-input-snapshots', response_model=ModelInputSnapshotListResponseV1)
def list_trace_model_input_snapshots(trace_id: str, limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), model_version_id: UUID | None = Query(default=None), db: Session = Depends(get_db), actor: User = Depends(snapshot_read_guard)) -> ModelInputSnapshotListResponseV1:
    filters = [CaseModelInputSnapshot.trace_id == trace_id]
    if model_version_id is not None:
        filters.append(CaseModelInputSnapshot.model_version_id == model_version_id)
    total = db.execute(select(func.count()).select_from(CaseModelInputSnapshot).where(*filters)).scalar_one()
    rows = db.execute(
        select(CaseModelInputSnapshot)
        .where(*filters)
        .order_by(CaseModelInputSnapshot.created_at.desc(), CaseModelInputSnapshot.id.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    for case_uuid in {row.case_id for row in rows}:
        require_case_access(db, actor, case_uuid, access_level='summary')
    items = [_snapshot_summary_item_from_row(row) for row in rows]
    return _snapshot_list_response(f'/api/v1/traces/{trace_id}/model-input-snapshots', items, total, limit, offset)
