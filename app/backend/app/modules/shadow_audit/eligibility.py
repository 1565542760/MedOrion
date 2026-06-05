from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.enums import ModelApprovalState
from app.db.models import ModelRegistry, ModelVersion
from app.modules.model_input.router import build_model_input_assessment_from_schema, build_model_input_schema_for_version

_ALLOWED_MODEL_STATES = {
    ModelApprovalState.APPROVED.value,
    'offline_evaluated',
    'shadow',
}


@dataclass(frozen=True)
class ShadowEligibilityResult:
    status: str
    reason: str | None
    details: dict[str, Any]
    eligible: bool
    runtime_safety_config: dict[str, Any]
    runtime_stub: bool = True
    not_for_diagnosis: bool = True

    def to_dict(self) -> dict[str, Any]:
        result = {
            'status': self.status,
            'reason': self.reason,
            'details': self.details,
            'eligible': self.eligible,
            'runtime_safety_config': self.runtime_safety_config,
            'runtime_stub': self.runtime_stub,
            'not_for_diagnosis': self.not_for_diagnosis,
        }
        if isinstance(self.details, dict):
            for key in ('canonical_adapter_code', 'runtime_adapter_code', 'accepted_adapter_codes', 'registry_adapter_code', 'canonical_match', 'registry_match', 'runtime_match', 'adapter_match'):
                if key in self.details:
                    result[key] = self.details[key]
        return result


# Safety note: an empty allowlist is intentionally fail-closed.
# A model version must be explicitly listed before it can ever become eligible.

def runtime_safety_config_summary() -> dict[str, Any]:
    return {
        'enable_shadow': bool(settings.enable_cap_cop_clinical_mlp_shadow),
        'cpu_only': bool(settings.cap_cop_clinical_mlp_shadow_cpu_only),
        'batch_size': int(settings.cap_cop_clinical_mlp_shadow_batch_size),
        'max_concurrency': int(settings.cap_cop_clinical_mlp_shadow_max_concurrency),
        'timeout_seconds': int(settings.cap_cop_clinical_mlp_shadow_timeout_seconds),
        'force_no_grad': bool(settings.cap_cop_clinical_mlp_shadow_force_no_grad),
        'force_eval_mode': bool(settings.cap_cop_clinical_mlp_shadow_force_eval_mode),
        'disable_gpu': bool(settings.cap_cop_clinical_mlp_shadow_disable_gpu),
        'allowed_model_version_ids': [str(value) for value in settings.cap_cop_clinical_mlp_shadow_allowed_model_version_ids],
    }


def _artifact_metadata(version: ModelVersion) -> dict[str, Any]:
    raw = version.artifact_ref_json
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        return {'artifact_uri': raw.strip()}
    return {}


def _normalize_adapter_code(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def _normalize_adapter_codes(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        candidate = _normalize_adapter_code(values)
        return [candidate] if candidate else []
    if isinstance(values, (list, tuple, set, frozenset)):
        normalized: list[str] = []
        for value in values:
            candidate = _normalize_adapter_code(value)
            if candidate and candidate not in normalized:
                normalized.append(candidate)
        return normalized
    candidate = _normalize_adapter_code(values)
    return [candidate] if candidate else []


def _is_metadata_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return len(value) == 0
    return False


def evaluate_adapter_governance(
    *,
    registry_adapter_code: Any = None,
    runtime_adapter_code: Any = None,
) -> dict[str, Any]:
    canonical_adapter_code = _normalize_adapter_code(settings.cap_cop_clinical_mlp_shadow_canonical_adapter_code)
    runtime_adapter_code_normalized = _normalize_adapter_code(
        runtime_adapter_code or settings.cap_cop_clinical_mlp_shadow_runtime_adapter_code,
    )
    accepted_adapter_codes = _normalize_adapter_codes(settings.cap_cop_clinical_mlp_shadow_accepted_adapter_codes)
    registry_adapter_code_normalized = _normalize_adapter_code(registry_adapter_code)
    canonical_match = bool(canonical_adapter_code) and registry_adapter_code_normalized == canonical_adapter_code
    registry_match = bool(registry_adapter_code_normalized) and registry_adapter_code_normalized in accepted_adapter_codes
    runtime_match = bool(runtime_adapter_code_normalized) and runtime_adapter_code_normalized in accepted_adapter_codes
    adapter_match = registry_match and runtime_match
    return {
        'canonical_adapter_code': canonical_adapter_code,
        'runtime_adapter_code': runtime_adapter_code_normalized,
        'accepted_adapter_codes': accepted_adapter_codes,
        'registry_adapter_code': registry_adapter_code_normalized or None,
        'canonical_match': canonical_match,
        'registry_match': registry_match,
        'runtime_match': runtime_match,
        'adapter_match': adapter_match,
    }


def _candidate_model(db: Session, model_version_id: UUID) -> tuple[ModelRegistry, ModelVersion]:
    version = db.execute(select(ModelVersion).where(ModelVersion.id == model_version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    model = db.execute(select(ModelRegistry).where(ModelRegistry.id == version.model_id)).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'model_version_not_found', 'message': 'Model version not found'})
    return model, version


def evaluate_cap_cop_clinical_mlp_shadow_eligibility(
    db: Session,
    *,
    model_version_id: UUID,
    provided_features: dict[str, Any] | None = None,
    available_modalities: list[str] | None = None,
    respect_global_switch: bool = True,
) -> ShadowEligibilityResult:
    runtime_safety_config = runtime_safety_config_summary()
    if respect_global_switch and not settings.enable_cap_cop_clinical_mlp_shadow:
        return ShadowEligibilityResult(
            status='shadow_disabled',
            reason='shadow gate disabled by backend configuration',
            details={
                'shadow_gate': 'ENABLE_CAP_COP_CLINICAL_MLP_SHADOW',
                'required_state': False,
                'runtime_safety_config': runtime_safety_config,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    model, version = _candidate_model(db, model_version_id)
    metadata = _artifact_metadata(version)
    adapter_governance = evaluate_adapter_governance(registry_adapter_code=metadata.get('adapter_code'))
    allowlist = {str(value) for value in settings.cap_cop_clinical_mlp_shadow_allowed_model_version_ids}
    if not allowlist:
        return ShadowEligibilityResult(
            status='model_not_allowlisted',
            reason='Shadow allowlist is empty and therefore rejects all model versions',
            details={
                'model_version_id': str(version.id),
                'allowlist_empty': True,
                'allowlist_size': 0,
                'approval_state': str(version.approval_state),
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )
    if str(version.id) not in allowlist:
        return ShadowEligibilityResult(
            status='model_not_allowlisted',
            reason='Model version is not in the configured shadow allowlist',
            details={
                'model_version_id': str(version.id),
                'allowlist_empty': False,
                'allowlist_size': len(allowlist),
                'approval_state': str(version.approval_state),
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    if str(version.approval_state) not in _ALLOWED_MODEL_STATES:
        return ShadowEligibilityResult(
            status='model_not_allowlisted',
            reason='Model version lifecycle is not eligible for controlled shadow execution',
            details={
                'model_version_id': str(version.id),
                'approval_state': str(version.approval_state),
                'allowed_states': sorted(_ALLOWED_MODEL_STATES),
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    required_metadata_fields = [
        'artifact_uri',
        'artifact_hash',
        'hash_algorithm',
        'file_size_bytes',
        'registered_by',
        'registered_at',
        'adapter_code',
    ]
    missing_metadata_fields = [field for field in required_metadata_fields if _is_metadata_missing(metadata.get(field))]
    if missing_metadata_fields:
        status_code = 'artifact_hash_missing' if 'artifact_hash' in missing_metadata_fields else 'artifact_metadata_incomplete'
        return ShadowEligibilityResult(
            status=status_code,
            reason='Artifact metadata is incomplete for controlled shadow execution',
            details={
                'model_version_id': str(version.id),
                'model_id': str(model.id),
                'missing_metadata_fields': missing_metadata_fields,
                'artifact_metadata': {key: metadata.get(key) for key in required_metadata_fields},
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    if not adapter_governance['adapter_match']:
        return ShadowEligibilityResult(
            status='adapter_mismatch',
            reason='Artifact adapter code does not match the controlled shadow adapter',
            details={
                'model_version_id': str(version.id),
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    try:
        schema_item = build_model_input_schema_for_version(model, version)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        code = detail.get('code') if isinstance(detail, dict) else None
        if code == 'unsupported_disease_task':
            return ShadowEligibilityResult(
                status='adapter_mismatch',
                reason='Model input schema does not match the CAP/COP clinical MLP shadow contract',
                details={
                    'model_version_id': str(version.id),
                    'model_id': str(model.id),
                    'detail': detail,
                    **adapter_governance,
                },
                eligible=False,
                runtime_safety_config=runtime_safety_config,
            )
        return ShadowEligibilityResult(
            status='model_input_schema_not_found',
            reason='Model input schema not available',
            details={
                'model_version_id': str(version.id),
                'model_id': str(model.id),
                'detail': detail,
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    supported_modalities = {str(item).lower() for item in schema_item.supported_modalities}
    requested_modalities = {str(item).lower() for item in (available_modalities or []) if str(item).strip()}
    if requested_modalities and not (supported_modalities & requested_modalities):
        return ShadowEligibilityResult(
            status='model_not_allowlisted',
            reason='Requested modalities are not compatible with the controlled shadow candidate',
            details={
                'model_version_id': str(version.id),
                'supported_modalities': sorted(supported_modalities),
                'requested_modalities': sorted(requested_modalities),
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    assessment = build_model_input_assessment_from_schema(schema_item, provided_features)
    if assessment.insufficient_data_for_assessment or assessment.missing_required_features:
        return ShadowEligibilityResult(
            status='input_insufficient',
            reason='Required input is incomplete for controlled shadow execution',
            details={
                'model_version_id': str(version.id),
                'model_input_schema_id': schema_item.model_input_schema_id,
                'current_assessment_status': assessment.current_assessment_status,
                'missing_required_features': assessment.missing_required_features,
                'defaultable_features': assessment.defaultable_features,
                'suggested_doctor_questions': assessment.suggested_doctor_questions,
                'default_strategy_available': assessment.default_strategy_available,
                **adapter_governance,
            },
            eligible=False,
            runtime_safety_config=runtime_safety_config,
        )

    return ShadowEligibilityResult(
        status='eligible',
        reason='Model version and inputs are eligible for controlled shadow execution',
        details={
            'model_version_id': str(version.id),
            'model_id': str(model.id),
            'model_input_schema_id': schema_item.model_input_schema_id,
            'disease_task_feature_set_id': schema_item.disease_task_feature_set_id,
            'feature_count': schema_item.feature_count,
            'mapped_feature_count': assessment.mapped_feature_count,
            'supported_modalities': list(schema_item.supported_modalities),
            'default_strategy_available': assessment.default_strategy_available,
            'current_assessment_status': assessment.current_assessment_status,
            **adapter_governance,
        },
        eligible=True,
        runtime_safety_config=runtime_safety_config,
    )
