from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import Case, CaseImagingInput, User
from app.modules.shadow_audit.imaging_runner_bridge import invoke_imaging_runner
from app.modules.shadow_audit.schemas import (
    ControlledShadowImagingResNet18OneShotRequestV1,
    ShadowAuditWriteRequestV1,
    ShadowInferenceOutputItemV1,
    ShadowInferenceRunItemV1,
)
from app.modules.shadow_audit.service import create_shadow_audit_record


IMAGING_SHADOW_MODEL_VERSION_ID = UUID("b12f315a-7f44-491d-bf46-b0da73f6da03")
IMAGING_SHADOW_ADAPTER_CODE = "imaging_resnet18_shadow_bridge"
IMAGING_SHADOW_MODEL_VERSION_LABEL = "cap_cop_classifier_agent_v1.0.0_imaging_resnet18"
IMAGING_REAL_SHADOW_ALLOWED_SOURCE_TYPES = {"synthetic"}


@dataclass(frozen=True)
class ImagingResNet18OneShotResult:
    run: ShadowInferenceRunItemV1
    outputs: list[ShadowInferenceOutputItemV1]
    artifact_hash: str
    runner_state: str
    prototype_state: str
    runner_response: dict[str, Any]
    execution_mode: str
    limitations: list[str]

    @property
    def status(self) -> str:
        return self.run.status

    @property
    def shadow_run_id(self) -> str:
        return self.run.shadow_run_id

    @property
    def error_code(self) -> str | None:
        return self.run.error_code

    @property
    def error_message(self) -> str | None:
        error_detail = self.run.error_detail_json or {}
        value = error_detail.get("message")
        return str(value) if isinstance(value, str) else None

    @property
    def case_id(self) -> UUID:
        return self.run.case_id

    @property
    def patient_id(self) -> UUID:
        return self.run.patient_id

    @property
    def trace_id(self) -> str:
        return self.run.trace_id

    @property
    def input_asset_id(self) -> str:
        return str((self.run.error_detail_json or {}).get("input_asset_id") or "")

    @property
    def resource_type(self) -> str:
        return "case_imaging_input"

    @property
    def model_family(self) -> str:
        return "imaging_resnet18"

    @property
    def not_for_diagnosis(self) -> bool:
        return True

    @property
    def runtime_stub(self) -> bool:
        return True


def _parse_uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": code, "message": message}) from exc


def _require_case(db: Session, case_id: str) -> tuple[UUID, Case]:
    case_uuid = _parse_uuid(case_id, "invalid_case_id", "Invalid case id")
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "case_not_found", "message": "Case not found"})
    return case_uuid, case


def _require_input_asset(db: Session, input_asset_id: str) -> CaseImagingInput:
    row = db.execute(select(CaseImagingInput).where(CaseImagingInput.input_asset_id == input_asset_id)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "imaging_input_not_found", "message": "Imaging input not found"})
    return row


def _runner_payload(
    case_id: UUID,
    patient_id: UUID,
    input_row: CaseImagingInput,
    trace_id: str,
    dry_run_label: str | None,
    enable_real_shadow: bool,
) -> dict[str, Any]:
    runner_modality = "ct_image"
    source_type = _normalize_source_type(input_row.source_type)
    payload = {
        "trace_id": trace_id,
        "case_id": str(case_id),
        "patient_id": str(patient_id),
        "input_asset_id": input_row.input_asset_id,
        "model_version_id": str(IMAGING_SHADOW_MODEL_VERSION_ID),
        "not_for_diagnosis": True,
        "deidentified": True,
        "modality": runner_modality,
        "source_type": source_type,
        "storage_uri": input_row.storage_uri,
        "execution_mode": "real_shadow_candidate" if enable_real_shadow else "metadata_only_stub",
        "enable_real_shadow": bool(enable_real_shadow),
        "coursework_shadow_bridge": True,
    }
    if dry_run_label:
        payload["dry_run_label"] = dry_run_label
    return payload


def _normalize_source_type(value: str | None) -> str:
    return str(value or "").strip().lower()


def _build_output_payload(
    *,
    trace_id: str,
    case_id: UUID,
    patient_id: UUID,
    input_row: CaseImagingInput,
    runner_response: dict[str, Any],
    artifact_hash: str,
    enable_real_shadow: bool,
    dry_run_label: str | None,
    runner_exit_code: int | None,
) -> dict[str, Any]:
    probabilities = runner_response.get("probabilities") if isinstance(runner_response.get("probabilities"), dict) else {}
    logits = runner_response.get("logits") if isinstance(runner_response.get("logits"), list) else []
    preprocessing_summary = runner_response.get("preprocessing_summary") if isinstance(runner_response.get("preprocessing_summary"), dict) else {}
    label_mapping = runner_response.get("label_mapping") if isinstance(runner_response.get("label_mapping"), dict) else {"CAP": 0, "COP": 1}
    candidate_label = str(runner_response.get("candidate_label") or "").strip() or None
    confidence_value = runner_response.get("confidence")
    uncertainty_value = runner_response.get("uncertainty")
    if confidence_value is None:
        try:
            confidence_value = max(float(probabilities.get("CAP", 0.0)), float(probabilities.get("COP", 0.0)))
        except Exception:
            confidence_value = 0.0
    if uncertainty_value is None:
        try:
            uncertainty_value = 1.0 - float(confidence_value)
        except Exception:
            uncertainty_value = 1.0
    augmented_limitations = _merge_limitations(
        list(runner_response.get("limitations") or []),
        [
            "shadow_only",
            "not_for_diagnosis",
            "not_formal_recommendation",
            "not_externally_validated",
            "internal_retrospective_evaluation_only",
            "probability_uncalibrated",
            "extreme_probability_not_clinical_certainty",
            "requires_doctor_review",
            "requires_quality_review_before_clinical_use",
            "coursework_mvp",
            "synthetic_or_demo_only",
        ],
    )
    return {
        'prediction_raw_json': {
            'runner_status': str(runner_response.get('status') or 'success'),
            'candidate_model_version_id': str(IMAGING_SHADOW_MODEL_VERSION_ID),
            'runner_model_version_id': str(runner_response.get('model_version_id') or IMAGING_SHADOW_MODEL_VERSION_LABEL),
            'input_asset_id': input_row.input_asset_id,
            'trace_id': trace_id,
            'case_id': str(case_id),
            'patient_id': str(patient_id),
            'model_family': 'imaging_resnet18',
            'adapter_code': IMAGING_SHADOW_ADAPTER_CODE,
            'artifact_hash': artifact_hash,
            'enable_real_shadow': bool(enable_real_shadow),
            'real_inference': True,
            'shadow_only': True,
            'not_for_diagnosis': True,
            'label_mapping': label_mapping,
            'logits': [float(v) for v in logits],
            'preprocessing_summary': preprocessing_summary,
            'dry_run_label': dry_run_label,
        },
        'prediction_probability_json': {
            'CAP': float(probabilities.get('CAP', 0.0)),
            'COP': float(probabilities.get('COP', 0.0)),
            'probability_source': 'softmax_logits',
            'calibrated': False,
        },
        'candidate_label': candidate_label,
        'confidence_json': {
            'confidence': float(confidence_value),
            'positive_class': 'COP',
            'negative_class': 'CAP',
            'calibrated': False,
        },
        'uncertainty_json': {
            'one_minus_max_probability': float(uncertainty_value),
            'runner_note': 'one_shot_shadow_no_grad_eval_cpu_only',
        },
        'limitations_json': {
            'items': augmented_limitations,
            'runner_mode': 'mri3d_subprocess',
            'not_for_diagnosis': True,
            'shadow_only': True,
            'not_formal_recommendation': True,
            'not_externally_validated': True,
            'internal_retrospective_evaluation_only': True,
            'probability_uncalibrated': True,
            'extreme_probability_not_clinical_certainty': True,
            'requires_doctor_review': True,
            'requires_quality_review_before_clinical_use': True,
            'bridge_runtime': 'temporary_mri3d_runner',
            'long_term_runtime_target': 'model_service_or_inference_service',
            'model_family': 'imaging_resnet18',
            'fold': 'fold5',
            'label_mapping': {'CAP': 0, 'COP': 1},
            'source_type': _normalize_source_type(input_row.source_type),
        },
        'input_quality_flags_json': {
            'source_type': _normalize_source_type(input_row.source_type),
            'deidentified': bool(input_row.deidentified),
            'not_for_diagnosis': True,
            'real_shadow_requested': bool(enable_real_shadow),
            'real_shadow_executed': True,
            'preprocess_artifact_applied': True,
            'runner_exit_code': runner_exit_code,
            'dry_run_label': dry_run_label,
        },
    }


def _merge_limitations(*parts: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for part in parts:
        for item in part:
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


def _runtime_env(
    *,
    input_row: CaseImagingInput,
    trace_id: str,
    artifact_preflight: dict[str, Any],
    runner_response: dict[str, Any],
    execution_mode: str,
    runner_state: str,
    prototype_state: str,
) -> dict[str, Any]:
    return {
        "execution_mode": execution_mode,
        "coursework_shadow_bridge": True,
        "runner_loaded": False,
        "torch_load": False,
        "real_inference": False,
        "not_for_diagnosis": True,
        "no_image_file_read": True,
        "not_formal_recommendation": True,
        "not_externally_validated": True,
        "model_family": "imaging_resnet18",
        "model_version_id": IMAGING_SHADOW_MODEL_VERSION_LABEL,
        "trace_id": trace_id,
        "input_asset_id": input_row.input_asset_id,
        "modality": input_row.modality,
        "source_type": input_row.source_type,
        "storage_uri_ref": input_row.storage_uri,
        "artifact_preflight": artifact_preflight,
        "runner_response": runner_response,
        "runner_state": runner_state,
        "prototype_state": prototype_state,
    }


def _error_detail(
    *,
    error_code: str,
    error_message: str,
    input_row: CaseImagingInput,
    artifact_preflight: dict[str, Any],
    runner_response: dict[str, Any],
    runner_state: str,
    prototype_state: str,
) -> dict[str, Any]:
    return {
        "code": error_code,
        "message": error_message,
        "coursework_shadow_bridge": True,
        "runner_loaded": False,
        "torch_load": False,
        "real_inference": False,
        "prototype_not_executed": True,
        "not_for_diagnosis": True,
        "not_formal_recommendation": True,
        "not_externally_validated": True,
        "model_family": "imaging_resnet18",
        "model_version_id": IMAGING_SHADOW_MODEL_VERSION_LABEL,
        "input_asset_id": input_row.input_asset_id,
        "trace_id": input_row.trace_id,
        "artifact_preflight": artifact_preflight,
        "runner_response": runner_response,
        "runner_state": runner_state,
        "prototype_state": prototype_state,
    }


def run_controlled_imaging_resnet18_one_shot_shadow(
    db: Session,
    case_id: str,
    actor: User,
    payload: ControlledShadowImagingResNet18OneShotRequestV1,
) -> ImagingResNet18OneShotResult:
    if not payload.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_imaging_shadow_flag", "message": "not_for_diagnosis must be true"})
    if not payload.runtime_stub:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_imaging_shadow_flag", "message": "runtime_stub must be true"})
    if payload.execution_mode != "metadata_only_stub":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_execution_mode", "message": "execution_mode must be metadata_only_stub"})

    case_uuid, case = _require_case(db, case_id)
    require_case_access(db, actor, str(case_uuid), access_level="detail")

    input_row = _require_input_asset(db, payload.input_asset_id)
    if input_row.case_id != case_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "imaging_input_not_found", "message": "Imaging input not found"})
    if not input_row.deidentified or not input_row.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "imaging_input_not_eligible", "message": "Imaging input must be deidentified and not_for_diagnosis"})

    normalized_source_type = _normalize_source_type(input_row.source_type)
    storage_uri = str(input_row.storage_uri or "").strip()
    if not storage_uri:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "imaging_input_not_eligible", "message": "Imaging input storage_uri must be provided"})

    enable_real_shadow = bool(payload.enable_real_shadow)
    if enable_real_shadow and normalized_source_type not in IMAGING_REAL_SHADOW_ALLOWED_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "imaging_input_source_type_not_allowed", "message": "Real-shadow imaging is restricted to synthetic inputs in this stage"})

    trace_id = (payload.trace_id.strip() if payload.trace_id else input_row.trace_id.strip())
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_trace_id", "message": "trace_id is required"})

    if payload.trace_id and payload.trace_id.strip() and payload.trace_id.strip() != input_row.trace_id.strip():
        trace_id_override_ignored = True
    else:
        trace_id_override_ignored = False

    runner_payload = _runner_payload(case_uuid, case.patient_id, input_row, trace_id, payload.dry_run_label, enable_real_shadow)
    artifact_probe = invoke_imaging_runner(check_artifact=True)
    artifact_preflight: dict[str, Any] = artifact_probe.payload or {}
    artifact_hash = str(artifact_preflight.get("artifact_hash") or artifact_preflight.get("artifact_hash_expected") or "metadata_only")
    artifact_match = bool(artifact_preflight.get("artifact_hash_match", True)) if artifact_preflight else True

    runner_result = invoke_imaging_runner(runner_payload)
    runner_response: dict[str, Any] = runner_result.payload or {}
    runner_state = str(runner_response.get("status") or "unknown")
    prototype_state = str(
        runner_response.get("prototype_state")
        or (
            "real_shadow_executed"
            if enable_real_shadow and runner_state == "success"
            else "prototype_not_executed" if runner_state in {"disabled", "failed"} else "unknown"
        )
    )
    runner_error = runner_response.get("error") if isinstance(runner_response.get("error"), dict) else {}
    runner_error_code = runner_error.get("code") if isinstance(runner_error, dict) else None
    runner_error_message = runner_error.get("message") if isinstance(runner_error, dict) else None

    if artifact_probe.error_code:
        status_code = "shadow_failed"
        error_code = artifact_probe.error_code
        error_message = artifact_probe.error_message or "Imaging runner artifact preflight failed"
        output_payload = None
    elif not artifact_match:
        status_code = "shadow_failed"
        error_code = "artifact_hash_mismatch"
        error_message = "Imaging runner artifact hash mismatch"
        output_payload = None
    elif runner_result.error_code is not None:
        status_code = "shadow_failed"
        error_code = runner_result.error_code
        error_message = runner_result.error_message or "Imaging runner invocation failed"
        output_payload = None
    elif enable_real_shadow:
        if runner_state == "success":
            status_code = "shadow_success"
            error_code = None
            error_message = None
            artifact_hash = str(runner_response.get("artifact_hash") or artifact_hash)
            output_payload = _build_output_payload(
                trace_id=trace_id,
                case_id=case_uuid,
                patient_id=case.patient_id,
                input_row=input_row,
                runner_response=runner_response,
                artifact_hash=artifact_hash,
                enable_real_shadow=True,
                dry_run_label=payload.dry_run_label,
                runner_exit_code=runner_result.exit_code,
            )
        else:
            status_code = "shadow_failed"
            error_code = runner_error_code or "imaging_runner_disabled"
            error_message = runner_error_message or "Imaging runner real shadow candidate did not execute"
            output_payload = None
    else:
        if runner_state == "disabled" or prototype_state == "prototype_not_executed":
            status_code = "shadow_disabled"
            error_code = runner_error_code or "imaging_runner_not_loaded"
            error_message = runner_error_message or "Imaging runner prototype not executed"
        else:
            status_code = "shadow_failed"
            error_code = runner_error_code or "imaging_runner_unexpected_state"
            error_message = runner_error_message or "Imaging runner returned unexpected state"
        output_payload = None

    limitations = _merge_limitations(
        list(runner_response.get("limitations") or []),
        [
            "shadow_only",
            "not_for_diagnosis",
            "not_formal_recommendation",
            "prototype_not_executed",
            "runner_loaded=false",
            "torch_load=false",
            "real_inference=false",
            "coursework_shadow_bridge=true",
            "no_image_file_read",
            "not_externally_validated",
        ],
    )
    if trace_id_override_ignored:
        limitations = _merge_limitations(limitations, ["trace_id_override_ignored"])
    if status_code == "shadow_success":
        limitations = _merge_limitations(
            limitations,
            [
                "probability_uncalibrated",
                "synthetic_or_demo_only",
                "internal_retrospective_evaluation_only",
                "extreme_probability_not_clinical_certainty",
                "requires_doctor_review",
                "requires_quality_review_before_clinical_use",
                "coursework_mvp",
            ],
        )

    started_at = datetime.now(UTC)
    completed_at = started_at
    runtime_env_json = {
        "execution_mode": "real_shadow_enabled" if enable_real_shadow else "disabled",
        "coursework_shadow_bridge": True,
        "real_shadow_requested": enable_real_shadow,
        "real_shadow_executed": status_code == "shadow_success",
        "runner_loaded": enable_real_shadow and status_code == "shadow_success",
        "runner_exit_code": runner_result.exit_code,
        "torch_load": enable_real_shadow and status_code == "shadow_success",
        "real_inference": status_code == "shadow_success",
        "not_for_diagnosis": True,
        "no_image_file_read": True,
        "not_formal_recommendation": True,
        "not_externally_validated": True,
        "model_family": "imaging_resnet18",
        "model_version_id": IMAGING_SHADOW_MODEL_VERSION_LABEL,
        "trace_id": trace_id,
        "input_asset_id": input_row.input_asset_id,
        "modality": input_row.modality,
        "source_type": normalized_source_type,
        "storage_uri_ref": storage_uri,
        "artifact_preflight": artifact_preflight,
        "runner_response": runner_response,
        "runner_state": runner_state,
        "prototype_state": prototype_state,
        "enable_real_shadow": enable_real_shadow,
    }
    error_detail_json = {
        "code": status_code,
        "coursework_shadow_bridge": True,
        "runner_loaded": enable_real_shadow and status_code == "shadow_success",
        "torch_load": enable_real_shadow and status_code == "shadow_success",
        "real_inference": status_code == "shadow_success",
        "prototype_not_executed": status_code != "shadow_success",
        "runner_exit_code": runner_result.exit_code,
        "not_for_diagnosis": True,
        "not_formal_recommendation": True,
        "not_externally_validated": True,
        "model_family": "imaging_resnet18",
        "model_version_id": IMAGING_SHADOW_MODEL_VERSION_LABEL,
        "input_asset_id": input_row.input_asset_id,
        "trace_id": trace_id,
        "artifact_preflight": artifact_preflight,
        "runner_response": runner_response,
        "runner_state": runner_state,
        "prototype_state": prototype_state,
        "enable_real_shadow": enable_real_shadow,
        "source_type": normalized_source_type,
        "storage_uri_ref": storage_uri,
        "message": error_message if status_code != "shadow_success" else None,
    }
    if status_code == "shadow_success":
        error_detail_json.pop("message", None)

    write_payload = ShadowAuditWriteRequestV1(
        trace_id=trace_id,
        case_id=case_uuid,
        model_version_id=IMAGING_SHADOW_MODEL_VERSION_ID,
        artifact_hash=artifact_hash,
        adapter_code=IMAGING_SHADOW_ADAPTER_CODE,
        status=status_code,
        not_for_diagnosis=True,
        runtime_stub=True,
        patient_id=str(case.patient_id),
        model_input_schema_id=None,
        input_snapshot_id=None,
        runtime_env_json=runtime_env_json,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=0,
        error_code=error_code,
        error_detail_json=error_detail_json,
        output=output_payload,
        idempotency_key=f"imaging:{case_uuid}:{input_row.input_asset_id}:{trace_id}:{artifact_hash}:{'real' if enable_real_shadow else 'stub'}",
    )
    audit_result = create_shadow_audit_record(db, write_payload)
    return ImagingResNet18OneShotResult(
        run=audit_result.run,
        outputs=audit_result.outputs,
        artifact_hash=artifact_hash,
        runner_state=runner_state,
        prototype_state=prototype_state,
        runner_response=runner_response,
        execution_mode="real_shadow_enabled" if enable_real_shadow else "disabled",
        limitations=limitations,
    )
