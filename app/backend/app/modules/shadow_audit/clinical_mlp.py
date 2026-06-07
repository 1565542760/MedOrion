from __future__ import annotations

import importlib.util
import hashlib
import json
import logging
import math
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Case, CaseModelInputSnapshot, ModelRegistry, ModelVersion, User
from app.modules.model_input.router import build_model_input_assessment_from_schema, build_model_input_schema_for_version
from app.modules.shadow_audit.schemas import ShadowAuditWriteRequestV1
from app.modules.shadow_audit.service import ShadowAuditWriteResult, create_shadow_audit_record

LOGGER = logging.getLogger('app.shadow_audit.clinical_mlp_one_shot')
EXECUTION_LOCK = threading.Lock()

CLINICAL_MLP_SCHEMA_ID = 'clinical_mlp_cap_cop_input_schema_v1'
CLINICAL_MLP_FEATURE_SET_ID = 'cap_cop_clinical_feature_set_v1'
WEIGHT_PATH = Path('/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold5_best.pth')
PREPROCESS_ARTIFACT_PATH = Path('/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/preprocess_artifacts/clinical_tabular_standardization_v1.json')


def _parse_uuid(value: UUID | str, code: str, message: str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _case_row(db: Session, case_id: UUID | str) -> tuple[UUID, Case]:
    case_uuid = _parse_uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return case_uuid, case


def _snapshot_row(db: Session, input_snapshot_id: str) -> CaseModelInputSnapshot:
    snapshot = db.execute(
        select(CaseModelInputSnapshot).where(CaseModelInputSnapshot.input_snapshot_id == input_snapshot_id)
    ).scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'input_snapshot_not_found', 'message': 'Input snapshot not found'})
    return snapshot


def _model_version_row(db: Session, model_version_id: UUID) -> tuple[ModelRegistry, ModelVersion]:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == version.model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    return model, version


def _artifact_hash_from_version(version: ModelVersion) -> str:
    raw = version.artifact_ref_json
    if isinstance(raw, dict):
        artifact_hash = raw.get('artifact_hash')
        if isinstance(artifact_hash, str) and artifact_hash.strip():
            return artifact_hash.strip()
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return 'metadata_only'


def _json_load(path: Path) -> dict[str, Any]:
    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'preprocess_artifact_invalid', 'message': 'Preprocess artifact must be a JSON object'})
    return data


def _preprocess_path(snapshot: CaseModelInputSnapshot) -> Path:
    ref = (snapshot.preprocess_artifact_ref or '').strip()
    if not ref:
        return PREPROCESS_ARTIFACT_PATH
    ref_path = Path(ref)
    if ref_path.is_absolute():
        return ref_path
    return PREPROCESS_ARTIFACT_PATH.parent / ref


def _encode_numeric_feature(feature: Any, raw_value: Any) -> float:
    feature_type = str(getattr(feature, 'feature_type', '') or '').lower()
    enum_mapping = getattr(feature, 'enum_mapping', None)

    if raw_value is None:
        return 0.0
    if isinstance(raw_value, bool):
        return 1.0 if raw_value else 0.0
    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    text_value = str(raw_value).strip()
    if not text_value:
        return 0.0

    if feature_type in {'boolean', 'bool'}:
        lowered = text_value.lower()
        if lowered in {'1', 'true', 'yes', 'y', 'present', 'positive'}:
            return 1.0
        if lowered in {'0', 'false', 'no', 'n', 'absent', 'negative'}:
            return 0.0
        return 1.0 if lowered not in {'0', 'false', 'no', 'n', 'absent', 'negative'} else 0.0

    if feature_type == 'numeric':
        try:
            return float(text_value)
        except ValueError:
            return 0.0

    if feature_type == 'categorical' and isinstance(enum_mapping, dict):
        keys = list(enum_mapping.keys())
        normalized = text_value.lower()
        for index, key in enumerate(keys):
            if normalized == str(key).strip().lower() or normalized == str(enum_mapping[key]).strip().lower():
                return float(index)
        for index, key in enumerate(keys):
            if str(key).strip().lower() == 'unknown':
                return float(index)
        return 0.0

    try:
        return float(text_value)
    except ValueError:
        return float(sum(ord(char) for char in text_value) % 1000) / 1000.0


def _build_feature_vector(schema_item: Any, mapped_features: dict[str, Any]) -> list[float]:
    vector: list[float] = []
    for feature in schema_item.feature_requirements:
        vector.append(_encode_numeric_feature(feature, mapped_features.get(feature.model_feature_name)))
    return vector


def _apply_preprocess(vector: list[float], preprocess_meta: dict[str, Any]) -> list[float]:
    scaler = preprocess_meta.get('standard_scaler') if isinstance(preprocess_meta, dict) else None
    if not isinstance(scaler, dict):
        return vector
    mean = scaler.get('mean') or []
    scale = scaler.get('scale') or []
    if len(mean) != len(vector) or len(scale) != len(vector):
        return vector
    adjusted: list[float] = []
    for value, mean_value, scale_value in zip(vector, mean, scale):
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
    return adjusted


def _build_runtime_env(
    *,
    snapshot: CaseModelInputSnapshot,
    case: Case,
    version: ModelVersion,
    schema_item: Any,
    trace_id: str,
    dry_run_label: str | None,
    assessment: Any,
    torch_available: bool,
    mode: str,
) -> dict[str, Any]:
    return {
        'execution_mode': mode,
        'one_shot_fold5': True,
        'cpu_only': bool(settings.cap_cop_clinical_mlp_shadow_cpu_only),
        'batch_size': int(settings.cap_cop_clinical_mlp_shadow_batch_size),
        'max_concurrency': int(settings.cap_cop_clinical_mlp_shadow_max_concurrency),
        'force_no_grad': bool(settings.cap_cop_clinical_mlp_shadow_force_no_grad),
        'force_eval_mode': bool(settings.cap_cop_clinical_mlp_shadow_force_eval_mode),
        'disable_gpu': bool(settings.cap_cop_clinical_mlp_shadow_disable_gpu),
        'torch_available': torch_available,
        'model_family': 'clinical_mlp',
        'case_id': str(case.id),
        'patient_id': str(case.patient_id),
        'trace_id': trace_id,
        'input_snapshot_id': snapshot.input_snapshot_id,
        'model_version_id': str(version.id),
        'model_input_schema_id': schema_item.model_input_schema_id,
        'disease_task_feature_set_id': schema_item.disease_task_feature_set_id,
        'feature_count': schema_item.feature_count,
        'mapped_feature_count': assessment.mapped_feature_count,
        'current_assessment_status': assessment.current_assessment_status,
        'missing_required_features': list(assessment.missing_required_features),
        'default_strategy_available': bool(assessment.default_strategy_available),
        'runtime_stub': True,
        'not_for_diagnosis': True,
        'no_silent_fallback': True,
        'dry_run_label': dry_run_label,
        'preprocess_artifact_ref': snapshot.preprocess_artifact_ref,
        'weight_path': str(WEIGHT_PATH),
        'preprocess_artifact_path': str(_preprocess_path(snapshot)),
    }


def _write_shadow_audit(
    db: Session,
    *,
    case_uuid: UUID,
    case: Case,
    snapshot: CaseModelInputSnapshot,
    version: ModelVersion,
    schema_item: Any,
    trace_id: str,
    status: str,
    error_code: str | None,
    error_detail: dict[str, Any],
    output: dict[str, Any] | None,
    dry_run_label: str | None,
    mode: str,
    assessment: Any,
    torch_available: bool,
) -> ShadowAuditWriteResult:
    started_at = datetime.now(UTC)
    completed_at = started_at
    runtime_env = _build_runtime_env(
        snapshot=snapshot,
        case=case,
        version=version,
        schema_item=schema_item,
        trace_id=trace_id,
        dry_run_label=dry_run_label,
        assessment=assessment,
        torch_available=torch_available,
        mode=mode,
    )
    if dry_run_label:
        runtime_env['dry_run_label'] = dry_run_label
    payload = ShadowAuditWriteRequestV1(
        trace_id=trace_id,
        case_id=case_uuid,
        model_version_id=version.id,
        artifact_hash=_artifact_hash_from_version(version),
        adapter_code=settings.cap_cop_clinical_mlp_shadow_runtime_adapter_code,
        status=status,
        not_for_diagnosis=True,
        runtime_stub=True,
        patient_id=str(case.patient_id),
        model_input_schema_id=uuid5(NAMESPACE_URL, schema_item.model_input_schema_id),
        input_snapshot_id=uuid5(NAMESPACE_URL, snapshot.input_snapshot_id),
        runtime_env_json=runtime_env,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=0,
        error_code=error_code,
        error_detail_json=error_detail,
        output=output,
        idempotency_key=f'fold5-one-shot:{snapshot.input_snapshot_id}:{trace_id}:{dry_run_label or "default"}',
    )
    return create_shadow_audit_record(db, payload)


def run_cap_cop_clinical_mlp_fold5_one_shot_shadow(
    db: Session,
    case_id: str,
    actor: User,
    payload: Any,
) -> ShadowAuditWriteResult:
    case_uuid, case = _case_row(db, case_id)
    snapshot = _snapshot_row(db, payload.input_snapshot_id)
    if snapshot.case_id != case_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'input_snapshot_not_found', 'message': 'Input snapshot not found'})

    from app.core.access_control import require_case_access, require_snapshot_access

    require_case_access(db, actor, case_uuid, access_level='detail')
    require_snapshot_access(db, actor, snapshot, mode='detail')

    trace_id = (payload.trace_id or snapshot.trace_id or '').strip()
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_trace_id', 'message': 'trace_id is required'})

    model, version = _model_version_row(db, snapshot.model_version_id)
    schema_item = build_model_input_schema_for_version(model, version)
    if schema_item.model_input_schema_id != CLINICAL_MLP_SCHEMA_ID or schema_item.disease_task_feature_set_id != CLINICAL_MLP_FEATURE_SET_ID:
        assessment = build_model_input_assessment_from_schema(schema_item, snapshot.mapped_features_json or {})
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status='shadow_model_not_enabled',
            error_code='unsupported_model_input_schema',
            error_detail={
                'code': 'unsupported_model_input_schema',
                'message': 'Only CAP/COP clinical MLP fold5 is supported for one-shot shadow execution',
                'model_input_schema_id': schema_item.model_input_schema_id,
                'disease_task_feature_set_id': schema_item.disease_task_feature_set_id,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode='one_shot_fold5',
            assessment=assessment,
            torch_available=False,
        )

    assessment = build_model_input_assessment_from_schema(schema_item, snapshot.mapped_features_json or {})
    if assessment.insufficient_data_for_assessment or assessment.current_assessment_status != 'ready_for_inference':
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status='shadow_insufficient_input',
            error_code='insufficient_data_for_assessment',
            error_detail={
                'code': 'insufficient_data_for_assessment',
                'message': 'Required inputs are insufficient for one-shot shadow execution',
                'current_assessment_status': assessment.current_assessment_status,
                'missing_required_features': list(assessment.missing_required_features),
                'default_strategy_available': bool(assessment.default_strategy_available),
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode='one_shot_fold5',
            assessment=assessment,
            torch_available=False,
        )

    torch_spec = importlib.util.find_spec('torch')
    if torch_spec is None:
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status='shadow_failed',
            error_code='torch_runtime_unavailable',
            error_detail={
                'code': 'torch_runtime_unavailable',
                'message': 'torch is not available in the backend runtime',
                'expected_weight_path': str(WEIGHT_PATH),
                'expected_preprocess_artifact_path': str(_preprocess_path(snapshot)),
                'dry_run_label': payload.dry_run_label,
                'candidate_model_version_id': str(version.id),
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode='one_shot_fold5',
            assessment=assessment,
            torch_available=False,
        )

    preprocess_path = _preprocess_path(snapshot)
    if not preprocess_path.exists():
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status='shadow_failed',
            error_code='preprocess_artifact_not_found',
            error_detail={
                'code': 'preprocess_artifact_not_found',
                'message': 'Preprocess artifact not found',
                'expected_preprocess_artifact_path': str(preprocess_path),
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode='one_shot_fold5',
            assessment=assessment,
            torch_available=True,
        )

    expected_hash = _artifact_hash_from_version(version)
    if expected_hash not in {'', 'metadata_only'} and WEIGHT_PATH.exists():
        sha256_hasher = hashlib.sha256()
        with WEIGHT_PATH.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                sha256_hasher.update(chunk)
        actual_hash_hex = sha256_hasher.hexdigest()
        if actual_hash_hex != expected_hash:
            return _write_shadow_audit(
                db,
                case_uuid=case_uuid,
                case=case,
                snapshot=snapshot,
                version=version,
                schema_item=schema_item,
                trace_id=trace_id,
                status='shadow_failed',
                error_code='artifact_hash_mismatch',
                error_detail={
                    'code': 'artifact_hash_mismatch',
                    'message': 'Artifact hash mismatch before model loading',
                    'expected_artifact_hash': expected_hash,
                    'actual_artifact_hash': actual_hash_hex,
                },
                output=None,
                dry_run_label=payload.dry_run_label,
                mode='one_shot_fold5',
                assessment=assessment,
                torch_available=True,
            )

    try:
        import torch  # type: ignore
    except Exception as exc:
        LOGGER.exception('torch import failed unexpectedly for fold5 one-shot shadow')
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status='shadow_failed',
            error_code='torch_runtime_unavailable',
            error_detail={
                'code': 'torch_runtime_unavailable',
                'message': 'torch is not available in the backend runtime',
                'exception': str(exc),
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode='one_shot_fold5',
            assessment=assessment,
            torch_available=False,
        )

    try:
        with EXECUTION_LOCK:
            loaded = torch.load(str(WEIGHT_PATH), map_location='cpu')
            if hasattr(loaded, 'eval') and callable(getattr(loaded, 'eval')):
                model_obj = loaded
            elif isinstance(loaded, dict) and hasattr(loaded.get('model'), 'eval'):
                model_obj = loaded['model']
            else:
                raise RuntimeError('unsupported_artifact_payload')

            if hasattr(model_obj, 'eval'):
                model_obj.eval()
            vector = _build_feature_vector(schema_item, assessment.mapped_features)
            preprocess_meta = _json_load(preprocess_path)
            vector = _apply_preprocess(vector, preprocess_meta)
            tensor = torch.tensor([vector], dtype=torch.float32)
            with torch.no_grad():
                raw_output = model_obj(tensor) if callable(model_obj) else model_obj.forward(tensor)
            if hasattr(raw_output, 'detach'):
                raw_values = [float(value) for value in raw_output.detach().cpu().reshape(-1).tolist()]
            elif isinstance(raw_output, (list, tuple)):
                raw_values = [float(value) for value in raw_output]
            else:
                raw_values = [float(raw_output)]
            if len(raw_values) == 1:
                logit = raw_values[0]
                p_cop = 1.0 / (1.0 + math.exp(-logit))
                p_cap = 1.0 - p_cop
            else:
                first_two = raw_values[:2]
                max_value = max(first_two)
                exp_values = [math.exp(value - max_value) for value in first_two]
                total = sum(exp_values) or 1.0
                p_cap = exp_values[0] / total
                p_cop = exp_values[1] / total if len(exp_values) > 1 else 1.0 - p_cap
            candidate_label = 'COP' if p_cop >= p_cap else 'CAP'
            output = {
                'prediction_raw_json': {
                    'raw_output_values': raw_values,
                    'candidate_model_version_id': str(version.id),
                    'input_snapshot_id': snapshot.input_snapshot_id,
                    'trace_id': trace_id,
                    'model_input_schema_id': schema_item.model_input_schema_id,
                    'disease_task_feature_set_id': schema_item.disease_task_feature_set_id,
                    'feature_count': schema_item.feature_count,
                    'mapped_feature_count': assessment.mapped_feature_count,
                    'dry_run_label': payload.dry_run_label,
                },
                'prediction_probability_json': {'CAP': round(p_cap, 6), 'COP': round(p_cop, 6)},
                'candidate_label': candidate_label,
                'confidence_json': {'confidence': round(max(p_cap, p_cop), 6), 'positive_class': 'COP', 'negative_class': 'CAP'},
                'uncertainty_json': {'note': 'one-shot_shadow_no_grad_eval_cpu_only', 'source': 'controlled_one_shot'},
                'limitations_json': {'items': ['shadow_audit_only', 'not_for_diagnosis', 'one_shot_fold5', 'cpu_only', 'no_grad', 'eval_mode', 'batch_size_1']},
                'input_quality_flags_json': {
                    'missing_required_features': list(assessment.missing_required_features),
                    'default_strategy_available': bool(assessment.default_strategy_available),
                    'requires_doctor_confirmation': bool(assessment.requires_doctor_confirmation),
                    'dry_run_label': payload.dry_run_label,
                },
            }
            return _write_shadow_audit(
                db,
                case_uuid=case_uuid,
                case=case,
                snapshot=snapshot,
                version=version,
                schema_item=schema_item,
                trace_id=trace_id,
                status='shadow_success',
                error_code=None,
                error_detail={
                    'code': 'shadow_success',
                    'message': 'Fold5 one-shot shadow execution completed successfully',
                    'dry_run_label': payload.dry_run_label,
                },
                output=output,
                dry_run_label=payload.dry_run_label,
                mode='one_shot_fold5',
                assessment=assessment,
                torch_available=True,
            )
    except Exception as exc:
        LOGGER.exception('Fold5 one-shot shadow execution failed')
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status='shadow_failed',
            error_code='runtime_inference_error',
            error_detail={
                'code': 'runtime_inference_error',
                'message': 'Controlled one-shot shadow execution failed',
                'exception': str(exc),
                'dry_run_label': payload.dry_run_label,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode='one_shot_fold5',
            assessment=assessment,
            torch_available=True,
        )
