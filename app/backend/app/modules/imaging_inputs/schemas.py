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


class DicomSeriesImagingInputCreateRequestV1(BaseModel):
    patient_id: UUID
    trace_id: str = Field(min_length=1)
    modality: Literal['CT'] = 'CT'
    source_type: Literal['real_deidentified', 'synthetic', 'demo'] = 'real_deidentified'
    storage_uri: str = Field(min_length=1)
    deidentified: Literal[True] = True
    not_for_diagnosis: Literal[True] = True
    source_format: Literal['dicom_series'] = 'dicom_series'
    preprocessed_format: Literal['nifti_nii_gz'] = 'nifti_nii_gz'
    preprocessing_script: str = 'dcmtonii_N4.py'
    conversion_tool: str = 'dcm2niix'
    bias_correction: str = 'N4BiasFieldCorrection'
    raw_output_file: str = 'raw_image.nii.gz'
    model_input_file: str = 'image.nii.gz'
    label_file: str = 'label.nii.gz'
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


class ImagingInputPreprocessingStatusItemV1(BaseModel):
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
    source_format: str
    preprocessed_format: str
    preprocessing_script: str
    conversion_tool: str
    bias_correction: str
    raw_output_file: str
    model_input_file: str
    label_file: str
    preprocessing_status: str
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


class ImagingInputPreprocessingStatusResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ImagingInputPreprocessingStatusItemV1


class ImagingPreprocessResponseV1(BaseModel):
    status: str = 'not_implemented'
    route: str
    error_code: str = 'preprocessing_not_implemented'
    message: str
    item: ImagingInputPreprocessingStatusItemV1
    limitations: list[str] = Field(default_factory=list)
