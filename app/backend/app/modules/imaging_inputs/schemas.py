
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImagingInputCreateRequestV1(BaseModel):
    patient_id: UUID
    trace_id: str = Field(min_length=1)
    modality: Literal['CT', 'NIfTI', 'demo_image', 'synthetic_visual_sample']
    source_type: Literal['real_deidentified', 'synthetic', 'demo']
    storage_uri: str = Field(min_length=1)
    deidentified: Literal[True] = True
    not_for_diagnosis: Literal[True] = True
    provenance_json: dict[str, Any] = Field(default_factory=dict)
    quality_flags_json: dict[str, Any] = Field(default_factory=dict)


class ImagingInputSummaryItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_asset_id: str
    case_id: UUID
    patient_id: UUID
    trace_id: str
    modality: str
    source_type: str
    deidentified: bool = True
    not_for_diagnosis: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ImagingInputItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_asset_id: str
    case_id: UUID
    patient_id: UUID
    trace_id: str
    modality: str
    source_type: str
    storage_uri: str
    deidentified: bool = True
    not_for_diagnosis: bool = True
    provenance_json: dict[str, Any] = Field(default_factory=dict)
    quality_flags_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ImagingInputCreateResponseV1(BaseModel):
    status: str = 'created'
    route: str
    item: ImagingInputItemV1


class ImagingInputListResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    total: int
    limit: int
    offset: int
    items: list[ImagingInputSummaryItemV1] = Field(default_factory=list)


class ImagingInputDetailResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ImagingInputItemV1
