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

os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

MODEL_VERSION_ID = 'b12f315a-7f44-491d-bf46-b0da73f6da03'
WEIGHT_PATH = Path('/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold5_best.pth')
PREPROCESS_ARTIFACT_PATH = Path('/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/clinical_tabular_standardization_v1.json')
EXPECTED_WEIGHT_SHA256 = '0b66192745f6c35d5158596e89db7bd1a2d6292ed66a0de4ca3f28c49fa9426a'
LABEL_MAPPING = {'CAP': 0, 'COP': 1}


def _emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    return exit_code


def _error(code: str, message: str, *, trace_id: str | None = None, input_snapshot_id: str | None = None) -> int:
    payload: dict[str, Any] = {
        'status': 'error',
        'error_code': code,
        'error_message': message,
        'limitations': ['not_for_diagnosis', 'shadow_only'],
    }
    if trace_id:
        payload['trace_id'] = trace_id
    if input_snapshot_id:
        payload['input_snapshot_id'] = input_snapshot_id
    return _emit(payload, exit_code=1)


def _read_input(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_json:
        path = Path(args.input_json)
        if not path.exists():
            raise RuntimeError('invalid_json: input file not found')
        text = path.read_text(encoding='utf-8-sig')
    else:
        if sys.stdin.isatty():
            raise RuntimeError('invalid_json: no stdin payload provided')
        text = sys.stdin.read()
        if text.startswith('\ufeff'):
            text = text.lstrip('\ufeff')
    if not text.strip():
        raise RuntimeError('invalid_json: empty JSON input')
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'invalid_json: {exc.msg}') from exc
    if not isinstance(parsed, dict):
        raise RuntimeError('invalid_json: top-level payload must be a JSON object')
    return parsed


def _load_preprocess_artifact() -> tuple[list[str], dict[str, Any]]:
    if not PREPROCESS_ARTIFACT_PATH.exists():
        raise RuntimeError('preprocess_artifact_missing')
    with PREPROCESS_ARTIFACT_PATH.open('r', encoding='utf-8') as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError('invalid_runner_response: preprocess artifact must be a JSON object')
    feature_columns = payload.get('feature_columns')
    if not isinstance(feature_columns, list) or len(feature_columns) != 36:
        raise RuntimeError('invalid_runner_response: preprocess artifact feature_columns invalid')
    return [str(column) for column in feature_columns], payload


def _coerce_numeric(value: Any) -> float:
    if value is None:
        raise KeyError('missing')
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        raise KeyError('missing')
    lowered = text.lower()
    if lowered in {'true', 'yes', 'y', 'present', 'positive'}:
        return 1.0
    if lowered in {'false', 'no', 'n', 'absent', 'negative'}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return float(sum(ord(ch) for ch in text) % 1000) / 1000.0


def _materialize_features(feature_columns: list[str], mapped_features: Any) -> tuple[list[float], list[str]]:
    missing: list[str] = []
    values: list[float] = []
    if isinstance(mapped_features, list):
        if len(mapped_features) != len(feature_columns):
            raise RuntimeError('input_insufficient')
        for index, raw_value in enumerate(mapped_features):
            if raw_value is None:
                missing.append(feature_columns[index])
                values.append(0.0)
            else:
                values.append(_coerce_numeric(raw_value))
        return values, missing
    if not isinstance(mapped_features, dict):
        raise RuntimeError('invalid_json: mapped_features must be a dict or list')
    for column in feature_columns:
        if column not in mapped_features or mapped_features[column] is None:
            missing.append(column)
            values.append(0.0)
            continue
        values.append(_coerce_numeric(mapped_features[column]))
    return values, missing


def _apply_standard_scaler(feature_columns: list[str], values: list[float], preprocess_payload: dict[str, Any]) -> tuple[list[float], bool]:
    scaler = preprocess_payload.get('standard_scaler')
    if not isinstance(scaler, dict):
        return values, False
    mean = scaler.get('mean')
    scale = scaler.get('scale')
    if not isinstance(mean, dict) or not isinstance(scale, dict):
        return values, False
    adjusted: list[float] = []
    applied = False
    for column, value in zip(feature_columns, values):
        if column in mean or column in scale:
            applied = True
        mean_value = mean.get(column, 0.0)
        scale_value = scale.get(column, 1.0)
        try:
            mean_float = float(mean_value)
        except (TypeError, ValueError):
            mean_float = 0.0
        try:
            scale_float = float(scale_value)
        except (TypeError, ValueError):
            scale_float = 1.0
        if scale_float == 0:
            adjusted.append(float(value) - mean_float)
        else:
            adjusted.append((float(value) - mean_float) / scale_float)
    return adjusted, applied


def _compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_state_dict(artifact: Any) -> dict[str, Any]:
    if isinstance(artifact, dict):
        if 'state_dict' in artifact and isinstance(artifact['state_dict'], dict):
            return dict(artifact['state_dict'])
        if 'model_state_dict' in artifact and isinstance(artifact['model_state_dict'], dict):
            return dict(artifact['model_state_dict'])
        if all(isinstance(key, str) for key in artifact.keys()):
            return dict(artifact)
    if hasattr(artifact, 'state_dict') and callable(getattr(artifact, 'state_dict')):
        return dict(artifact.state_dict())
    raise RuntimeError('torch_load_failed')


def _normalize_state_dict(state_dict: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in state_dict.items():
        if key.startswith('module.'):
            key = key[len('module.'):]
        normalized[key] = value
    return normalized


def _build_model(torch_module: Any) -> Any:
    nn = torch_module.nn
    class ClinicalMlpFold5(nn.Module):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__()
            self.fc = nn.Sequential(
                nn.Linear(36, 64),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(32, 2),
            )

        def forward(self, x: Any) -> Any:
            return self.fc(x)

    return ClinicalMlpFold5()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog='cap_cop_clinical_mlp_fold5_runner',
        description='Standalone controlled runner for CAP/COP clinical MLP fold5 one-shot shadow execution.',
    )
    parser.add_argument('--input-json', help='Read runner input from a JSON file instead of stdin.', default=None)
    args = parser.parse_args()

    if not args.input_json and sys.stdin.isatty():
        parser.print_help()
        return 0

    try:
        payload = _read_input(args)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith('invalid_json:'):
            return _error('invalid_json', message.split(':', 1)[1].strip())
        return _error('invalid_json', message)

    trace_id = str(payload.get('trace_id') or '').strip() or None
    input_snapshot_id = str(payload.get('input_snapshot_id') or '').strip() or None

    try:
        model_version_id = str(payload.get('model_version_id') or '').strip()
        if model_version_id != MODEL_VERSION_ID:
            return _error('model_version_mismatch', 'model_version_id does not match CAP/COP clinical MLP fold5', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        if payload.get('not_for_diagnosis') is not True:
            return _error('not_for_diagnosis_required', 'not_for_diagnosis must be true', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        feature_columns, preprocess_payload = _load_preprocess_artifact()
        mapped_features = payload.get('mapped_features')
        feature_values, missing_features = _materialize_features(feature_columns, mapped_features)
        if missing_features:
            return _error('input_insufficient', f'missing required features: {", ".join(missing_features)}', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        if not WEIGHT_PATH.exists():
            return _error('artifact_missing', f'weight file not found at {WEIGHT_PATH}', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        actual_hash = _compute_sha256(WEIGHT_PATH)
        if actual_hash != EXPECTED_WEIGHT_SHA256:
            return _error('artifact_hash_mismatch', 'weight file hash mismatch', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        try:
            import torch  # type: ignore
        except Exception:
            return _error('torch_unavailable', 'torch is not available in the MRI3D runtime', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        torch.set_num_threads(1)
        try:
            torch.set_num_interop_threads(1)
        except Exception:
            pass

        artifact = torch.load(str(WEIGHT_PATH), map_location='cpu')
        state_dict = _normalize_state_dict(_extract_state_dict(artifact))
        model = _build_model(torch)
        model.load_state_dict(state_dict, strict=True)
        model.eval()

        scaled_values, preprocess_applied = _apply_standard_scaler(feature_columns, feature_values, preprocess_payload)
        tensor = torch.tensor([scaled_values], dtype=torch.float32, device='cpu')
        with torch.no_grad():
            raw_output = model(tensor)
        if not hasattr(raw_output, 'detach'):
            return _error('invalid_output', 'model output is not tensor-like', trace_id=trace_id, input_snapshot_id=input_snapshot_id)
        logits = [float(value) for value in raw_output.detach().cpu().reshape(-1).tolist()]
        if len(logits) != 2:
            return _error('invalid_output', 'model output must contain exactly two logits', trace_id=trace_id, input_snapshot_id=input_snapshot_id)

        exp_values = [math.exp(value - max(logits)) for value in logits]
        total = sum(exp_values)
        if total <= 0:
            return _error('invalid_output', 'invalid probability normalization', trace_id=trace_id, input_snapshot_id=input_snapshot_id)
        prob_cap = exp_values[0] / total
        prob_cop = exp_values[1] / total
        candidate_label = 'CAP' if prob_cap >= prob_cop else 'COP'
        confidence = max(prob_cap, prob_cop)
        uncertainty = 1.0 - confidence

        payload_out: dict[str, Any] = {
            'status': 'success',
            'trace_id': trace_id,
            'case_id': str(payload.get('case_id') or '').strip() or None,
            'patient_id': str(payload.get('patient_id') or '').strip() or None,
            'input_snapshot_id': input_snapshot_id,
            'model_version_id': model_version_id,
            'label_mapping': LABEL_MAPPING,
            'logits': [round(value, 6) for value in logits],
            'probabilities': {'CAP': round(prob_cap, 6), 'COP': round(prob_cop, 6)},
            'candidate_label': candidate_label,
            'confidence': {'max_probability': round(confidence, 6)},
            'uncertainty': {'one_minus_max_probability': round(uncertainty, 6)},
            'limitations': ['not_for_diagnosis', 'shadow_only', 'not_formal_recommendation'] + (['preprocess_artifact_not_applied'] if not preprocess_applied else []),
            'runtime': {
                'python_path': sys.executable,
                'torch_version': getattr(torch, '__version__', 'unknown'),
                'device': 'cpu',
            },
        }
        return _emit(payload_out)
    except RuntimeError as exc:
        message = str(exc)
        if message == 'input_insufficient':
            return _error('input_insufficient', 'input is missing required features', trace_id=trace_id, input_snapshot_id=input_snapshot_id)
        if message == 'preprocess_artifact_missing':
            return _error('preprocess_artifact_missing', f'preprocess artifact not found at {PREPROCESS_ARTIFACT_PATH}', trace_id=trace_id, input_snapshot_id=input_snapshot_id)
        if message == 'torch_load_failed':
            return _error('torch_load_failed', 'could not load torch artifact', trace_id=trace_id, input_snapshot_id=input_snapshot_id)
        return _error('invalid_runner_response', message, trace_id=trace_id, input_snapshot_id=input_snapshot_id)
    except FileNotFoundError as exc:
        if str(WEIGHT_PATH) in str(exc):
            return _error('artifact_missing', f'weight file not found at {WEIGHT_PATH}', trace_id=trace_id, input_snapshot_id=input_snapshot_id)
        return _error('runner_unavailable', str(exc), trace_id=trace_id, input_snapshot_id=input_snapshot_id)
    except Exception as exc:
        return _error('inference_failed', str(exc), trace_id=trace_id, input_snapshot_id=input_snapshot_id)


if __name__ == '__main__':
    raise SystemExit(main())
