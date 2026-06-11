from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
) -> dict[str, Any]:
    runner_modality = "ct_image"
    payload = {
        "trace_id": trace_id,
        "case_id": str(case_id),
        "patient_id": str(patient_id),
        "input_asset_id": input_row.input_asset_id,
        "model_version_id": str(IMAGING_SHADOW_MODEL_VERSION_ID),
        "not_for_diagnosis": True,
        "deidentified": True,
        "modality": runner_modality,
        "source_type": input_row.source_type,
        "storage_uri": input_row.storage_uri,
        "execution_mode": "metadata_only_stub",
        "coursework_shadow_bridge": True,
    }
    if dry_run_label:
        payload["dry_run_label"] = dry_run_label
    return payload


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

    trace_id = (payload.trace_id.strip() if payload.trace_id else input_row.trace_id.strip())
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_trace_id", "message": "trace_id is required"})

    if payload.trace_id and payload.trace_id.strip() and payload.trace_id.strip() != input_row.trace_id.strip():
        trace_id_override_ignored = True
    else:
        trace_id_override_ignored = False

    runner_payload = _runner_payload(case_uuid, case.patient_id, input_row, trace_id, payload.dry_run_label)
    artifact_probe = invoke_imaging_runner(check_artifact=True)
    artifact_preflight: dict[str, Any] = artifact_probe.payload or {}
    artifact_hash = str(artifact_preflight.get("artifact_hash") or artifact_preflight.get("artifact_hash_expected") or "metadata_only")
    artifact_match = bool(artifact_preflight.get("artifact_hash_match", True)) if artifact_preflight else True

    runner_result = invoke_imaging_runner(runner_payload)
    runner_response: dict[str, Any] = runner_result.payload or {}
    runner_state = str(runner_response.get("status") or "unknown")
    prototype_state = str(runner_response.get("prototype_state") or "unknown")
    runner_error = runner_response.get("error") if isinstance(runner_response.get("error"), dict) else {}
    runner_error_code = runner_error.get("code") if isinstance(runner_error, dict) else None
    runner_error_message = runner_error.get("message") if isinstance(runner_error, dict) else None

    if artifact_probe.error_code:
        status_code = "shadow_failed"
        error_code = artifact_probe.error_code
        error_message = artifact_probe.error_message or "Imaging runner artifact preflight failed"
    elif not artifact_match:
        status_code = "shadow_failed"
        error_code = "artifact_hash_mismatch"
        error_message = "Imaging runner artifact hash mismatch"
    elif runner_result.error_code is not None:
        status_code = "shadow_failed"
        error_code = runner_result.error_code
        error_message = runner_result.error_message or "Imaging runner invocation failed"
    elif runner_state == "disabled" or prototype_state == "prototype_not_executed":
        status_code = "shadow_disabled"
        error_code = runner_error_code or "imaging_runner_prototype_not_executed"
        error_message = runner_error_message or "Imaging runner prototype not executed"
    else:
        status_code = "shadow_failed"
        error_code = runner_error_code or "imaging_runner_unexpected_state"
        error_message = runner_error_message or "Imaging runner returned unexpected state"

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

    started_at = datetime.now(UTC)
    completed_at = started_at
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
        runtime_env_json=_runtime_env(
            input_row=input_row,
            trace_id=trace_id,
            artifact_preflight=artifact_preflight,
            runner_response=runner_response,
            execution_mode=runner_state if runner_state != "unknown" else prototype_state,
            runner_state=runner_state,
            prototype_state=prototype_state,
        ),
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=0,
        error_code=error_code,
        error_detail_json=_error_detail(
            error_code=error_code,
            error_message=error_message,
            input_row=input_row,
            artifact_preflight=artifact_preflight,
            runner_response=runner_response,
            runner_state=runner_state,
            prototype_state=prototype_state,
        ),
        output=None,
        idempotency_key=f"imaging:{case_uuid}:{input_row.input_asset_id}:{trace_id}:{artifact_hash}",
    )
    audit_result = create_shadow_audit_record(db, write_payload)
    return ImagingResNet18OneShotResult(
        run=audit_result.run,
        outputs=audit_result.outputs,
        artifact_hash=artifact_hash,
        runner_state=runner_state,
        prototype_state=prototype_state,
        runner_response=runner_response,
        execution_mode=runner_state if runner_state != "unknown" else prototype_state,
        limitations=limitations,
    )
