from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from fastapi import HTTPException, status

IMAGING_SOURCE_FORMAT_DICOM_SERIES = "dicom_series"
IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ = "nifti_nii_gz"
IMAGING_PREPROCESSING_SCRIPT = "dcmtonii_N4.py"
IMAGING_CONVERSION_TOOL = "dcm2niix"
IMAGING_BIAS_CORRECTION = "N4BiasFieldCorrection"
IMAGING_MODEL_INPUT_FILE = "image.nii.gz"
IMAGING_LABEL_FILE = "label.nii.gz"
IMAGING_REAL_SHADOW_ALLOWED_SOURCE_TYPES = {"synthetic"}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _looks_like_nifti_reference(storage_uri: str) -> bool:
    lowered = storage_uri.lower()
    return lowered.endswith(".nii") or lowered.endswith(".nii.gz")


def _looks_like_dicom_directory(storage_uri: str) -> bool:
    normalized = storage_uri.strip()
    if not normalized:
        return False
    if normalized.startswith("file://"):
        normalized = normalized[7:]
    lowered = normalized.lower()
    if lowered.endswith(("/", "\\")):
        return True
    path = Path(normalized)
    try:
        if path.exists() and path.is_dir():
            return True
    except OSError:
        pass
    if "dicom" in lowered and not _looks_like_nifti_reference(lowered):
        return True
    return False


def extract_imaging_input_contract(input_row: Any) -> dict[str, Any]:
    provenance = _as_mapping(getattr(input_row, "provenance_json", None))
    quality_flags = _as_mapping(getattr(input_row, "quality_flags_json", None))
    storage_uri = _normalize_text(getattr(input_row, "storage_uri", None))
    source_type = _normalize_text(getattr(input_row, "source_type", None)).lower()
    source_format = _normalize_text(provenance.get("source_format") or quality_flags.get("source_format")).lower()
    preprocessed_format = _normalize_text(provenance.get("preprocessed_format") or quality_flags.get("preprocessed_format")).lower()
    preprocessing_script = _normalize_text(provenance.get("preprocessing_script") or quality_flags.get("preprocessing_script"))
    conversion_tool = _normalize_text(provenance.get("conversion_tool") or quality_flags.get("conversion_tool"))
    bias_correction = _normalize_text(provenance.get("bias_correction") or quality_flags.get("bias_correction"))
    model_input_file = _normalize_text(provenance.get("model_input_file") or quality_flags.get("model_input_file")) or IMAGING_MODEL_INPUT_FILE
    label_file = _normalize_text(provenance.get("label_file") or quality_flags.get("label_file")) or IMAGING_LABEL_FILE
    return {
        "provenance_json": provenance,
        "quality_flags_json": quality_flags,
        "storage_uri": storage_uri,
        "source_type": source_type,
        "source_format": source_format,
        "preprocessed_format": preprocessed_format,
        "preprocessing_script": preprocessing_script,
        "conversion_tool": conversion_tool,
        "bias_correction": bias_correction,
        "model_input_file": model_input_file,
        "label_file": label_file,
    }


def require_preprocessed_imaging_reference(input_row: Any, *, allow_synthetic_only: bool = True) -> dict[str, Any]:
    contract = extract_imaging_input_contract(input_row)
    storage_uri = contract["storage_uri"]
    source_type = contract["source_type"]
    source_format = contract["source_format"]
    preprocessed_format = contract["preprocessed_format"]
    if allow_synthetic_only and source_type != "synthetic":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "unsupported_source_type",
                "message": "Only synthetic imaging inputs are allowed for this coursework bridge",
            },
        )
    if source_format == IMAGING_SOURCE_FORMAT_DICOM_SERIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "imaging_input_not_preprocessed",
                "message": "DICOM series must be preprocessed with dcmtonii_N4.py before shadow execution",
            },
        )
    if _looks_like_dicom_directory(storage_uri):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "imaging_input_not_preprocessed",
                "message": "DICOM directory storage_uri must be preprocessed into NIfTI before shadow execution",
            },
        )
    if preprocessed_format and preprocessed_format not in {
        IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
        "synthetic_fixture",
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "imaging_input_not_preprocessed",
                "message": "Real shadow execution requires a preprocessed NIfTI input or synthetic fixture",
            },
        )
    if storage_uri and not _looks_like_nifti_reference(storage_uri):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "imaging_input_not_preprocessed",
                "message": "Real shadow execution requires a preprocessed .nii or .nii.gz reference",
            },
        )
    return contract


def imaging_preprocessing_metadata(input_row: Any) -> dict[str, Any]:
    contract = extract_imaging_input_contract(input_row)
    return {
        "source_format": contract["source_format"] or "unknown",
        "preprocessed_format": contract["preprocessed_format"] or "unknown",
        "preprocessing_script": contract["preprocessing_script"] or IMAGING_PREPROCESSING_SCRIPT,
        "conversion_tool": contract["conversion_tool"] or IMAGING_CONVERSION_TOOL,
        "bias_correction": contract["bias_correction"] or IMAGING_BIAS_CORRECTION,
        "model_input_file": contract["model_input_file"],
        "label_file": contract["label_file"],
    }
