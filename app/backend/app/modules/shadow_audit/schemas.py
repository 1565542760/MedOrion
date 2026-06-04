
from __future__ import annotations

from datetime import datetime
from typing import Any
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
    item: ShadowInferenceRunDetailItemV1
    limitations: list[str] = Field(default_factory=list)
