from __future__ import annotations

from datetime import datetime
from typing import Any
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
