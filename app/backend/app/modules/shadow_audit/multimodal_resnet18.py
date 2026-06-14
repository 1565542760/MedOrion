from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access, require_snapshot_access
from app.db.models import Case, CaseImagingInput, CaseModelInputSnapshot, ModelRegistry, ModelVersion, User
from app.modules.model_input.router import build_model_input_assessment_from_schema, build_model_input_schema_for_version
from app.modules.shadow_audit.imaging_contract import (
    imaging_preprocessing_metadata,
    require_preprocessed_imaging_reference,
)
from app.modules.shadow_audit.workflow_readiness import _multimodal_clinical_feature_values, _multimodal_clinical_payload_contract
from app.modules.shadow_audit.multimodal_runner_bridge import invoke_multimodal_runner
from app.modules.shadow_audit.schemas import (
    ControlledShadowMultimodalResNet18OneShotRequestV1,
    ShadowAuditWriteRequestV1,
    ShadowInferenceOutputItemV1,
    ShadowInferenceRunItemV1,
)
from app.modules.shadow_audit.service import create_shadow_audit_record


MULTIMODAL_SHADOW_MODEL_VERSION_ID = UUID("b12f315a-7f44-491d-bf46-b0da73f6da03")
MULTIMODAL_SHADOW_ADAPTER_CODE = "multimodal_resnet18_shadow_bridge"
MULTIMODAL_SHADOW_MODEL_VERSION_LABEL = "cap_cop_classifier_agent_v1.0.0_multimodal_resnet18"
MULTIMODAL_SHADOW_MODEL_FAMILY = "multimodal_resnet18"
MULTIMODAL_SCHEMA_ID = "clinical_mlp_cap_cop_input_schema_v1"
MULTIMODAL_FEATURE_SET_ID = "cap_cop_clinical_feature_set_v1"
MULTIMODAL_ALLOWED_SOURCE_TYPES = {"synthetic"}
MULTIMODAL_WEIGHT_HASH = "f17a4ed6f1f2f4b5e5c0d793a536b4b6e73d154ad2f5578fd844ae041967c809"
MULTIMODAL_RUNNER_FEATURE_COLUMNS_PATH = Path(
    "/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/"
    "multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json"
)
MULTIMODAL_RUNNER_DEFAULT_ZERO_FEATURES = {
    "Height",
    "Weight",
    "BMI",
    "Hospitalization_duration",
    "Upper_left_lung",
    "Lower_left_lung",
    "Right_upper_lung",
    "Right_middle_lung",
    "Right_lower_lung",
    "Whole_lung_lesion",
    "The_lesion_is_located_subpleurally",
    "dizziness",
    "Anti-dizziness_signs",
    "Tree_Bud_Syndrome",
    "Frosted_Glass_Shadow",
    "Bronchial_inflation_sign",
    "Hilar_lymphadenopathy",
    "Pleural_traction",
    "Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green)",
    "chest_tightness",
    "Coughing_up_blood",
    "Weight_loss",
    "CEA",
    "CA153",
    "Serum_non-small_cell lung_cancer-related antigen",
}
MULTIMODAL_RUNNER_ALIAS_MAP = {
    "Striated_shadow": "Striated_shadow.1",
    "Shortness_of_breath": "Dyspnea",
    "Lymphocyte_count": "LymphocytePercent",
    "C-reactive_protein": "CRP",
    "High-sensitivity_C-reactive_protein": "CRP",
}
MULTIMODAL_RUNNER_CATEGORICAL_MAP = {
    "male": 1.0,
    "female": 0.0,
    "none": 0.0,
    "mild": 1.0,
    "moderate": 2.0,
    "severe": 3.0,
    "yes": 1.0,
    "no": 0.0,
    "true": 1.0,
    "false": 0.0,
}


@dataclass(frozen=True)
class MultimodalResNet18OneShotResult:
    run: ShadowInferenceRunItemV1
    outputs: list[ShadowInferenceOutputItemV1]
    artifact_hash: str
    runner_state: str
    prototype_state: str
    runner_response: dict[str, Any]
    execution_mode: str
    limitations: list[str]
    input_asset_id: str
    input_snapshot_id: str

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
    def resource_type(self) -> str:
        return "case_multimodal_input"

    @property
    def model_family(self) -> str:
        return MULTIMODAL_SHADOW_MODEL_FAMILY

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


def _require_snapshot(db: Session, input_snapshot_id: str) -> CaseModelInputSnapshot:
    row = db.execute(
        select(CaseModelInputSnapshot).where(CaseModelInputSnapshot.input_snapshot_id == input_snapshot_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "input_snapshot_not_found", "message": "Input snapshot not found"})
    return row


def _model_version_row(db: Session, model_version_id: UUID) -> tuple[ModelRegistry, ModelVersion]:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "model_version_not_found", "message": "Model version not found"})
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == version.model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "model_version_not_found", "message": "Model version not found"})
    return model, version


def _artifact_hash_from_preflight(result: dict[str, Any] | None) -> str:
    if not isinstance(result, dict):
        return "metadata_only"
    hash_value = result.get("artifact_hash")
    if isinstance(hash_value, str) and hash_value.strip():
        return hash_value.strip()
    expected = result.get("artifact_hash_expected")
    if isinstance(expected, str) and expected.strip():
        return expected.strip()
    return "metadata_only"


def _normalize_source_type(value: str | None) -> str:
    return str(value or "").strip().lower()


def _merge_limitations(*parts: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for part in parts:
        for item in part:
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


@lru_cache(maxsize=1)
def _runner_feature_columns() -> list[str]:
    if not MULTIMODAL_RUNNER_FEATURE_COLUMNS_PATH.exists():
        raise RuntimeError(f"artifact_missing: {MULTIMODAL_RUNNER_FEATURE_COLUMNS_PATH}")
    payload = json.loads(MULTIMODAL_RUNNER_FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    feature_columns = payload.get("feature_columns")
    if not isinstance(feature_columns, list) or len(feature_columns) != 36:
        raise RuntimeError("multimodal_runner_invalid_feature_schema: feature_columns must contain 36 entries")
    return [str(value) for value in feature_columns]


def _coerce_runner_numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return None
        for separator in (" ", ",", ";", "\t"):
            normalized = normalized.replace(separator, " ")
        token = normalized.split(" ", 1)[0]
        try:
            return float(token)
        except ValueError:
            return None
    return None


def _clinical_feature_values(snapshot: CaseModelInputSnapshot) -> tuple[dict[str, float], dict[str, Any]]:
    return _multimodal_clinical_feature_values(snapshot)


def _runtime_env(
    *,
    case: Case,
    input_row: CaseImagingInput,
    snapshot: CaseModelInputSnapshot,
    trace_id: str,
    mode: str,
    artifact_hash: str,
    artifact_preflight: dict[str, Any] | None,
    runner_response: dict[str, Any] | None,
    runner_loaded: bool,
    real_inference: bool,
) -> dict[str, Any]:
    return {
        "execution_mode": mode,
        "coursework_shadow_bridge": True,
        "runner_loaded": bool(runner_loaded),
        "torch_load": bool(real_inference),
        "real_inference": bool(real_inference),
        "not_for_diagnosis": True,
        "shadow_only": True,
        "not_formal_recommendation": True,
        "not_externally_validated": True,
        "model_family": MULTIMODAL_SHADOW_MODEL_FAMILY,
        "model_version_id": MULTIMODAL_SHADOW_MODEL_VERSION_LABEL,
        "artifact_hash": artifact_hash,
        "case_id": str(case.id),
        "patient_id": str(case.patient_id),
        "trace_id": trace_id,
        "input_asset_id": input_row.input_asset_id,
        "input_snapshot_id": snapshot.input_snapshot_id,
        "modality": input_row.modality,
        "source_type": input_row.source_type,
        "storage_uri_ref": input_row.storage_uri,
        "imaging_contract": imaging_preprocessing_metadata(input_row),
        "artifact_preflight": artifact_preflight or {},
        "runner_response": runner_response or {},
        "clinical_schema_id": snapshot.model_input_schema_id,
        "clinical_feature_set_id": snapshot.disease_task_feature_set_id,
    }


def _error_detail(
    *,
    error_code: str,
    error_message: str,
    case: Case,
    input_row: CaseImagingInput,
    snapshot: CaseModelInputSnapshot,
    artifact_hash: str,
    artifact_preflight: dict[str, Any] | None,
    runner_response: dict[str, Any] | None,
    runner_state: str,
    prototype_state: str,
    mode: str,
) -> dict[str, Any]:
    return {
        "code": error_code,
        "message": error_message,
        "coursework_shadow_bridge": True,
        "runner_loaded": mode == "real_shadow_candidate",
        "torch_load": False,
        "real_inference": False,
        "prototype_not_executed": prototype_state == "prototype_not_executed",
        "not_for_diagnosis": True,
        "not_formal_recommendation": True,
        "not_externally_validated": True,
        "model_family": MULTIMODAL_SHADOW_MODEL_FAMILY,
        "model_version_id": MULTIMODAL_SHADOW_MODEL_VERSION_LABEL,
        "artifact_hash": artifact_hash,
        "case_id": str(case.id),
        "patient_id": str(case.patient_id),
        "input_asset_id": input_row.input_asset_id,
        "input_snapshot_id": snapshot.input_snapshot_id,
        "trace_id": snapshot.trace_id,
        "imaging_contract": imaging_preprocessing_metadata(input_row),
        "artifact_preflight": artifact_preflight or {},
        "runner_response": runner_response or {},
        "runner_state": runner_state,
        "prototype_state": prototype_state,
    }


def _write_shadow_audit(
    db: Session,
    *,
    case_uuid: UUID,
    case: Case,
    input_row: CaseImagingInput,
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
    artifact_hash: str,
    artifact_preflight: dict[str, Any] | None,
    runner_response: dict[str, Any] | None,
    runner_state: str,
    prototype_state: str,
    clinical_feature_values: dict[str, Any] | list[Any],
    clinical_feature_translation_summary: dict[str, Any] | None = None,
    real_inference: bool,
) -> MultimodalResNet18OneShotResult:
    started_at = datetime.now(UTC)
    completed_at = started_at
    assessment = build_model_input_assessment_from_schema(schema_item, snapshot.mapped_features_json or {})
    runtime_env = _runtime_env(
        case=case,
        input_row=input_row,
        snapshot=snapshot,
        trace_id=trace_id,
        mode=mode,
        artifact_hash=artifact_hash,
        artifact_preflight=artifact_preflight,
        runner_response=runner_response,
        runner_loaded=real_inference,
        real_inference=real_inference,
    )
    if clinical_feature_translation_summary is not None:
        runtime_env["clinical_feature_translation_summary"] = clinical_feature_translation_summary
    if dry_run_label:
        runtime_env["dry_run_label"] = dry_run_label

    payload = ShadowAuditWriteRequestV1(
        trace_id=trace_id,
        case_id=case_uuid,
        model_version_id=version.id,
        artifact_hash=artifact_hash,
        adapter_code=MULTIMODAL_SHADOW_ADAPTER_CODE,
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
        idempotency_key=f"multimodal-one-shot:{input_row.input_asset_id}:{snapshot.input_snapshot_id}:{trace_id}:{dry_run_label or 'default'}",
    )
    result = create_shadow_audit_record(db, payload)
    limitations = []
    if output is not None:
        output_item = result.outputs[0] if result.outputs else None
        if output_item is not None:
            raw_items = output_item.limitations_json.get("items") if isinstance(output_item.limitations_json, dict) else None
            if isinstance(raw_items, list):
                limitations = [str(item) for item in raw_items]
    else:
        limitations = [error_code or status]

    return MultimodalResNet18OneShotResult(
        run=result.run,
        outputs=result.outputs,
        artifact_hash=artifact_hash,
        runner_state=runner_state,
        prototype_state=prototype_state,
        runner_response=runner_response or {},
        execution_mode=mode,
        limitations=limitations,
        input_asset_id=input_row.input_asset_id,
        input_snapshot_id=snapshot.input_snapshot_id,
    )


def run_controlled_multimodal_resnet18_one_shot_shadow(
    db: Session,
    case_id: str,
    actor: User,
    payload: ControlledShadowMultimodalResNet18OneShotRequestV1,
) -> MultimodalResNet18OneShotResult:
    if not payload.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_multimodal_shadow_flag", "message": "not_for_diagnosis must be true"})
    if not payload.runtime_stub:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_multimodal_shadow_flag", "message": "runtime_stub must be true"})
    if payload.execution_mode != "metadata_only_stub":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_execution_mode", "message": "execution_mode must be metadata_only_stub"})

    case_uuid, case = _require_case(db, case_id)
    require_case_access(db, actor, str(case_uuid), access_level="detail")

    input_row = _require_input_asset(db, payload.input_asset_id)
    if input_row.case_id != case_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "imaging_input_not_found", "message": "Imaging input not found"})
    if not input_row.deidentified or not input_row.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "imaging_input_not_eligible", "message": "Imaging input must be deidentified and not_for_diagnosis"})
    if _normalize_source_type(input_row.source_type) not in MULTIMODAL_ALLOWED_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "unsupported_source_type", "message": "Only synthetic imaging inputs are allowed for this coursework bridge"})
    imaging_contract = require_preprocessed_imaging_reference(input_row, allow_synthetic_only=True)

    snapshot = _require_snapshot(db, payload.input_snapshot_id)
    if snapshot.case_id != case_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "input_snapshot_not_found", "message": "Input snapshot not found"})

    require_snapshot_access(db, actor, snapshot, mode="detail")

    if snapshot.patient_id != input_row.patient_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "input_context_mismatch", "message": "Imaging input and clinical snapshot must belong to the same patient"})

    trace_id = (payload.trace_id.strip() if payload.trace_id else snapshot.trace_id.strip() if snapshot.trace_id else input_row.trace_id.strip())
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_trace_id", "message": "trace_id is required"})

    model, version = _model_version_row(db, snapshot.model_version_id)
    if version.id != MULTIMODAL_SHADOW_MODEL_VERSION_ID:
        assessment = build_model_input_assessment_from_schema(build_model_input_schema_for_version(model, version), snapshot.mapped_features_json or {})
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=build_model_input_schema_for_version(model, version),
            trace_id=trace_id,
            status="shadow_failed",
            error_code="multimodal_clinical_schema_unverified",
            error_detail={
                "code": "multimodal_clinical_schema_unverified",
                "message": "The multimodal bridge is pinned to the approved CAP/COP fold5 clinical provenance",
                "approved_model_version_id": str(MULTIMODAL_SHADOW_MODEL_VERSION_ID),
                "actual_model_version_id": str(version.id),
                "current_assessment_status": assessment.current_assessment_status,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="metadata_only_stub",
            artifact_hash=MULTIMODAL_WEIGHT_HASH,
            artifact_preflight=None,
            runner_response=None,
            runner_state="disabled",
            prototype_state="prototype_not_executed",
            clinical_feature_values=[],
            real_inference=False,
        )
    schema_item = build_model_input_schema_for_version(model, version)
    if schema_item.model_input_schema_id != MULTIMODAL_SCHEMA_ID or schema_item.disease_task_feature_set_id != MULTIMODAL_FEATURE_SET_ID or len(schema_item.feature_requirements) != 36:
        assessment = build_model_input_assessment_from_schema(schema_item, snapshot.mapped_features_json or {})
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status="shadow_failed",
            error_code="multimodal_clinical_schema_unverified",
            error_detail={
                "code": "multimodal_clinical_schema_unverified",
                "message": "The multimodal bridge requires the CAP/COP 36-feature clinical schema to be verified first",
                "model_input_schema_id": schema_item.model_input_schema_id,
                "disease_task_feature_set_id": schema_item.disease_task_feature_set_id,
                "feature_count": schema_item.feature_count,
                "current_assessment_status": assessment.current_assessment_status,
                "missing_required_features": list(assessment.missing_required_features),
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="metadata_only_stub",
            artifact_hash=MULTIMODAL_WEIGHT_HASH,
            artifact_preflight=None,
            runner_response=None,
            runner_state="disabled",
            prototype_state="prototype_not_executed",
            clinical_feature_values=[],
            real_inference=False,
        )

    clinical_feature_values, clinical_feature_translation_summary = _clinical_feature_values(snapshot)
    if any(value is None for value in clinical_feature_values.values()):
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status="shadow_failed",
            error_code="multimodal_clinical_schema_unverified",
            error_detail={
                "code": "multimodal_clinical_schema_unverified",
                "message": "The multimodal bridge could not confirm the 36-feature clinical order",
                "model_input_schema_id": schema_item.model_input_schema_id,
                "disease_task_feature_set_id": schema_item.disease_task_feature_set_id,
                "feature_count": schema_item.feature_count,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="metadata_only_stub",
            artifact_hash=MULTIMODAL_WEIGHT_HASH,
            artifact_preflight=None,
            runner_response=None,
            runner_state="disabled",
            prototype_state="prototype_not_executed",
            clinical_feature_values=clinical_feature_values,
            clinical_feature_translation_summary=clinical_feature_translation_summary,
            real_inference=False,
        )

    if not payload.enable_real_shadow:
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status="shadow_disabled",
            error_code="shadow_disabled",
            error_detail={
                "code": "shadow_disabled",
                "message": "Multimodal real shadow execution is disabled by request",
                "model_family": MULTIMODAL_SHADOW_MODEL_FAMILY,
                "bridge_runtime": "temporary_mri3d_runner",
                "real_shadow_requested": False,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="metadata_only_stub",
            artifact_hash="metadata_only",
            artifact_preflight=None,
            runner_response=None,
            runner_state="disabled",
            prototype_state="prototype_not_executed",
            clinical_feature_values=clinical_feature_values,
            clinical_feature_translation_summary=clinical_feature_translation_summary,
            real_inference=False,
        )

    artifact_probe = invoke_multimodal_runner(check_artifact=True)
    if artifact_probe.payload is None:
        error_code = artifact_probe.error_code or "runner_unavailable"
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status="shadow_failed",
            error_code=error_code,
            error_detail={
                "code": error_code,
                "message": artifact_probe.error_message or "Multimodal runner artifact preflight failed",
                "runner_command": artifact_probe.command,
                "runner_exit_code": artifact_probe.exit_code,
                "dry_run_label": payload.dry_run_label,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="real_shadow_candidate",
            artifact_hash="metadata_only",
            artifact_preflight=None,
            runner_response=None,
            runner_state="failed",
            prototype_state="artifact_preflight_failed",
            clinical_feature_values=clinical_feature_values,
            clinical_feature_translation_summary=clinical_feature_translation_summary,
            real_inference=False,
        )

    artifact_preflight = artifact_probe.payload or {}
    artifact_hash = _artifact_hash_from_preflight(artifact_preflight)
    if not bool(artifact_preflight.get("artifact_hash_match", False)):
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status="shadow_failed",
            error_code="artifact_hash_mismatch",
            error_detail={
                "code": "artifact_hash_mismatch",
                "message": "Exact multimodal fold artifact hash did not match expected provenance",
                "artifact_hash": artifact_hash,
                "artifact_hash_expected": artifact_preflight.get("artifact_hash_expected"),
                "runner_command": artifact_probe.command,
                "runner_exit_code": artifact_probe.exit_code,
                "dry_run_label": payload.dry_run_label,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="real_shadow_candidate",
            artifact_hash=artifact_hash,
            artifact_preflight=artifact_preflight,
            runner_response=None,
            runner_state="failed",
            prototype_state="artifact_preflight_failed",
            clinical_feature_values=clinical_feature_values,
            clinical_feature_translation_summary=clinical_feature_translation_summary,
            real_inference=False,
        )

    runner_request = {
        "trace_id": trace_id,
        "case_id": str(case_uuid),
        "patient_id": str(case.patient_id),
        "input_asset_id": input_row.input_asset_id,
        "input_snapshot_id": snapshot.input_snapshot_id,
        "model_version_id": str(version.id),
        "not_for_diagnosis": True,
        "shadow_only": True,
        "deidentified": True,
        "enable_real_shadow": True,
        "modality": input_row.modality,
        "source_type": _normalize_source_type(input_row.source_type),
        "storage_uri": input_row.storage_uri,
        "source_format": str(imaging_contract.get("preprocessed_format") or imaging_contract["source_format"]),
        "preprocessed_format": str(imaging_contract.get("preprocessed_format") or imaging_contract["source_format"]),
        "preprocessing_script": imaging_contract["preprocessing_script"],
        "conversion_tool": imaging_contract["conversion_tool"],
        "bias_correction": imaging_contract["bias_correction"],
        "model_input_file": imaging_contract["model_input_file"],
        "label_file": imaging_contract["label_file"],
        "clinical_features": clinical_feature_values,
        "clinical_feature_translation_summary": clinical_feature_translation_summary,
    }
    if payload.dry_run_label:
        runner_request["dry_run_label"] = payload.dry_run_label

    runner_result = invoke_multimodal_runner(runner_request)
    if runner_result.payload is None:
        runner_error_code = runner_result.error_code or "runner_unavailable"
        if runner_error_code == "runner_timeout":
            status_code = "shadow_timeout"
            error_code = "runner_timeout"
            prototype_state = "runner_timeout"
        else:
            status_code = "shadow_failed"
            error_code = runner_error_code
            prototype_state = "runner_failed"
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status=status_code,
            error_code=error_code,
            error_detail={
                "code": error_code,
                "message": runner_result.error_message or "Multimodal runner invocation failed",
                "runner_command": runner_result.command,
                "runner_exit_code": runner_result.exit_code,
                "dry_run_label": payload.dry_run_label,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="real_shadow_candidate",
            artifact_hash=artifact_hash,
            artifact_preflight=artifact_preflight,
            runner_response=None,
            runner_state="failed",
            prototype_state=prototype_state,
            clinical_feature_values=clinical_feature_values,
            clinical_feature_translation_summary=clinical_feature_translation_summary,
            real_inference=False,
        )

    runner_payload = runner_result.payload
    runner_status = str(runner_payload.get("status") or "").strip().lower()
    if runner_status != "success":
        runner_error_code = str(runner_payload.get("error_code") or runner_result.error_code or "invalid_runner_response").strip() or "invalid_runner_response"
        if runner_error_code == "input_insufficient":
            status_code = "shadow_insufficient_input"
            audit_error_code = "insufficient_data_for_assessment"
        elif runner_error_code == "runner_timeout":
            status_code = "shadow_timeout"
            audit_error_code = "runner_timeout"
        else:
            status_code = "shadow_failed"
            audit_error_code = runner_error_code
        return _write_shadow_audit(
            db,
            case_uuid=case_uuid,
            case=case,
            input_row=input_row,
            snapshot=snapshot,
            version=version,
            schema_item=schema_item,
            trace_id=trace_id,
            status=status_code,
            error_code=audit_error_code,
            error_detail={
                "code": audit_error_code,
                "message": str(runner_payload.get("error_message") or runner_result.error_message or "Multimodal runner reported an error"),
                "runner_error_code": runner_error_code,
                "runner_exit_code": runner_result.exit_code,
                "runner_command": runner_result.command,
                "dry_run_label": payload.dry_run_label,
            },
            output=None,
            dry_run_label=payload.dry_run_label,
            mode="real_shadow_candidate",
            artifact_hash=artifact_hash,
            artifact_preflight=artifact_preflight,
            runner_response=runner_payload,
            runner_state="failed",
            prototype_state="runner_failed",
            clinical_feature_values=clinical_feature_values,
            clinical_feature_translation_summary=clinical_feature_translation_summary,
            real_inference=False,
        )

    probabilities = runner_payload.get("probabilities") if isinstance(runner_payload.get("probabilities"), dict) else {}
    confidence = runner_payload.get("confidence")
    uncertainty = runner_payload.get("uncertainty")
    limitations = runner_payload.get("limitations")
    if isinstance(limitations, list):
        limitations_items = [str(item) for item in limitations]
    elif isinstance(limitations, dict):
        items = limitations.get("items")
        limitations_items = [str(item) for item in items] if isinstance(items, list) else [str(limitations)]
    else:
        limitations_items = []
    augmented_limitations = _merge_limitations(
        limitations_items,
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
    output = {
        "prediction_raw_json": {
            "runner_status": runner_status,
            "candidate_model_version_id": str(version.id),
            "runner_model_version_id": str(runner_payload.get("model_version_id") or MULTIMODAL_SHADOW_MODEL_VERSION_LABEL),
            "input_asset_id": input_row.input_asset_id,
            "input_snapshot_id": snapshot.input_snapshot_id,
            "trace_id": trace_id,
            "case_id": str(case_uuid),
            "patient_id": str(case.patient_id),
            "model_family": MULTIMODAL_SHADOW_MODEL_FAMILY,
            "adapter_code": MULTIMODAL_SHADOW_ADAPTER_CODE,
            "artifact_hash": artifact_hash,
            "enable_real_shadow": True,
            "real_inference": True,
            "shadow_only": True,
            "not_for_diagnosis": True,
            "label_mapping": runner_payload.get("label_mapping") if isinstance(runner_payload.get("label_mapping"), dict) else {"CAP": 0, "COP": 1},
            "logits": [float(v) for v in (runner_payload.get("logits") if isinstance(runner_payload.get("logits"), list) else [])],
            "image_preprocessing_summary": runner_payload.get("image_preprocessing_summary") if isinstance(runner_payload.get("image_preprocessing_summary"), dict) else {},
            "clinical_preprocessing_summary": runner_payload.get("clinical_preprocessing_summary") if isinstance(runner_payload.get("clinical_preprocessing_summary"), dict) else {},
            "imaging_contract": imaging_contract,
            "fusion_architecture": runner_payload.get("fusion_architecture"),
            "runner_runtime": runner_payload.get("runtime_env") if isinstance(runner_payload.get("runtime_env"), dict) else {},
            "dry_run_label": payload.dry_run_label,
        },
        "prediction_probability_json": {
            "CAP": float(probabilities.get("CAP", 0.0)),
            "COP": float(probabilities.get("COP", 0.0)),
            "probability_source": "softmax_logits",
            "calibrated": False,
        },
        "candidate_label": str(runner_payload.get("candidate_label") or "").strip() or None,
        "confidence_json": {
            "confidence": float(confidence if isinstance(confidence, (int, float)) else (runner_payload.get("confidence") or 0.0)),
            "positive_class": "COP",
            "negative_class": "CAP",
            "calibrated": False,
        },
        "uncertainty_json": {
            "one_minus_max_probability": float(uncertainty if isinstance(uncertainty, (int, float)) else (runner_payload.get("uncertainty") or 1.0)),
            "runner_note": "one_shot_shadow_no_grad_eval_cpu_only",
        },
        "limitations_json": {
            "items": augmented_limitations,
            "runner_mode": "mri3d_subprocess",
            "not_for_diagnosis": True,
            "shadow_only": True,
            "not_formal_recommendation": True,
            "not_externally_validated": True,
            "internal_retrospective_evaluation_only": True,
            "probability_uncalibrated": True,
            "extreme_probability_not_clinical_certainty": True,
            "requires_doctor_review": True,
            "requires_quality_review_before_clinical_use": True,
            "bridge_runtime": "temporary_mri3d_runner",
            "long_term_runtime_target": "model_service_or_inference_service",
            "model_family": MULTIMODAL_SHADOW_MODEL_FAMILY,
            "fold": "fold1",
            "label_mapping": {"CAP": 0, "COP": 1},
            "source_type": _normalize_source_type(input_row.source_type),
            "imaging_contract": imaging_contract,
            "artifact_hash": artifact_hash,
        },
        "input_quality_flags_json": {
            "source_type": _normalize_source_type(input_row.source_type),
            "deidentified": bool(input_row.deidentified),
            "not_for_diagnosis": True,
            "real_shadow_requested": True,
            "real_shadow_executed": True,
            "clinical_schema_id": schema_item.model_input_schema_id,
            "clinical_feature_count": schema_item.feature_count,
            "preprocess_artifact_applied": True,
            "source_format": imaging_contract["source_format"],
            "preprocessed_format": imaging_contract["preprocessed_format"],
            "preprocessing_script": imaging_contract["preprocessing_script"],
            "conversion_tool": imaging_contract["conversion_tool"],
            "bias_correction": imaging_contract["bias_correction"],
            "model_input_file": imaging_contract["model_input_file"],
            "label_file": imaging_contract["label_file"],
            "runner_exit_code": runner_result.exit_code,
            "dry_run_label": payload.dry_run_label,
        },
    }
    return _write_shadow_audit(
        db,
        case_uuid=case_uuid,
        case=case,
        input_row=input_row,
        snapshot=snapshot,
        version=version,
        schema_item=schema_item,
        trace_id=trace_id,
        status="shadow_success",
        error_code=None,
        error_detail={},
        output=output,
        dry_run_label=payload.dry_run_label,
        mode="real_shadow_candidate",
        artifact_hash=artifact_hash,
        artifact_preflight=artifact_preflight,
        runner_response=runner_payload,
        runner_state="success",
        prototype_state="real_shadow_executed",
        clinical_feature_values=clinical_feature_values,
        clinical_feature_translation_summary=clinical_feature_translation_summary,
        real_inference=True,
    )
