
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import Case, CaseImagingInput, User
from app.modules.shadow_audit.schemas import ControlledShadowImagingResNet18OneShotRequestV1


@dataclass(frozen=True)
class ImagingResNet18OneShotResult:
    status: str
    error_code: str | None
    error_message: str | None
    case_id: UUID
    patient_id: UUID
    trace_id: str
    input_asset_id: str
    execution_mode: str
    resource_type: str = 'case_imaging_input'
    model_family: str = 'imaging_resnet18'
    not_for_diagnosis: bool = True
    runtime_stub: bool = True
    limitations: list[str] = None

    def to_dict(self) -> dict[str, object]:
        return {
            'status': self.status,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'case_id': self.case_id,
            'patient_id': self.patient_id,
            'trace_id': self.trace_id,
            'input_asset_id': self.input_asset_id,
            'execution_mode': self.execution_mode,
            'resource_type': self.resource_type,
            'model_family': self.model_family,
            'not_for_diagnosis': self.not_for_diagnosis,
            'runtime_stub': self.runtime_stub,
            'limitations': list(self.limitations or []),
        }


def _parse_uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _require_case(db: Session, case_id: str) -> tuple[UUID, Case]:
    case_uuid = _parse_uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return case_uuid, case


def _require_input_asset(db: Session, input_asset_id: str) -> CaseImagingInput:
    row = db.execute(
        select(CaseImagingInput).where(CaseImagingInput.input_asset_id == input_asset_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'imaging_input_not_found', 'message': 'Imaging input not found'})
    return row


def run_controlled_imaging_resnet18_one_shot_shadow(
    db: Session,
    case_id: str,
    actor: User,
    payload: ControlledShadowImagingResNet18OneShotRequestV1,
) -> ImagingResNet18OneShotResult:
    if not payload.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_imaging_shadow_flag', 'message': 'not_for_diagnosis must be true'})
    if not payload.runtime_stub:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_imaging_shadow_flag', 'message': 'runtime_stub must be true'})
    if payload.execution_mode != 'metadata_only_stub':
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'invalid_execution_mode', 'message': 'execution_mode must be metadata_only_stub'})

    case_uuid, case = _require_case(db, case_id)
    require_case_access(db, actor, str(case_uuid), access_level='detail')

    input_row = _require_input_asset(db, payload.input_asset_id)
    if input_row.case_id != case_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'imaging_input_not_found', 'message': 'Imaging input not found'})
    if not input_row.deidentified or not input_row.not_for_diagnosis:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'imaging_input_not_eligible', 'message': 'Imaging input must be deidentified and not_for_diagnosis'})

    trace_id = input_row.trace_id.strip()
    limitations = [
        'shadow_only',
        'not_for_diagnosis',
        'not_formal_recommendation',
        'runner_not_connected',
        'no_image_file_read',
        'not_externally_validated',
    ]
    if payload.trace_id and payload.trace_id.strip() and payload.trace_id.strip() != trace_id:
        limitations.append('trace_id_override_ignored')

    return ImagingResNet18OneShotResult(
        status='shadow_failed',
        error_code='imaging_runner_not_implemented',
        error_message='Imaging ResNet18 controlled shadow bridge is metadata-only in this stage',
        case_id=case_uuid,
        patient_id=case.patient_id,
        trace_id=trace_id,
        input_asset_id=input_row.input_asset_id,
        execution_mode='metadata_only_stub',
        limitations=limitations,
    )
