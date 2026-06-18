from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import Case, CaseImagingInput, CaseModelInputSnapshot, User
from app.modules.shadow_audit.clinical_mlp import run_cap_cop_clinical_mlp_fold5_one_shot_shadow
from app.modules.shadow_audit.imaging_contract import imaging_preprocessing_state, is_ready_preprocessed_imaging_reference
from app.modules.shadow_audit.imaging_resnet18 import run_controlled_imaging_resnet18_one_shot_shadow
from app.modules.shadow_audit.multimodal_resnet18 import run_controlled_multimodal_resnet18_one_shot_shadow
from app.modules.shadow_audit.schemas import ControlledShadowClinicalMlpFold5OneShotRequestV1, ControlledShadowImagingResNet18OneShotRequestV1, ControlledShadowMultimodalResNet18OneShotRequestV1
from app.modules.shadow_audit.workflow_readiness import build_cap_cop_shadow_workflow_readiness, _latest_ready_multimodal_snapshot, _multimodal_clinical_payload_contract

BRANCHES = ['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18']
PREVIEW_LIMITATIONS = ['preview_only', 'shadow_only', 'not_for_diagnosis', 'not_formal_recommendation', 'probability_uncalibrated', 'requires_doctor_review', 'requires_quality_review_before_clinical_use', 'no_runner_invocation', 'no_trace_or_evidence']
EXECUTE_LIMITATIONS = ['shadow_only', 'not_for_diagnosis', 'not_formal_recommendation', 'probability_uncalibrated', 'requires_doctor_review', 'requires_quality_review_before_clinical_use']


def _uuid(value: str, code: str, message: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': code, 'message': message}) from exc


def _case(db: Session, case_id: str):
    case_uuid = _uuid(case_id, 'invalid_case_id', 'Invalid case id')
    case = db.execute(select(Case).where(Case.id == case_uuid)).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'case_not_found', 'message': 'Case not found'})
    return case_uuid, case


def _latest_ready_snapshot(db: Session, case_id: UUID):
    return db.execute(select(CaseModelInputSnapshot).where(CaseModelInputSnapshot.case_id == case_id).where(CaseModelInputSnapshot.validation_status == 'ready_for_inference').where(CaseModelInputSnapshot.current_assessment_status == 'ready_for_inference').where(CaseModelInputSnapshot.not_for_diagnosis.is_(True)).where(CaseModelInputSnapshot.runtime_stub.is_(True)).order_by(CaseModelInputSnapshot.created_at.desc().nullslast(), CaseModelInputSnapshot.updated_at.desc().nullslast(), CaseModelInputSnapshot.id.desc())).scalars().first()


def _latest_ready_imaging(db: Session, case_id: UUID):
    rows = db.execute(select(CaseImagingInput).where(CaseImagingInput.case_id == case_id).order_by(CaseImagingInput.created_at.desc().nullslast(), CaseImagingInput.updated_at.desc().nullslast(), CaseImagingInput.id.desc())).scalars().all()
    for row in rows:
        if is_ready_preprocessed_imaging_reference(row):
            return row
    return None

def _requested(requested: Iterable[str] | None):
    if not requested:
        return list(BRANCHES)
    out, seen = [], set()
    for branch in requested:
        branch = str(branch).strip()
        if branch in BRANCHES and branch not in seen:
            out.append(branch)
            seen.add(branch)
    return out or list(BRANCHES)


def _limits(preview: bool):
    return list(PREVIEW_LIMITATIONS if preview else EXECUTE_LIMITATIONS)


def _item(branch: str, status_value: str, *, disabled=None, run_id=None, output_id=None, candidate=None, probabilities=None, limitations=None):
    return {'branch': branch, 'status': status_value, 'shadow_run_id': run_id, 'output_id': output_id, 'candidate_label': candidate, 'probabilities': probabilities or {}, 'disabled_reasons': list(disabled or []), 'limitations': list(limitations or [])}


def _output(output: Any):
    if output is None:
        return None, {}, []
    limitations = []
    if isinstance(getattr(output, 'limitations_json', None), dict) and isinstance(output.limitations_json.get('items'), list):
        limitations = [str(item) for item in output.limitations_json.get('items')]
    probs = getattr(output, 'prediction_probability_json', None)
    candidate = getattr(output, 'candidate_label', None)
    return (str(candidate) if candidate is not None else None, dict(probs) if isinstance(probs, dict) else {}, limitations)


def _planned(branch: str, readiness_branch: dict[str, Any], requested: bool):
    if not requested:
        return _item(branch, 'skipped', disabled=['branch_not_requested'], limitations=_limits(True))
    if bool(readiness_branch.get('can_run')):
        return _item(branch, 'planned', limitations=_limits(True))
    return _item(branch, 'skipped', disabled=list(readiness_branch.get('disabled_reasons') or ['branch_blocked']), limitations=_limits(True))


def _failed(branch: str, code: str, message: str | None = None):
    reasons = [code]
    if message and message.strip() and message.strip() not in reasons:
        reasons.append(message.strip())
    return _item(branch, 'failed', disabled=reasons, limitations=_limits(False) + [code])


def _clinical(db: Session, case_id: str, actor: User, trace_id: str | None, dry_run_label: str | None, execution_id: str | None = None):
    snapshot = _latest_ready_snapshot(db, _uuid(case_id, 'invalid_case_id', 'Invalid case id'))
    if snapshot is None:
        return _failed('clinical_mlp', 'clinical_snapshot_not_ready', 'No ready clinical snapshot was found')
    result = run_cap_cop_clinical_mlp_fold5_one_shot_shadow(db, case_id, actor, SimpleNamespace(input_snapshot_id=snapshot.input_snapshot_id, trace_id=trace_id or snapshot.trace_id, dry_run_label=dry_run_label, skip_input_assessment=False, execution_id=execution_id))
    output = result.outputs[0] if result.outputs else None
    candidate, probabilities, limitations = _output(output)
    if output is None and result.run.status == 'shadow_success':
        return _failed('clinical_mlp', 'invalid_runner_response', 'Clinical one-shot completed without a shadow output')
    return _item('clinical_mlp', 'executed' if result.run.status == 'shadow_success' else 'failed', run_id=result.run.shadow_run_id, output_id=getattr(output, 'output_id', None) if output is not None else None, candidate=candidate, probabilities=probabilities, disabled=[] if result.run.status == 'shadow_success' else [str(result.run.error_code or 'clinical_branch_failed')], limitations=limitations or _limits(False))


def _imaging(db: Session, case_id: str, actor: User, trace_id: str | None, dry_run_label: str | None, execution_id: str | None = None):
    case_uuid = _uuid(case_id, 'invalid_case_id', 'Invalid case id')
    input_row = _latest_ready_imaging(db, case_uuid)
    if input_row is None:
        return _failed('imaging_resnet18', 'imaging_input_not_ready', 'No ready imaging input was found')
    result = run_controlled_imaging_resnet18_one_shot_shadow(db, case_id, actor, SimpleNamespace(input_asset_id=input_row.input_asset_id, trace_id=trace_id or input_row.trace_id, dry_run_label=dry_run_label, enable_real_shadow=True, not_for_diagnosis=True, runtime_stub=True, execution_mode='metadata_only_stub', execution_id=execution_id))
    output = result.outputs[0] if result.outputs else None
    candidate, probabilities, limitations = _output(output)
    if output is None and result.status == 'shadow_success':
        return _failed('imaging_resnet18', 'invalid_runner_response', 'Imaging one-shot completed without a shadow output')
    return _item('imaging_resnet18', 'executed' if result.status == 'shadow_success' else 'failed', run_id=result.shadow_run_id, output_id=getattr(output, 'output_id', None) if output is not None else None, candidate=candidate, probabilities=probabilities, disabled=[] if result.status == 'shadow_success' else [str(result.error_code or 'imaging_branch_failed')], limitations=limitations or _limits(False))


def _multimodal(db: Session, case_id: str, actor: User, trace_id: str | None, dry_run_label: str | None, execution_id: str | None = None):
    case_uuid = _uuid(case_id, 'invalid_case_id', 'Invalid case id')
    snapshot = _latest_ready_multimodal_snapshot(db, case_uuid)
    imaging_row = _latest_ready_imaging(db, case_uuid)
    if snapshot is None or imaging_row is None:
        return _item('multimodal_resnet18', 'skipped', disabled=['multimodal_inputs_not_ready'], limitations=_limits(False))
    if snapshot.patient_id != imaging_row.patient_id:
        return _item('multimodal_resnet18', 'skipped', disabled=['multimodal_input_context_mismatch'], limitations=_limits(False))
    contract = _multimodal_clinical_payload_contract(snapshot)
    if not contract['ready']:
        return _item('multimodal_resnet18', 'skipped', disabled=list(contract['disabled_reasons'] or ['clinical_input_insufficient']), limitations=_limits(False))
    result = run_controlled_multimodal_resnet18_one_shot_shadow(db, case_id, actor, SimpleNamespace(input_asset_id=imaging_row.input_asset_id, input_snapshot_id=snapshot.input_snapshot_id, trace_id=trace_id or snapshot.trace_id or imaging_row.trace_id, dry_run_label=dry_run_label, enable_real_shadow=True, not_for_diagnosis=True, runtime_stub=True, execution_mode='metadata_only_stub', execution_id=execution_id))
    output = result.outputs[0] if result.outputs else None
    candidate, probabilities, limitations = _output(output)
    if output is None and result.status == 'shadow_success':
        return _failed('multimodal_resnet18', 'invalid_runner_response', 'Multimodal one-shot completed without a shadow output')
    return _item('multimodal_resnet18', 'executed' if result.status == 'shadow_success' else 'failed', run_id=result.shadow_run_id, output_id=getattr(output, 'output_id', None) if output is not None else None, candidate=candidate, probabilities=probabilities, disabled=[] if result.status == 'shadow_success' else [str(result.error_code or 'multimodal_branch_failed')], limitations=limitations or _limits(False))


def run_cap_cop_shadow_workflow(db: Session, case_id: str, actor: User, payload: Any) -> dict[str, Any]:
    case_uuid, case = _case(db, case_id)
    readiness = build_cap_cop_shadow_workflow_readiness(db, case_uuid, actor)
    requested = _requested(getattr(payload, 'requested_branches', None))
    workflow_run_id = f'workflow_{uuid4().hex[:16]}'
    checked_at = datetime.now(UTC).isoformat()
    if str(getattr(payload, 'mode', 'preview')) == 'preview':
        return {'workflow_run_id': workflow_run_id, 'mode': 'preview', 'overall_status': readiness['overall_status'], 'case_id': str(case.id), 'patient_id': str(case.patient_id), 'branches': [_planned(branch, readiness['branches'][branch], branch in requested) for branch in BRANCHES], 'checked_at': checked_at, 'limitations': _limits(True)}
    require_case_access(db, actor, str(case_uuid), access_level='detail')
    workflow_execution_id = f'exec_{uuid4().hex[:16]}'
    branches = []
    for branch in BRANCHES:
        if branch not in requested:
            branches.append(_item(branch, 'skipped', disabled=['branch_not_requested'], limitations=_limits(False)))
            continue
        ready = readiness['branches'][branch]
        if not bool(ready.get('can_run')):
            branches.append(_item(branch, 'skipped', disabled=list(ready.get('disabled_reasons') or ['branch_blocked']), limitations=_limits(False)))
            continue
        handler = {'clinical_mlp': _clinical, 'imaging_resnet18': _imaging, 'multimodal_resnet18': _multimodal}[branch]
        try:
            branches.append(handler(db, case_id, actor, getattr(payload, 'trace_id', None), getattr(payload, 'dry_run_label', None), workflow_execution_id))
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            code = str(detail.get('code') or 'branch_execution_failed')
            message = str(detail.get('message') or 'Branch execution failed')
            branches.append(_item(branch, 'failed', disabled=[code, message], limitations=_limits(False) + [code]))
        except Exception as exc:
            branches.append(_item(branch, 'failed', disabled=['branch_execution_exception', str(exc)], limitations=_limits(False) + ['branch_execution_exception']))
    return {'workflow_run_id': workflow_run_id, 'mode': 'execute', 'overall_status': readiness['overall_status'], 'case_id': str(case.id), 'patient_id': str(case.patient_id), 'branches': branches, 'checked_at': checked_at, 'limitations': _limits(False)}
