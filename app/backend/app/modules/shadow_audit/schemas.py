from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ShadowInferenceOutputItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    output_id: str
    shadow_run_id: str
    trace_id: str
    case_id: str
    model_version_id: str
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

    id: str
    shadow_run_id: str
    trace_id: str
    case_id: str
    patient_id: str
    model_version_id: str
    artifact_hash: str
    adapter_code: str
    model_input_schema_id: str | None = None
    input_snapshot_id: str | None = None
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
