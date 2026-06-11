#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

MODEL_NAME = "imaging_resnet18_cap_cop_classifier"
ADAPTER_CODE = "imaging_resnet18_cap_cop_adapter"
MODEL_VERSION_ID = "cap_cop_classifier_agent_v1.0.0_imaging_resnet18"
WEIGHT_PATH = Path(
    "/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/"
    "imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth"
)
EXPECTED_WEIGHT_SHA256 = "892fd836b0f361ca6ed4d90f5a57c71587984c817cc3ba1e6d88618f6da9f781"
LABEL_MAPPING = {"CAP": 0, "COP": 1}
EXPECTED_MODALITY = "ct_image"
EXPECTED_SHAPE = (96, 96, 96)


def _emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return exit_code


def _disabled_payload(trace_id: str | None = None, case_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "disabled",
        "prototype_state": "prototype_not_executed",
        "error": {
            "code": "imaging_runner_not_loaded",
            "message": "imaging ResNet18 runner prototype candidate is not enabled for live execution",
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
        "model_version_id": MODEL_VERSION_ID,
        "label_mapping": LABEL_MAPPING,
        "artifact_uri": str(WEIGHT_PATH),
        "artifact_hash_expected": EXPECTED_WEIGHT_SHA256,
    }
    if trace_id:
        payload["trace_id"] = trace_id
    if case_id:
        payload["case_id"] = case_id
    return payload


def _failed(code: str, message: str, *, trace_id: str | None = None, case_id: str | None = None) -> int:
    payload = {
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


def _require_text(payload: dict[str, Any], key: str, *, allow_empty: bool = False) -> str:
    value = payload.get(key)
    text = "" if value is None else str(value).strip()
    if not text and not allow_empty:
        raise RuntimeError(f"missing_required_input: {key}")
    return text


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


def _validate_common_request(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    trace_id = _require_text(payload, "trace_id")
    case_id = _require_text(payload, "case_id")
    input_asset_id = _require_text(payload, "input_asset_id")
    storage_uri = _require_text(payload, "storage_uri")
    modality = _require_text(payload, "modality")
    if modality != EXPECTED_MODALITY:
        raise RuntimeError("unsupported_modality: expected ct_image")
    if payload.get("not_for_diagnosis") is not True:
        raise RuntimeError("missing_required_input: not_for_diagnosis must be true")
    if payload.get("deidentified") is not True and payload.get("source_type") != "synthetic":
        raise RuntimeError("missing_required_input: deidentified must be true for non-synthetic inputs")
    return trace_id, case_id, input_asset_id, storage_uri


def _compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_check(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"artifact_missing: {path}")
    actual_hash = _compute_sha256(path)
    return {
        "status": "artifact_preflight",
        "prototype_state": "prototype_not_executed",
        "model_name": MODEL_NAME,
        "adapter_code": ADAPTER_CODE,
        "model_version_id": MODEL_VERSION_ID,
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


def _load_torch_modules():
    try:
        import torch  # type: ignore
        import torch.nn as nn  # type: ignore
        import torch.nn.functional as F  # type: ignore
        import torchvision  # type: ignore
        import nibabel as nib  # type: ignore
        import numpy as np  # type: ignore
        import monai  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"dependency_unavailable: {exc}") from exc
    return torch, nn, F, nib, np, monai, torchvision


def _build_model(torch_module: Any, monai_module: Any, nn_module: Any) -> Any:
    class ImagingResNet18CapCop(nn_module.Module):
        def __init__(self) -> None:
            super().__init__()
            self.img_model = monai_module.networks.nets.ResNet(
                block="basic",
                layers=[2, 2, 2, 2],
                block_inplanes=[64, 128, 256, 512],
                spatial_dims=3,
                n_input_channels=1,
                num_classes=32,
            )
            self.img_dropout = nn_module.Sequential(
                nn_module.Linear(32, 32),
                nn_module.ReLU(),
                nn_module.Dropout(0.3),
            )
            self.classifier = nn_module.Sequential(
                nn_module.Linear(32, 16),
                nn_module.ReLU(),
                nn_module.Linear(16, 2),
            )

        def forward(self, x: Any) -> Any:
            x = self.img_model(x)
            x = self.img_dropout(x)
            return self.classifier(x)

    return ImagingResNet18CapCop()


def _prepare_input_tensor(
    payload: dict[str, Any],
    torch_module: Any,
    nib_module: Any,
    np_module: Any,
    F_module: Any,
) -> tuple[Any, dict[str, Any]]:
    source_type = str(payload.get("source_type") or "synthetic").strip().lower()
    storage_uri = str(payload.get("storage_uri") or "").strip()
    preprocessing_summary: dict[str, Any] = {
        "source_type": source_type,
        "expected_shape": list(EXPECTED_SHAPE),
        "resize": "trilinear_to_96x96x96",
        "normalization": "z_score",
        "dtype": "float32",
        "channel_layout": "channel_first",
        "batch_size": 1,
        "concurrency": 1,
        "cpu_only": True,
    }

    if source_type == "synthetic":
        seed_value = payload.get("synthetic_seed")
        if seed_value is None:
            seed_value = int(hashlib.sha256(payload["trace_id"].encode("utf-8")).hexdigest()[:8], 16)
        fixture_uri = storage_uri
        fixture_path = Path(fixture_uri[7:] if fixture_uri.startswith("file://") else fixture_uri)
        if fixture_path.exists() and (fixture_path.suffix == ".nii" or str(fixture_path).endswith(".nii.gz")):
            volume = nib_module.load(str(fixture_path)).get_fdata().astype(np_module.float32)
            preprocessing_summary["input_origin"] = f"synthetic_nifti_fixture:{fixture_path}"
        else:
            rng = np_module.random.default_rng(int(seed_value))
            volume = rng.standard_normal(EXPECTED_SHAPE, dtype=np_module.float32)
            preprocessing_summary["input_origin"] = "synthetic_fixture"
    else:
        uri = storage_uri
        if uri.startswith("file://"):
            uri = uri[7:]
        path = Path(uri)
        if not path.exists():
            raise RuntimeError(f"input_missing: {uri}")
        if path.suffix not in {".nii", ".gz"} and not str(path).endswith(".nii.gz"):
            raise RuntimeError("unsupported_image_format: expected .nii or .nii.gz")
        volume = nib_module.load(str(path)).get_fdata().astype(np_module.float32)
        preprocessing_summary["input_origin"] = str(path)

    if volume.ndim == 4 and volume.shape[-1] == 1:
        volume = volume[..., 0]
    if volume.ndim != 3:
        raise RuntimeError(f"unsupported_image_rank: expected 3D volume, got ndim={volume.ndim}")

    mean = float(volume.mean())
    std = float(volume.std())
    if std > 1e-5:
        volume = (volume - mean) / std
        normalization_applied = True
    else:
        volume = volume - mean
        normalization_applied = False

    tensor = torch_module.as_tensor(volume, dtype=torch_module.float32).unsqueeze(0).unsqueeze(0)
    tensor = F_module.interpolate(tensor, size=EXPECTED_SHAPE, mode="trilinear", align_corners=False)
    preprocessing_summary["raw_shape"] = list(volume.shape)
    preprocessing_summary["preprocessed_shape"] = list(tensor.shape)
    preprocessing_summary["normalization_applied"] = normalization_applied
    return tensor.contiguous(), preprocessing_summary


def _run_real_shadow(payload: dict[str, Any]) -> dict[str, Any]:
    import torch as _torch  # type: ignore

    _torch.set_num_threads(1)
    try:
        _torch.set_num_interop_threads(1)
    except Exception:
        pass

    torch_module, nn_module, F_module, nib_module, np_module, monai_module, torchvision_module = _load_torch_modules()
    if not WEIGHT_PATH.exists():
        raise RuntimeError(f"artifact_missing: {WEIGHT_PATH}")
    actual_hash = _compute_sha256(WEIGHT_PATH)
    if actual_hash != EXPECTED_WEIGHT_SHA256:
        raise RuntimeError("artifact_hash_mismatch: exact fold5 weight hash mismatch")

    artifact_obj = torch_module.load(str(WEIGHT_PATH), map_location="cpu")
    state_dict = artifact_obj
    if isinstance(artifact_obj, dict):
        state_dict = artifact_obj.get("state_dict") or artifact_obj.get("model_state_dict") or artifact_obj
    if not isinstance(state_dict, dict):
        raise RuntimeError("torch_load_failed: unsupported artifact object type")

    model = _build_model(torch_module, monai_module, nn_module)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    input_tensor, preprocessing_summary = _prepare_input_tensor(payload, torch_module, nib_module, np_module, F_module)
    with torch_module.no_grad():
        logits_tensor = model(input_tensor)
        if logits_tensor.ndim != 2 or logits_tensor.shape[-1] != 2:
            raise RuntimeError(f"invalid_output: expected [1,2], got {tuple(logits_tensor.shape)}")
        logits = [float(x) for x in logits_tensor.squeeze(0).detach().cpu().tolist()]

    exp_values = [float(__import__("math").exp(x - max(logits))) for x in logits]
    total = sum(exp_values)
    if total <= 0:
        raise RuntimeError("invalid_output: probability normalization failed")
    prob_cap = exp_values[0] / total
    prob_cop = exp_values[1] / total
    candidate_label = "CAP" if prob_cap >= prob_cop else "COP"
    confidence = max(prob_cap, prob_cop)
    uncertainty = 1.0 - confidence

    return {
        "status": "success",
        "trace_id": str(payload.get("trace_id")),
        "case_id": str(payload.get("case_id")),
        "patient_id": payload.get("patient_id"),
        "input_asset_id": str(payload.get("input_asset_id")),
        "source_type": str(payload.get("source_type") or "synthetic"),
        "model_name": MODEL_NAME,
        "adapter_code": ADAPTER_CODE,
        "model_version_id": MODEL_VERSION_ID,
        "artifact_hash": actual_hash,
        "label_mapping": LABEL_MAPPING,
        "logits": [round(v, 6) for v in logits],
        "probabilities": {"CAP": round(prob_cap, 6), "COP": round(prob_cop, 6)},
        "candidate_label": candidate_label,
        "confidence": round(confidence, 6),
        "uncertainty": round(uncertainty, 6),
        "preprocessing_summary": preprocessing_summary,
        "runtime_env": {
            "python_path": sys.executable,
            "torch_version": str(torch_module.__version__),
            "torchvision_version": str(torchvision_module.__version__),
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
        "real_inference": True,
        "shadow_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cap_cop_imaging_resnet18_runner",
        description="Controlled CAP/COP imaging ResNet18 runner candidate with disabled prototype and explicit real-shadow mode.",
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
        trace_id, case_id, input_asset_id, storage_uri = _validate_common_request(payload)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("missing_required_input:"):
            return _failed("missing_required_input", message.split(":", 1)[1].strip(), trace_id=trace_id, case_id=case_id)
        if message.startswith("unsupported_modality:"):
            return _failed("unsupported_modality", message.split(":", 1)[1].strip(), trace_id=trace_id, case_id=case_id)
        if message.startswith("invalid_json:"):
            return _failed("invalid_json", message.split(":", 1)[1].strip(), trace_id=trace_id, case_id=case_id)
        return _failed("invalid_request", message, trace_id=trace_id, case_id=case_id)

    if payload.get("enable_real_shadow") is not True:
        return _emit(_disabled_payload(trace_id=trace_id, case_id=case_id), exit_code=1)

    try:
        result = _run_real_shadow(payload)
        return _emit(result)
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
