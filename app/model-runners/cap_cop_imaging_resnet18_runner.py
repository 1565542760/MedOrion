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


def _emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return exit_code


def _error(code: str, message: str, *, trace_id: str | None = None, case_id: str | None = None) -> int:
    payload: dict[str, Any] = {
        "status": "disabled",
        "prototype_state": "prototype_not_executed",
        "error": {"code": code, "message": message},
        "limitations": [
            "not_for_diagnosis",
            "prototype_not_executed",
            "metadata_only",
            "shadow_only",
        ],
    }
    if trace_id:
        payload["trace_id"] = trace_id
    if case_id:
        payload["case_id"] = case_id
    return _emit(payload, exit_code=1)


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
    value = str(payload.get(key) or "").strip()
    if not value:
        raise RuntimeError(f"missing_required_input: {key}")
    return value


def _validate_request(payload: dict[str, Any]) -> tuple[str, str]:
    trace_id = _require_text(payload, "trace_id")
    case_id = _require_text(payload, "case_id")
    _require_text(payload, "input_asset_id")
    _require_text(payload, "storage_uri")
    modality = _require_text(payload, "modality")
    if modality != EXPECTED_MODALITY:
        raise RuntimeError("unsupported_modality: expected ct_image")
    if payload.get("not_for_diagnosis") is not True:
        raise RuntimeError("missing_required_input: not_for_diagnosis must be true")
    if payload.get("deidentified") is not True:
        raise RuntimeError("missing_required_input: deidentified must be true")
    return trace_id, case_id


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


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cap_cop_imaging_resnet18_runner",
        description="Controlled prototype candidate for CAP/COP imaging ResNet18 shadow preflight.",
    )
    parser.add_argument("--input-json", default=None, help="Read request JSON from a file instead of stdin.")
    parser.add_argument("--artifact-path", default=str(WEIGHT_PATH), help="Explicit artifact path to verify.")
    parser.add_argument(
        "--check-artifact",
        action="store_true",
        help="Only compute and report artifact hash metadata; never load model weights.",
    )
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
                return _error("artifact_missing", message.split(":", 1)[1].strip())
            return _error("artifact_check_failed", message)

    try:
        payload = _read_input(args)
        trace_id, case_id = _validate_request(payload)
    except json.JSONDecodeError as exc:
        return _error("invalid_json", exc.msg)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("missing_required_input:"):
            return _error("missing_required_input", message.split(":", 1)[1].strip())
        if message.startswith("unsupported_modality:"):
            return _error("unsupported_modality", message.split(":", 1)[1].strip())
        if message.startswith("invalid_json:"):
            return _error("invalid_json", message.split(":", 1)[1].strip())
        return _error("invalid_request", message)

    return _emit(
        {
            "status": "disabled",
            "prototype_state": "prototype_not_executed",
            "error": {
                "code": "imaging_runner_not_loaded",
                "message": "imaging ResNet18 runner prototype candidate is not enabled for live execution",
            },
            "trace_id": trace_id,
            "case_id": case_id,
            "model_name": MODEL_NAME,
            "adapter_code": ADAPTER_CODE,
            "model_version_id": MODEL_VERSION_ID,
            "label_mapping": LABEL_MAPPING,
            "artifact_uri": str(WEIGHT_PATH),
            "artifact_hash_expected": EXPECTED_WEIGHT_SHA256,
            "limitations": [
                "not_for_diagnosis",
                "prototype_not_executed",
                "metadata_only",
                "shadow_only",
                "no_torch_load",
                "no_real_forward",
            ],
        },
        exit_code=1,
    )


if __name__ == "__main__":
    raise SystemExit(main())
