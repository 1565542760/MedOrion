from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiseaseTaskFeatureSetItemV1(BaseModel):
    feature_set_id: str
    feature_set_key: str
    feature_set_name: str
    disease_task_code: str
    schema_version: str = 'v1'
    description: str | None = None


class ModelFeatureRequirementItemV1(BaseModel):
    feature_order: int
    source_clinical_field: str
    model_feature_name: str
    feature_type: str
    required: bool = False
    optional: bool = True
    defaultable: bool = False
    default_strategy: str | None = None
    missing_value_policy: str | None = None
    unit: str | None = None
    value_range: dict | list | str | None = None
    enum_mapping: dict | list | str | None = None
    notes: str | None = None


class ModelInputSchemaItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_version_id: UUID
    model_id: UUID
    model_name: str
    version_label: str
    model_input_schema_id: str
    model_input_schema_key: str
    model_input_schema_name: str
    schema_version: str
    disease_task: str
    disease_task_feature_set_id: str
    disease_task_feature_set_key: str
    disease_task_feature_set_name: str
    supported_disease_tasks: list[str] = Field(default_factory=list)
    supported_modalities: list[str] = Field(default_factory=list)
    lifecycle_status: str
    model_family: str | None = None
    preprocess_artifact_ref: str | None = None
    feature_count: int = 0
    feature_requirements: list[ModelFeatureRequirementItemV1] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    runtime_stub: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelFeatureRequirementsResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    model_version_id: UUID
    model_input_schema_id: str
    model_input_schema_key: str
    disease_task_feature_set_id: str
    disease_task_feature_set_key: str
    feature_count: int
    required_count: int
    optional_count: int
    defaultable_count: int
    feature_requirements: list[ModelFeatureRequirementItemV1] = Field(default_factory=list)
    runtime_stub: bool = True
    limitations: list[str] = Field(default_factory=list)


class ModelInputPreviewRequestV1(BaseModel):
    model_version_id: UUID
    disease_task: str
    provided_features: dict[str, Any] = Field(default_factory=dict)


class ModelInputValidationRequestV1(BaseModel):
    model_version_id: UUID
    disease_task: str
    provided_features: dict[str, Any] = Field(default_factory=dict)


class ModelMissingRequiredFeatureItemV1(BaseModel):
    model_feature_name: str
    source_clinical_field: str
    why_required: str | None = None
    default_strategy: str | None = None
    missing_value_policy: str | None = None
    suggested_doctor_question: str | None = None


class ModelInputAssessmentItemV1(BaseModel):
    model_version_id: UUID
    model_input_schema_id: str
    model_input_schema_key: str
    disease_task_feature_set_id: str
    disease_task_feature_set_key: str
    disease_task: str
    mapped_features: dict[str, Any] = Field(default_factory=dict)
    missing_features: list[str] = Field(default_factory=list)
    missing_required_features: list[str] = Field(default_factory=list)
    missing_required_details: list[ModelMissingRequiredFeatureItemV1] = Field(default_factory=list)
    defaultable_features: list[str] = Field(default_factory=list)
    suggested_doctor_questions: list[str] = Field(default_factory=list)
    current_assessment_status: str
    insufficient_data_for_assessment: bool = False
    default_strategy_available: bool = False
    requires_doctor_confirmation: bool = False
    feature_count: int = 0
    mapped_feature_count: int = 0
    runtime_stub: bool = True
    limitations: list[str] = Field(default_factory=list)


class ModelInputPreviewResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ModelInputAssessmentItemV1


class ModelInputValidationResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ModelInputAssessmentItemV1


class ModelSelectionCandidateItemV1(BaseModel):
    model_version_id: UUID
    model_id: UUID
    model_name: str
    version_label: str
    model_input_schema_id: str
    model_input_schema_key: str
    lifecycle_status: str
    supported_modalities: list[str] = Field(default_factory=list)
    feature_completeness: float = 0.0
    missing_fields: list[str] = Field(default_factory=list)
    missing_required_features: list[str] = Field(default_factory=list)
    defaultable_features: list[str] = Field(default_factory=list)
    suitability_reason: str
    current_assessment_status: str
    insufficient_data_for_assessment: bool = False
    runtime_stub: bool = True


class ModelSelectionPreviewRequestV1(BaseModel):
    disease_task: str
    available_modalities: list[str] = Field(default_factory=list)
    provided_features: dict[str, Any] = Field(default_factory=dict)


class ModelSelectionPreviewResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    disease_task: str
    selection_required: bool
    selection_reason: str
    candidate_count: int = 0
    selected_candidate: ModelSelectionCandidateItemV1 | None = None
    validation: ModelInputAssessmentItemV1 | None = None
    candidates: list[ModelSelectionCandidateItemV1] = Field(default_factory=list)
    runtime_stub: bool = True
    limitations: list[str] = Field(default_factory=list)


class ModelInputSnapshotCreateRequestV1(BaseModel):
    trace_id: str = Field(min_length=1)
    model_version_id: UUID
    model_input_schema_id: str = Field(min_length=1)
    disease_task_feature_set_id: str = Field(min_length=1)
    preprocess_artifact_ref: str | None = None
    mapped_features: dict[str, Any] = Field(default_factory=dict)
    missing_features: list[Any] = Field(default_factory=list)
    defaulted_features: list[Any] = Field(default_factory=list)
    doctor_provided_features: list[Any] = Field(default_factory=list)
    source_refs: list[Any] = Field(default_factory=list)
    validation_status: Literal['ready_for_inference', 'insufficient_data_for_assessment', 'missing_required_features', 'default_applied', 'doctor_confirmation_required', 'validation_failed']
    current_assessment_status: Literal['ready_for_inference', 'insufficient_data_for_assessment', 'missing_required_features', 'default_applied', 'doctor_confirmation_required', 'validation_failed']
    insufficient_data_for_assessment: bool = False
    runtime_stub: Literal[True] = True
    not_for_diagnosis: Literal[True] = True


class ModelInputSnapshotSummaryItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_snapshot_id: str
    case_id: UUID
    patient_id: UUID
    trace_id: str
    model_version_id: UUID
    model_input_schema_id: str
    disease_task_feature_set_id: str
    validation_status: str
    current_assessment_status: str
    insufficient_data_for_assessment: bool = False
    runtime_stub: bool = True
    not_for_diagnosis: bool = True
    mapped_feature_count: int = 0
    missing_feature_count: int = 0
    defaulted_feature_count: int = 0
    doctor_provided_feature_count: int = 0
    source_ref_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelInputSnapshotItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_snapshot_id: str
    case_id: UUID
    patient_id: UUID
    trace_id: str
    model_version_id: UUID
    model_input_schema_id: str
    disease_task_feature_set_id: str
    preprocess_artifact_ref: str | None = None
    mapped_features: dict[str, Any] = Field(default_factory=dict)
    missing_features: list[Any] = Field(default_factory=list)
    defaulted_features: list[Any] = Field(default_factory=list)
    doctor_provided_features: list[Any] = Field(default_factory=list)
    source_refs: list[Any] = Field(default_factory=list)
    validation_status: str
    current_assessment_status: str
    insufficient_data_for_assessment: bool = False
    runtime_stub: bool = True
    not_for_diagnosis: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelInputSnapshotListResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    total: int
    limit: int
    offset: int
    items: list[ModelInputSnapshotSummaryItemV1] = Field(default_factory=list)


class ClinicalTableStrictValidationRequestV1(BaseModel):
    model_config = ConfigDict(extra='forbid')

    raw_columns: list[str] = Field(default_factory=list, min_length=1)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    sample_row: dict[str, Any] = Field(default_factory=dict)
    source_type: Literal['csv_paste', 'csv_upload_metadata', 'manual_entry']
    not_for_diagnosis: bool = True
    shadow_only: bool = True


class ClinicalTableStrictFeatureMappingItemV1(BaseModel):
    feature_order: int
    model_feature_name: str
    source_clinical_field: str
    required: bool = True
    present: bool = False
    raw_column: str | None = None
    mapping_status: Literal['matched', 'missing', 'type_error']
    feature_type: str
    unit: str | None = None
    coercion_status: Literal['ok', 'missing', 'type_error']
    sample_value: Any | None = None
    coerced_value: Any | None = None
    message: str | None = None


class ClinicalTableStrictTypeCoercionItemV1(BaseModel):
    feature_order: int
    model_feature_name: str
    feature_type: str
    row_count: int
    coercion_status: Literal['ok', 'missing', 'type_error']
    sample_value: Any | None = None
    coerced_value: Any | None = None
    first_error_row_index: int | None = None
    message: str | None = None


class ClinicalTableStrictValidationResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    artifact_id: str
    artifact_ref: str
    artifact_feature_count: int
    artifact_feature_order: list[str] = Field(default_factory=list)
    feature_mappings: list[ClinicalTableStrictFeatureMappingItemV1] = Field(default_factory=list)
    type_coercion_results: list[ClinicalTableStrictTypeCoercionItemV1] = Field(default_factory=list)
    missing_required_features: list[str] = Field(default_factory=list)
    extra_raw_columns: list[str] = Field(default_factory=list)
    validation_status: Literal['ready_for_inference', 'schema_unverified', 'insufficient_data_for_assessment']
    can_create_snapshot: bool = False
    order_matches_artifact: bool = False
    failure_reasons: list[str] = Field(default_factory=list)
    source_type: str
    row_count: int = 0
    not_for_diagnosis: bool = True
    shadow_only: bool = True
    runtime_stub: bool = True
    limitations: list[str] = Field(default_factory=list)



class ClinicalTableControlledSnapshotCreateRequestV1(BaseModel):
    model_config = ConfigDict(extra='forbid')

    raw_columns: list[str] = Field(default_factory=list, min_length=1)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    sample_row: dict[str, Any] = Field(default_factory=dict)
    source_type: Literal['csv_paste', 'csv_upload_metadata', 'manual_entry']
    trace_id: str | None = None
    not_for_diagnosis: bool = True
    shadow_only: bool = True


class ClinicalTableControlledSnapshotCreateResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    artifact_id: str
    artifact_ref: str
    artifact_feature_count: int
    artifact_feature_order: list[str] = Field(default_factory=list)
    validation_status: Literal['ready_for_inference', 'schema_unverified', 'insufficient_data_for_assessment']
    can_create_snapshot: bool = False
    order_matches_artifact: bool = False
    failure_reasons: list[str] = Field(default_factory=list)
    source_type: str
    row_count: int = 0
    not_for_diagnosis: bool = True
    shadow_only: bool = True
    runtime_stub: bool = True
    snapshot_created: bool = False
    snapshot: ModelInputSnapshotItemV1 | None = None
    mapped_features: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[Any] = Field(default_factory=list)
    doctor_provided_features: list[Any] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

