#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

MODEL_NAME = "multimodal_resnet18_cap_cop_classifier"
ADAPTER_CODE = "multimodal_resnet18_cap_cop_adapter"
DEFAULT_MODEL_VERSION_ID = "cap_cop_classifier_agent_v1.0.0_multimodal_resnet18"
WEIGHT_PATH = Path(
    "/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/"
    "multimodal_resnet18_bigdata/weights/fold1_best.pth"
)
EXPECTED_WEIGHT_SHA256 = "f17a4ed6f1f2f4b5e5c0d793a536b4b6e73d154ad2f5578fd844ae041967c809"
FEATURE_SCHEMA_PATH = Path(
    "/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/"
    "multimodal_resnet18_bigdata/feature_schema.json"
)
CLINICAL_PREPROCESS_ARTIFACT_PATH = Path(
    "/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/"
    "multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json"
)
LABEL_MAPPING = {"CAP": 0, "COP": 1}
EXPECTED_MODALITY_SCOPE = "ct_image+clinical_table"
EXPECTED_SHAPE = (96, 96, 96)
EXPECTED_SOURCE_TYPE = "synthetic"
SOURCE_FORMAT_DICOM_SERIES = "dicom_series"
PREPROCESSED_FORMAT_NIFTI_NII_GZ = "nifti_nii_gz"
PREPROCESSING_SCRIPT_NAME = "dcmtonii_N4.py"
CONVERSION_TOOL_NAME = "dcm2niix"
BIAS_CORRECTION_NAME = "N4BiasFieldCorrection"
MODEL_INPUT_FILE_NAME = "image.nii.gz"
LABEL_FILE_NAME = "label.nii.gz"


def _emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return exit_code


def _failed(code: str, message: str, *, trace_id: str | None = None, case_id: str | None = None) -> int:
    payload: dict[str, Any] = {
        "status": "failed",
        "error_code": code,
        "error_message": message,
        "not_for_diagnosis": True,
    }
    if trace_id:
        payload["trace_id"] = trace_id
    if case_id:
        payload["case_id"] = case_id
    return _emit(payload, exit_code=1)


def _disabled_payload(trace_id: str | None = None, case_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "disabled",
        "prototype_state": "prototype_not_executed",
        "error": {
            "code": "multimodal_runner_not_enabled",
            "message": "multimodal ResNet18 runner prototype candidate is not enabled for live execution",
        },
        "limitations": [
            "not_for_diagnosis",
            "prototype_not_executed",
            "metadata_only",
            "shadow_only",
            "no_torch_load",
            "no_real_forward",
        ],
        "model_name": MODEL_NAME,
        "adapter_code": ADAPTER_CODE,
        "model_version_id": DEFAULT_MODEL_VERSION_ID,
        "label_mapping": LABEL_MAPPING,
        "artifact_uri": str(WEIGHT_PATH),
        "artifact_hash_expected": EXPECTED_WEIGHT_SHA256,
    }
    if trace_id:
        payload["trace_id"] = trace_id
    if case_id:
        payload["case_id"] = case_id
    return payload


def _read_input(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_json:
        path = Path(args.input_json)
        if not path.exists():
            raise RuntimeError("invalid_json: input file not found")
        text = path.read_text(encoding="utf-8-sig")
    else:
        if sys.stdin.isatty():
            raise RuntimeError("invalid_json: no stdin payload provided")
        text = sys.stdin.read()
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
    if not text.strip():
        raise RuntimeError("invalid_json: empty JSON input")
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise RuntimeError("invalid_json: top-level payload must be a JSON object")
    return parsed


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    text = "" if value is None else str(value).strip()
    if not text:
        raise RuntimeError(f"missing_required_input: {key}")
    return text


def _compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"artifact_missing: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"invalid_artifact: {path}")
    return obj

def _normalize_contract_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _looks_like_preprocessed_nifti(path: Path) -> bool:
    lowered = str(path).lower()
    return lowered.endswith(".nii") or lowered.endswith(".nii.gz")


def _load_clinical_artifact() -> tuple[list[str], dict[str, float], dict[str, float], dict[str, Any]]:
    payload = _load_json(CLINICAL_PREPROCESS_ARTIFACT_PATH)
    feature_columns = payload.get("feature_columns")
    scaler = payload.get("standard_scaler", {})
    if not isinstance(feature_columns, list) or len(feature_columns) != 36:
        raise RuntimeError("clinical_artifact_invalid: feature_columns must contain 36 entries")
    if not isinstance(scaler, dict):
        raise RuntimeError("clinical_artifact_invalid: standard_scaler missing")
    mean = scaler.get("mean")
    scale = scaler.get("scale")
    if not isinstance(mean, dict) or not isinstance(scale, dict):
        raise RuntimeError("clinical_artifact_invalid: standard_scaler mean/scale missing")
    return [str(x) for x in feature_columns], {str(k): float(v) for k, v in mean.items()}, {str(k): float(v) for k, v in scale.items()}, payload


def _parse_clinical_features(payload: dict[str, Any], feature_order: list[str]) -> dict[str, float]:
    raw = payload.get("clinical_features")
    if raw is None:
        raise RuntimeError("clinical_input_insufficient: clinical_features missing")
    if isinstance(raw, list):
        if len(raw) != len(feature_order):
            raise RuntimeError("clinical_input_insufficient: feature count mismatch")
        out: dict[str, float] = {}
        for idx, name in enumerate(feature_order):
            value = raw[idx]
            if value is None:
                raise RuntimeError(f"clinical_input_insufficient: missing feature {name}")
            try:
                out[name] = float(value)
            except Exception as exc:
                raise RuntimeError(f"clinical_input_invalid: feature {name} not numeric") from exc
        return out
    if not isinstance(raw, dict):
        raise RuntimeError("clinical_input_invalid: clinical_features must be list or dict")
    keys = list(raw.keys())
    if set(keys) != set(feature_order):
        missing = [f for f in feature_order if f not in raw]
        extra = [k for k in keys if k not in feature_order]
        if missing:
            raise RuntimeError(f"clinical_input_insufficient: missing features {missing}")
        raise RuntimeError(f"clinical_input_invalid: unexpected features {extra}")
    ordered: dict[str, float] = {}
    for name in feature_order:
        value = raw[name]
        if value is None:
            raise RuntimeError(f"clinical_input_insufficient: missing feature {name}")
        try:
            ordered[name] = float(value)
        except Exception as exc:
            raise RuntimeError(f"clinical_input_invalid: feature {name} not numeric") from exc
    return ordered


def _normalize_state_dict(sd: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in sd.items():
        if key.startswith("module."):
            key = key[len("module.") :]
        normalized[key] = value
    return normalized


def _load_torch_stack():
    try:
        import torch  # type: ignore
        import torch.nn as nn  # type: ignore
        import torch.nn.functional as F  # type: ignore
        import nibabel as nib  # type: ignore
        import numpy as np  # type: ignore
        import monai  # type: ignore
        import torchvision  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"dependency_unavailable: {exc}") from exc
    return torch, nn, F, nib, np, monai, torchvision


def _build_model(torch_module: Any, nn_module: Any, monai_module: Any) -> Any:
    class AttentionFusion(nn_module.Module):
        def __init__(self, dim_img: int = 32, dim_clin: int = 32) -> None:
            super().__init__()
            self.attn = nn_module.Sequential(
                nn_module.Linear(dim_img + dim_clin, 16),
                nn_module.ReLU(),
                nn_module.Linear(16, 2),
                nn_module.Softmax(dim=1),
            )

        def forward(self, img_feat: Any, clin_feat: Any) -> Any:
            fused_input = torch_module.cat([img_feat, clin_feat], dim=1)
            weights = self.attn(fused_input)
            w_img = weights[:, 0].unsqueeze(1)
            w_clin = weights[:, 1].unsqueeze(1)
            return w_img * img_feat + w_clin * clin_feat

    class MultiModalResNet18(nn_module.Module):
        def __init__(self, in_channels_img: int = 1, n_clinical: int = 36, n_classes: int = 2) -> None:
            super().__init__()
            self.img_model = monai_module.networks.nets.ResNet(
                block="basic",
                layers=[2, 2, 2, 2],
                block_inplanes=[64, 128, 256, 512],
                spatial_dims=3,
                n_input_channels=in_channels_img,
                num_classes=32,
            )
            self.img_dropout = nn_module.Sequential(
                nn_module.Linear(32, 32),
                nn_module.ReLU(),
                nn_module.Dropout(0.3),
            )
            self.clinical_fc = nn_module.Sequential(
                nn_module.Linear(n_clinical, 32),
                nn_module.ReLU(),
                nn_module.Dropout(0.3),
                nn_module.Linear(32, 32),
                nn_module.ReLU(),
            )
            self.fusion = AttentionFusion(32, 32)
            self.classifier = nn_module.Sequential(
                nn_module.Linear(32, 16),
                nn_module.ReLU(),
                nn_module.Linear(16, n_classes),
            )

        def forward(self, img: Any, clinical: Any) -> Any:
            img_feat = self.img_model(img)
            img_feat = self.img_dropout(img_feat)
            clin_feat = self.clinical_fc(clinical)
            fused = self.fusion(img_feat, clin_feat)
            return self.classifier(fused)

    return MultiModalResNet18()


def _prepare_image(
    payload: dict[str, Any],
    torch_module: Any,
    nib_module: Any,
    np_module: Any,
    F_module: Any,
) -> tuple[Any, dict[str, Any]]:
    source_type = str(payload.get("source_type") or "").strip().lower()
    if source_type != EXPECTED_SOURCE_TYPE:
        raise RuntimeError("unsupported_source_type: expected synthetic")

    source_format = _normalize_contract_text(payload.get("source_format"))
    preprocessed_format = _normalize_contract_text(payload.get("preprocessed_format"))
    preprocessing_script = str(payload.get("preprocessing_script") or PREPROCESSING_SCRIPT_NAME).strip()
    conversion_tool = str(payload.get("conversion_tool") or CONVERSION_TOOL_NAME).strip()
    bias_correction = str(payload.get("bias_correction") or BIAS_CORRECTION_NAME).strip()
    model_input_file = str(payload.get("model_input_file") or MODEL_INPUT_FILE_NAME).strip()
    label_file = str(payload.get("label_file") or LABEL_FILE_NAME).strip()

    uri = payload.get("storage_uri") or payload.get("image_path")
    if not uri:
        raise RuntimeError("missing_required_input: storage_uri or image_path required")
    uri = str(uri).strip()
    if uri.startswith("file://"):
        uri = uri[7:]
    path = Path(uri)
    if path.exists() and path.is_dir():
        raise RuntimeError("imaging_input_not_preprocessed: DICOM directory requires dcmtonii_N4 preprocessing")
    if source_format == SOURCE_FORMAT_DICOM_SERIES:
        raise RuntimeError("imaging_input_not_preprocessed: DICOM series requires dcmtonii_N4 preprocessing")
    if preprocessed_format and preprocessed_format not in {PREPROCESSED_FORMAT_NIFTI_NII_GZ, "synthetic_fixture"}:
        raise RuntimeError("imaging_input_not_preprocessed: expected preprocessed nifti_nii_gz or synthetic fixture")
    if not path.exists():
        raise RuntimeError(f"input_missing: {uri}")
    if not _looks_like_preprocessed_nifti(path):
        raise RuntimeError("imaging_input_not_preprocessed: expected preprocessed .nii or .nii.gz input")

    image = nib_module.load(str(path)).get_fdata().astype(np_module.float32)
    if image.ndim != 3:
        raise RuntimeError(f"unsupported_image_rank: expected 3D volume, got ndim={image.ndim}")

    mean = float(image.mean())
    std = float(image.std())
    if std > 1e-5:
        image = (image - mean) / std
        normalization_applied = True
    else:
        image = image - mean
        normalization_applied = False

    tensor = torch_module.as_tensor(image, dtype=torch_module.float32).unsqueeze(0).unsqueeze(0)
    tensor = F_module.interpolate(tensor, size=EXPECTED_SHAPE, mode="trilinear", align_corners=False)
    summary = {
        "source_type": source_type,
        "source_format": source_format or "unknown",
        "preprocessed_format": preprocessed_format or "unknown",
        "preprocessing_script": preprocessing_script,
        "conversion_tool": conversion_tool,
        "bias_correction": bias_correction,
        "model_input_file": model_input_file,
        "label_file": label_file,
        "input_origin": str(path),
        "raw_shape": list(image.shape),
        "preprocessed_shape": list(tensor.shape),
        "expected_shape": list(EXPECTED_SHAPE),
        "dtype": "float32",
        "channel_layout": "channel_first",
        "normalization": "z_score",
        "normalization_applied": normalization_applied,
        "resize": "trilinear_to_96x96x96",
        "batch_size": 1,
        "concurrency": 1,
        "cpu_only": True,
    }
    return tensor.contiguous(), summary


def _prepare_clinical(
    payload: dict[str, Any],
    feature_order: list[str],
    mean: dict[str, float],
    scale: dict[str, float],
) -> tuple[Any, dict[str, Any]]:
    feature_map = _parse_clinical_features(payload, feature_order)
    ordered = []
    for name in feature_order:
        value = feature_map[name]
        mean_val = float(mean.get(name, 0.0))
        scale_val = float(scale.get(name, 1.0))
        if scale_val == 0:
            ordered.append(float(value) - mean_val)
        else:
            ordered.append((float(value) - mean_val) / scale_val)
    import torch as _torch  # local import for type/runtime clarity

    tensor = _torch.tensor([ordered], dtype=_torch.float32)
    summary = {
        "feature_order_version": "clinical_tabular_standardization_v1",
        "feature_count": len(feature_order),
        "feature_order": feature_order,
        "preprocessing_artifact": str(CLINICAL_PREPROCESS_ARTIFACT_PATH),
        "standardization": "x_scaled = (x - mean) / scale",
        "input_shape": list(tensor.shape),
        "output_shape": list(tensor.shape),
        "missing_policy": "fail_fast_no_silent_fallback",
        "notebook_behavior": "pandas_read_csv_duplicate_mangling_preserved",
    }
    return tensor, summary


def _artifact_check(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"artifact_missing: {path}")
    actual_hash = _compute_sha256(path)
    return {
        "status": "artifact_preflight",
        "prototype_state": "prototype_not_executed",
        "model_name": MODEL_NAME,
        "adapter_code": ADAPTER_CODE,
        "model_version_id": DEFAULT_MODEL_VERSION_ID,
        "artifact_uri": str(path),
        "artifact_hash": actual_hash,
        "artifact_hash_expected": EXPECTED_WEIGHT_SHA256,
        "artifact_hash_match": actual_hash == EXPECTED_WEIGHT_SHA256,
        "file_size_bytes": path.stat().st_size,
        "limitations": [
            "not_for_diagnosis",
            "prototype_not_executed",
            "metadata_only",
            "shadow_only",
        ],
    }


def _real_forward(payload: dict[str, Any]) -> dict[str, Any]:
    torch_module, nn_module, F_module, nib_module, np_module, monai_module, torchvision_module = _load_torch_stack()
    torch_module.set_num_threads(1)
    try:
        torch_module.set_num_interop_threads(1)
    except Exception:
        pass

    if not WEIGHT_PATH.exists():
        raise RuntimeError(f"artifact_missing: {WEIGHT_PATH}")
    actual_hash = _compute_sha256(WEIGHT_PATH)
    if actual_hash != EXPECTED_WEIGHT_SHA256:
        raise RuntimeError("artifact_hash_mismatch: exact fold1 weight hash mismatch")

    feature_order, mean, scale, preprocess_payload = _load_clinical_artifact()
    clinical_tensor, clinical_summary = _prepare_clinical(payload, feature_order, mean, scale)
    image_tensor, image_summary = _prepare_image(payload, torch_module, nib_module, np_module, F_module)

    artifact_model = torch_module.load(str(WEIGHT_PATH), map_location="cpu")
    state_dict = artifact_model
    if isinstance(artifact_model, dict):
        state_dict = artifact_model.get("state_dict") or artifact_model.get("model_state_dict") or artifact_model
    if not isinstance(state_dict, dict):
        raise RuntimeError("torch_load_failed: unsupported artifact object type")
    state_dict = _normalize_state_dict(state_dict)

    model = _build_model(torch_module, nn_module, monai_module)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    with torch_module.no_grad():
        logits_tensor = model(image_tensor, clinical_tensor)
        if logits_tensor.ndim != 2 or logits_tensor.shape[-1] != 2:
            raise RuntimeError(f"invalid_output: expected [1,2], got {tuple(logits_tensor.shape)}")
        logits = [float(x) for x in logits_tensor.squeeze(0).detach().cpu().tolist()]

    exp_values = [math.exp(x - max(logits)) for x in logits]
    total = sum(exp_values)
    if total <= 0:
        raise RuntimeError("invalid_output: probability normalization failed")
    prob_cap = exp_values[0] / total
    prob_cop = exp_values[1] / total
    candidate_label = "CAP" if prob_cap >= prob_cop else "COP"
    confidence = max(prob_cap, prob_cop)
    uncertainty = 1.0 - confidence

    model_version_id = str(payload.get("model_version_id") or DEFAULT_MODEL_VERSION_ID).strip()

    return {
        "status": "success",
        "trace_id": str(payload.get("trace_id")),
        "case_id": str(payload.get("case_id")),
        "patient_id": payload.get("patient_id"),
        "input_asset_id": payload.get("input_asset_id"),
        "source_type": EXPECTED_SOURCE_TYPE,
        "model_name": MODEL_NAME,
        "adapter_code": ADAPTER_CODE,
        "model_version_id": model_version_id,
        "artifact_hash": actual_hash,
        "label_mapping": LABEL_MAPPING,
        "logits": [round(v, 6) for v in logits],
        "probabilities": {"CAP": round(prob_cap, 6), "COP": round(prob_cop, 6)},
        "candidate_label": candidate_label,
        "confidence": round(confidence, 6),
        "uncertainty": round(uncertainty, 6),
        "image_preprocessing_summary": image_summary,
        "clinical_preprocessing_summary": clinical_summary,
        "fusion_architecture": "AttentionFusion(dim_img=32, dim_clin=32)",
        "runtime_env": {
            "python_path": sys.executable,
            "torch_version": str(torch_module.__version__),
            "torchvision_version": str(torchvision_module.__version__),
            "monai_version": str(monai_module.__version__),
            "device": "cpu",
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
            "batch_size": 1,
            "concurrency": 1,
        },
        "limitations": [
            "not_for_diagnosis",
            "shadow_only",
            "real_inference=true",
            "CPU_only",
            "batch_size=1",
            "concurrency=1",
            "no_silent_fallback",
        ],
        "not_for_diagnosis": True,
        "shadow_only": True,
        "real_inference": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cap_cop_multimodal_resnet18_runner",
        description="Controlled CAP/COP multimodal ResNet18 runner prototype.",
    )
    parser.add_argument("--input-json", default=None, help="Read request JSON from a file instead of stdin.")
    parser.add_argument("--artifact-path", default=str(WEIGHT_PATH), help="Explicit artifact path to verify.")
    parser.add_argument("--check-artifact", action="store_true", help="Only compute and report artifact hash metadata.")
    args = parser.parse_args()

    if not args.check_artifact and not args.input_json and sys.stdin.isatty():
        parser.print_help()
        return 0

    if args.check_artifact:
        try:
            return _emit(_artifact_check(Path(args.artifact_path)))
        except RuntimeError as exc:
            message = str(exc)
            if message.startswith("artifact_missing:"):
                return _failed("artifact_missing", message.split(":", 1)[1].strip())
            return _failed("artifact_check_failed", message)

    try:
        payload = _read_input(args)
    except json.JSONDecodeError as exc:
        return _failed("invalid_json", exc.msg)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("invalid_json:"):
            return _failed("invalid_json", message.split(":", 1)[1].strip())
        return _failed("invalid_request", message)

    trace_id = str(payload.get("trace_id") or "").strip() or None
    case_id = str(payload.get("case_id") or "").strip() or None

    try:
        trace_id = _require_text(payload, "trace_id")
        case_id = _require_text(payload, "case_id")
        _require_text(payload, "not_for_diagnosis")
        _require_text(payload, "shadow_only")
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("missing_required_input:"):
            return _failed("missing_required_input", message.split(":", 1)[1].strip(), trace_id=trace_id, case_id=case_id)
        return _failed("invalid_request", message, trace_id=trace_id, case_id=case_id)

    if str(payload.get("not_for_diagnosis")).lower() not in {"true", "1", "yes"}:
        return _failed("missing_required_input", "not_for_diagnosis must be true", trace_id=trace_id, case_id=case_id)
    if str(payload.get("shadow_only")).lower() not in {"true", "1", "yes"}:
        return _failed("missing_required_input", "shadow_only must be true", trace_id=trace_id, case_id=case_id)

    if payload.get("enable_real_shadow") is not True:
        return _emit(_disabled_payload(trace_id=trace_id, case_id=case_id), exit_code=1)

    try:
        return _emit(_real_forward(payload))
    except RuntimeError as exc:
        message = str(exc)
        if ":" in message:
            code, detail = message.split(":", 1)
            return _failed(code.strip(), detail.strip(), trace_id=trace_id, case_id=case_id)
        return _failed("inference_failed", message, trace_id=trace_id, case_id=case_id)
    except Exception as exc:  # pragma: no cover
        return _failed("inference_failed", str(exc), trace_id=trace_id, case_id=case_id)


if __name__ == "__main__":
    raise SystemExit(main())
