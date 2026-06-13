
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.model_input.schemas import ModelInputAssessmentItemV1


class ShadowInferenceOutputItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    output_id: str
    shadow_run_id: str
    trace_id: str
    case_id: UUID
    model_version_id: UUID
    prediction_raw_json: dict = Field(default_factory=dict)
    prediction_probability_json: dict = Field(default_factory=dict)
    candidate_label: str | None = None
    confidence_json: dict = Field(default_factory=dict)
    uncertainty_json: dict = Field(default_factory=dict)
    limitations_json: dict = Field(default_factory=dict)
    input_quality_flags_json: dict = Field(default_factory=dict)
    created_at: datetime | None = None


class ShadowInferenceRunItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shadow_run_id: str
    trace_id: str
    case_id: UUID
    patient_id: UUID
    model_version_id: UUID
    artifact_hash: str
    adapter_code: str
    model_input_schema_id: UUID | None = None
    input_snapshot_id: UUID | None = None
    status: str
    runtime_env_json: dict = Field(default_factory=dict)
    runtime_stub: bool = True
    not_for_diagnosis: bool = True
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShadowInferenceRunDetailItemV1(ShadowInferenceRunItemV1):
    outputs: list[ShadowInferenceOutputItemV1] = Field(default_factory=list)


class ShadowInferenceRunListResponseV1(BaseModel):
    items: list[ShadowInferenceRunItemV1] = Field(default_factory=list)
    total: int = 0


class ShadowInferenceRunDetailResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ShadowInferenceRunDetailItemV1


class ShadowInferenceOutputListResponseV1(BaseModel):
    items: list[ShadowInferenceOutputItemV1] = Field(default_factory=list)
    total: int = 0


class ShadowAuditWriteRequestV1(BaseModel):
    trace_id: str
    case_id: UUID
    model_version_id: UUID
    artifact_hash: str
    adapter_code: str
    status: str
    not_for_diagnosis: bool = True
    runtime_stub: bool = True
    patient_id: str | None = None
    model_input_schema_id: UUID | None = None
    input_snapshot_id: UUID | None = None
    runtime_env_json: dict = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail_json: dict = Field(default_factory=dict)
    output: dict | None = None
    idempotency_key: str | None = None


class RuntimeSafetyConfigItemV1(BaseModel):
    cpu_only: bool = True
    batch_size: int = 1
    max_concurrency: int = 1
    timeout_seconds: int = 10
    force_no_grad: bool = True
    force_eval_mode: bool = True
    disable_gpu: bool = True


class ShadowEligibilityGateItemV1(BaseModel):
    status: str
    eligible: bool = False
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    canonical_adapter_code: str | None = None
    runtime_adapter_code: str | None = None
    accepted_adapter_codes: list[str] = Field(default_factory=list)
    adapter_match: bool = False
    runtime_stub: bool = True
    not_for_diagnosis: bool = True
    runtime_safety_config: RuntimeSafetyConfigItemV1 = Field(default_factory=RuntimeSafetyConfigItemV1)


class ControlledShadowClinicalMlpRequestV1(BaseModel):
    trace_id: str
    model_version_id: UUID
    provided_features: dict[str, Any] = Field(default_factory=dict)
    available_modalities: list[str] = Field(default_factory=list)
    runtime_options_json: dict[str, Any] = Field(default_factory=dict)
    not_for_diagnosis: bool = True
    runtime_stub: bool = True
    idempotency_key: str | None = None


class ControlledShadowClinicalMlpResponseV1(BaseModel):
    status: str
    route: str
    execution_mode: str = 'controlled_shadow_stub'
    shadow_disabled: bool = False
    validation: ModelInputAssessmentItemV1
    eligibility: ShadowEligibilityGateItemV1 = Field(default_factory=ShadowEligibilityGateItemV1)
    runtime_safety_config: RuntimeSafetyConfigItemV1 = Field(default_factory=RuntimeSafetyConfigItemV1)
    item: ShadowInferenceRunDetailItemV1
    limitations: list[str] = Field(default_factory=list)

class ControlledShadowClinicalMlpFold5OneShotRequestV1(BaseModel):
    input_snapshot_id: str = Field(min_length=1)
    trace_id: str | None = None
    dry_run_label: str | None = None


class ControlledShadowClinicalMlpFold5OneShotResponseV1(BaseModel):
    status: str
    route: str
    execution_mode: str = 'one_shot_fold5'
    shadow_run_id: str
    case_id: UUID
    patient_id: UUID
    trace_id: str
    model_version_id: UUID
    input_snapshot_id: str
    not_for_diagnosis: bool = True
    runtime_stub: bool = True
    candidate_label: str | None = None
    prediction_probability_json: dict[str, Any] = Field(default_factory=dict)
    confidence_json: dict[str, Any] = Field(default_factory=dict)
    limitations_json: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None


class ControlledShadowImagingResNet18OneShotRequestV1(BaseModel):
    input_asset_id: str = Field(min_length=1)
    trace_id: str | None = None
    dry_run_label: str | None = None
    enable_real_shadow: bool = False
    not_for_diagnosis: Literal[True] = True
    runtime_stub: Literal[True] = True
    execution_mode: Literal['metadata_only_stub'] = 'metadata_only_stub'


class ControlledShadowImagingResNet18OneShotResponseV1(BaseModel):
    status: str
    route: str
    execution_mode: str = 'metadata_only_stub'
    case_id: UUID
    patient_id: UUID
    trace_id: str
    input_asset_id: str
    resource_type: str = 'case_imaging_input'
    model_family: str = 'imaging_resnet18'
    not_for_diagnosis: bool = True
    runtime_stub: bool = True
    shadow_run_id: str | None = None
    artifact_hash: str | None = None
    runner_state: str | None = None
    prototype_state: str | None = None
    candidate_label: str | None = None
    prediction_probability_json: dict[str, Any] = Field(default_factory=dict)
    confidence_json: dict[str, Any] = Field(default_factory=dict)
    uncertainty_json: dict[str, Any] = Field(default_factory=dict)
    limitations_json: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    limitations: list[str] = Field(default_factory=list)


class ControlledShadowMultimodalResNet18OneShotRequestV1(BaseModel):
    input_asset_id: str = Field(min_length=1)
    input_snapshot_id: str = Field(min_length=1)
    trace_id: str | None = None
    dry_run_label: str | None = None
    enable_real_shadow: bool = False
    not_for_diagnosis: Literal[True] = True
    runtime_stub: Literal[True] = True
    execution_mode: Literal['metadata_only_stub'] = 'metadata_only_stub'


class ControlledShadowMultimodalResNet18OneShotResponseV1(BaseModel):
    status: str
    route: str
    execution_mode: str = 'metadata_only_stub'
    shadow_disabled: bool = False
    case_id: UUID
    patient_id: UUID
    trace_id: str
    input_asset_id: str
    input_snapshot_id: str
    resource_type: str = 'case_multimodal_input'
    model_family: str = 'multimodal_resnet18'
    not_for_diagnosis: bool = True
    runtime_stub: bool = True
    shadow_run_id: str | None = None
    artifact_hash: str | None = None
    runner_state: str | None = None
    prototype_state: str | None = None
    candidate_label: str | None = None
    prediction_probability_json: dict[str, Any] = Field(default_factory=dict)
    confidence_json: dict[str, Any] = Field(default_factory=dict)
    uncertainty_json: dict[str, Any] = Field(default_factory=dict)
    limitations_json: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    limitations: list[str] = Field(default_factory=list)


class CapCopShadowWorkflowBranchReadinessItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    branch_name: Literal['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18']
    status: Literal['ready', 'blocked', 'schema_unverified', 'preprocessing_required', 'unavailable']
    can_run: bool = False
    disabled_reasons: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    detected_inputs: dict[str, Any] = Field(default_factory=dict)
    next_action: str


class CapCopShadowWorkflowReadinessResponseV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = 'ok'
    route: str
    overall_status: Literal['ready_partial', 'ready_all', 'blocked']
    case_id: UUID
    patient_id: UUID | None = None
    branches: dict[str, CapCopShadowWorkflowBranchReadinessItemV1] = Field(default_factory=dict)
    checked_at: datetime | None = None
    limitations: list[str] = Field(default_factory=list)


class CapCopShadowWorkflowRequestV1(BaseModel):
    mode: Literal['preview', 'execute']
    requested_branches: list[Literal['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18']] = Field(default_factory=list)
    dry_run_label: str | None = None
    not_for_diagnosis: Literal[True] = True
    shadow_only: Literal[True] = True


class CapCopShadowWorkflowBranchExecutionItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    branch: Literal['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18']
    status: Literal['planned', 'executed', 'skipped', 'failed']
    shadow_run_id: str | None = None
    output_id: str | None = None
    candidate_label: str | None = None
    probabilities: dict[str, Any] = Field(default_factory=dict)
    disabled_reasons: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CapCopShadowWorkflowRunResponseV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = 'ok'
    route: str
    workflow_run_id: str
    mode: Literal['preview', 'execute']
    overall_status: Literal['ready_partial', 'ready_all', 'blocked']
    case_id: UUID
    patient_id: UUID
    branches: list[CapCopShadowWorkflowBranchExecutionItemV1] = Field(default_factory=list)
    checked_at: datetime | None = None
    limitations: list[str] = Field(default_factory=list)
