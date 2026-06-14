from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.access_control import require_case_access
from app.db.models import CaseImagingInput
from app.db.session import SessionLocal
from app.modules.auth.dependencies import require_roles
from app.modules.inference.persistence import resolve_case_context
from app.modules.imaging_inputs.schemas import (
    DicomSeriesImagingInputCreateRequestV1,
    ImagingInputCreateRequestV1,
    ImagingInputCreateResponseV1,
    ImagingInputDetailResponseV1,
    ImagingInputItemV1,
    ImagingInputListResponseV1,
    ImagingPreprocessRequestV1,
    ImagingInputPreprocessingStatusItemV1,
    ImagingInputPreprocessingStatusResponseV1,
    ImagingInputSummaryItemV1,
    ImagingPreprocessResponseV1,
)
from app.modules.imaging_inputs.preprocess_execute import execute_controlled_single_demo_dicom_preprocessing
from app.modules.imaging_inputs.preprocess_plan import build_imaging_preprocessing_job_plan
from app.modules.shadow_audit.imaging_contract import (
    IMAGING_BIAS_CORRECTION,
    IMAGING_CONVERSION_TOOL,
    IMAGING_LABEL_FILE,
    IMAGING_MODEL_INPUT_FILE,
    IMAGING_PREPROCESSING_SCRIPT,
    IMAGING_PREPROCESSING_EXECUTION_MODE_CONTRACT_CHECK,
    IMAGING_PREPROCESSING_EXECUTION_MODE_DRY_RUN,
    IMAGING_PREPROCESSING_STATUS_ALREADY_PREPROCESSED,
    IMAGING_PREPROCESSING_STATUS_NOT_IMPLEMENTED,
    IMAGING_PREPROCESSING_STATUS_PENDING,
    IMAGING_PREPROCESSING_STATUS_READY,
    IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
    IMAGING_RAW_OUTPUT_FILE,
    IMAGING_SOURCE_FORMAT_DICOM_SERIES,
    imaging_preprocessing_metadata,
    imaging_preprocessing_state,
    require_preprocessed_imaging_reference,
)

router = APIRouter()
logger = logging.getLogger('app.imaging_inputs')

IMAGING_INPUT_READ_ROLES = ['doctor', 'admin', 'super_admin']
IMAGING_INPUT_WRITE_ROLES = ['doctor', 'admin', 'super_admin']
imaging_input_read_guard = require_roles(IMAGING_INPUT_READ_ROLES)
imaging_input_write_guard = require_roles(IMAGING_INPUT_WRITE_ROLES)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _resolve_case_context_or_404(db: Session, case_identifier: str) -> tuple[UUID, UUID]:
    try:
        case_id_text, patient_id_text = resolve_case_context(db, case_identifier)
    except RuntimeError as exc:
        if str(exc) == 'case_not_found':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'code': 'case_not_found', 'message': 'Case not found'},
            ) from exc
        raise
    return UUID(case_id_text), UUID(patient_id_text)


def _normalize_text(value: str | None) -> str:
    return (value or '').strip()


def _contract_payload(
    *,
    source_format: str,
    preprocessed_format: str,
    preprocessing_script: str,
    conversion_tool: str,
    bias_correction: str,
    raw_output_file: str,
    model_input_file: str,
    label_file: str,
    preprocessing_status: str,
) -> dict[str, Any]:
    return {
        'source_format': source_format,
        'preprocessed_format': preprocessed_format,
        'preprocessing_script': preprocessing_script,
        'conversion_tool': conversion_tool,
        'bias_correction': bias_correction,
        'raw_output_file': raw_output_file,
        'model_input_file': model_input_file,
        'label_file': label_file,
        'preprocessing_status': preprocessing_status,
    }


def _register_imaging_row(
    db: Session,
    *,
    case_id: UUID,
    patient_id: UUID,
    trace_id: str,
    modality: str,
    source_type: str,
    storage_uri: str,
    provenance_json: dict[str, Any],
    quality_flags_json: dict[str, Any],
    deidentified: bool = True,
    not_for_diagnosis: bool = True,
) -> CaseImagingInput:
    input_asset_id = f'img_{uuid4().hex}'
    row = CaseImagingInput(
        input_asset_id=input_asset_id,
        case_id=case_id,
        patient_id=patient_id,
        trace_id=_normalize_text(trace_id),
        modality=modality,
        source_type=source_type,
        storage_uri=_normalize_text(storage_uri),
        deidentified=deidentified,
        not_for_diagnosis=not_for_diagnosis,
        provenance_json=dict(provenance_json or {}),
        quality_flags_json=dict(quality_flags_json or {}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _summary_item(row: CaseImagingInput) -> ImagingInputSummaryItemV1:
    return ImagingInputSummaryItemV1(
        id=row.id,
        input_asset_id=row.input_asset_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        modality=row.modality,
        source_type=row.source_type,
        deidentified=row.deidentified,
        not_for_diagnosis=row.not_for_diagnosis,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _detail_item(row: CaseImagingInput) -> ImagingInputItemV1:
    return ImagingInputItemV1(
        id=row.id,
        input_asset_id=row.input_asset_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        modality=row.modality,
        source_type=row.source_type,
        storage_uri=row.storage_uri,
        deidentified=row.deidentified,
        not_for_diagnosis=row.not_for_diagnosis,
        provenance_json=dict(row.provenance_json or {}),
        quality_flags_json=dict(row.quality_flags_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _status_item(row: CaseImagingInput) -> ImagingInputPreprocessingStatusItemV1:
    state = imaging_preprocessing_state(row)
    return ImagingInputPreprocessingStatusItemV1(
        id=row.id,
        input_asset_id=row.input_asset_id,
        case_id=row.case_id,
        patient_id=row.patient_id,
        trace_id=row.trace_id,
        modality=row.modality,
        source_type=row.source_type,
        storage_uri=row.storage_uri,
        deidentified=row.deidentified,
        not_for_diagnosis=row.not_for_diagnosis,
        source_format=state['source_format'],
        preprocessed_format=state['preprocessed_format'],
        preprocessing_script=state['preprocessing_script'],
        conversion_tool=state['conversion_tool'],
        bias_correction=state['bias_correction'],
        raw_output_file=state['raw_output_file'],
        model_input_file=state['model_input_file'],
        label_file=state['label_file'],
        preprocessing_status=state['preprocessing_status'],
        provenance_json=dict(row.provenance_json or {}),
        quality_flags_json=dict(row.quality_flags_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )



def _persist_preprocess_preview(
    db: Session,
    row: CaseImagingInput,
    *,
    preprocessing_status: str,
    execution_mode: str,
    dry_run: bool,
    execute: bool,
    candidate_kind: str,
    job_plan: dict[str, Any],
) -> CaseImagingInput:
    provenance = dict(row.provenance_json or {})
    quality_flags = dict(row.quality_flags_json or {})
    preview_payload = {
        'preprocessing_status': preprocessing_status,
        'preprocessing_execution_mode': execution_mode,
        'preprocessing_dry_run': dry_run,
        'preprocessing_execute': execute,
        'preprocessing_will_execute': False,
        'preprocessing_requested_at': _now().isoformat(),
        'preprocessing_job_id': job_plan['job_id'],
        'preprocessing_job_state': job_plan['job_state'],
        'preprocessing_managed_workspace': job_plan['managed_workspace'],
        'preprocessing_expected_input_kind': job_plan['expected_input_kind'],
        'preprocessing_candidate_kind': candidate_kind,
        'preprocessing_command_plan': job_plan['command_plan'],
        'preprocessing_expected_outputs': job_plan['expected_outputs'],
        'preprocessing_safety_gate': job_plan['safety_gate'],
        'expected_steps': job_plan['expected_steps'],
        'expected_raw_output_file': IMAGING_RAW_OUTPUT_FILE,
        'expected_model_input_file': IMAGING_MODEL_INPUT_FILE,
        'expected_label_file': IMAGING_LABEL_FILE,
        'expected_preprocessed_format': IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
    }
    provenance.update(preview_payload)
    quality_flags.update(preview_payload)
    row.provenance_json = provenance
    row.quality_flags_json = quality_flags
    db.commit()
    db.refresh(row)
    return row


def _persist_preprocess_execution_result(
    db: Session,
    row: CaseImagingInput,
    *,
    preprocessing_status: str,
    execution_mode: str,
    dry_run: bool,
    execute: bool,
    candidate_kind: str,
    job_plan: dict[str, Any],
    execution_result: dict[str, Any] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> CaseImagingInput:
    provenance = dict(row.provenance_json or {})
    quality_flags = dict(row.quality_flags_json or {})
    execution_payload = {
        'preprocessing_status': preprocessing_status,
        'preprocessing_execution_mode': execution_mode,
        'preprocessing_dry_run': dry_run,
        'preprocessing_execute': execute,
        'preprocessing_will_execute': bool(execute),
        'preprocessing_requested_at': _now().isoformat(),
        'preprocessing_job_id': job_plan['job_id'],
        'preprocessing_job_state': preprocessing_status,
        'preprocessing_managed_workspace': job_plan['managed_workspace'],
        'preprocessing_expected_input_kind': job_plan['expected_input_kind'],
        'preprocessing_candidate_kind': candidate_kind,
        'preprocessing_command_plan': job_plan['command_plan'],
        'preprocessing_expected_outputs': job_plan['expected_outputs'],
        'preprocessing_safety_gate': job_plan['safety_gate'],
        'expected_steps': job_plan['expected_steps'],
        'expected_raw_output_file': IMAGING_RAW_OUTPUT_FILE,
        'expected_model_input_file': IMAGING_MODEL_INPUT_FILE,
        'expected_label_file': IMAGING_LABEL_FILE,
        'expected_preprocessed_format': IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
        'preprocessing_error_code': error_code,
        'preprocessing_error_message': error_message,
    }
    if execution_result:
        execution_payload.update({
            'preprocessing_source_storage_uri': execution_result.get('source_storage_uri'),
            'preprocessing_raw_output_uri': execution_result.get('raw_output_uri'),
            'preprocessing_image_output_uri': execution_result.get('image_output_uri'),
            'preprocessing_dcm2niix_stdout': execution_result.get('dcm2niix_stdout'),
            'preprocessing_dcm2niix_stderr': execution_result.get('dcm2niix_stderr'),
            'preprocessing_n4_stdout': execution_result.get('n4_stdout'),
            'preprocessing_n4_stderr': execution_result.get('n4_stderr'),
        })
        if preprocessing_status == 'completed' and execution_result.get('image_output_uri'):
            row.storage_uri = str(execution_result['image_output_uri'])
    provenance.update(execution_payload)
    quality_flags.update(execution_payload)
    row.provenance_json = provenance
    row.quality_flags_json = quality_flags
    db.commit()
    db.refresh(row)
    return row


@router.post('/cases/{case_id}/imaging-inputs', response_model=ImagingInputCreateResponseV1)
def create_imaging_input(
    case_id: str,
    payload: ImagingInputCreateRequestV1,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_write_guard),
) -> ImagingInputCreateResponseV1:
    resolved_case_id, resolved_patient_id = _resolve_case_context_or_404(db, case_id)
    if payload.patient_id != resolved_patient_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'patient_mismatch', 'message': 'Patient does not match the case'},
        )

    require_case_access(db, user, str(resolved_case_id), access_level='detail')

    row = _register_imaging_row(
        db,
        case_id=resolved_case_id,
        patient_id=resolved_patient_id,
        trace_id=payload.trace_id,
        modality=payload.modality,
        source_type=payload.source_type,
        storage_uri=payload.storage_uri,
        provenance_json=payload.provenance_json,
        quality_flags_json=payload.quality_flags_json,
        deidentified=True,
        not_for_diagnosis=True,
    )
    return ImagingInputCreateResponseV1(
        status='created',
        route='/cases/{case_id}/imaging-inputs',
        item=_detail_item(row),
    )


@router.post('/cases/{case_id}/imaging-inputs/dicom-series', response_model=ImagingInputPreprocessingStatusResponseV1)
def register_dicom_series_imaging_input(
    case_id: str,
    payload: DicomSeriesImagingInputCreateRequestV1,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_write_guard),
) -> ImagingInputPreprocessingStatusResponseV1:
    resolved_case_id, resolved_patient_id = _resolve_case_context_or_404(db, case_id)
    if payload.patient_id != resolved_patient_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'patient_mismatch', 'message': 'Patient does not match the case'},
        )

    require_case_access(db, user, str(resolved_case_id), access_level='detail')

    provenance = {
        'source_format': IMAGING_SOURCE_FORMAT_DICOM_SERIES,
        'preprocessed_format': IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
        'preprocessing_script': payload.preprocessing_script or IMAGING_PREPROCESSING_SCRIPT,
        'conversion_tool': payload.conversion_tool or IMAGING_CONVERSION_TOOL,
        'bias_correction': payload.bias_correction or IMAGING_BIAS_CORRECTION,
        'raw_output_file': payload.raw_output_file or IMAGING_RAW_OUTPUT_FILE,
        'model_input_file': payload.model_input_file or 'image.nii.gz',
        'label_file': payload.label_file or 'label.nii.gz',
        'preprocessing_status': IMAGING_PREPROCESSING_STATUS_PENDING,
        **dict(payload.provenance_json or {}),
    }
    quality_flags = {
        'source_format': IMAGING_SOURCE_FORMAT_DICOM_SERIES,
        'preprocessed_format': IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
        'preprocessing_script': payload.preprocessing_script or IMAGING_PREPROCESSING_SCRIPT,
        'conversion_tool': payload.conversion_tool or IMAGING_CONVERSION_TOOL,
        'bias_correction': payload.bias_correction or IMAGING_BIAS_CORRECTION,
        'raw_output_file': payload.raw_output_file or IMAGING_RAW_OUTPUT_FILE,
        'model_input_file': payload.model_input_file or 'image.nii.gz',
        'label_file': payload.label_file or 'label.nii.gz',
        'preprocessing_status': IMAGING_PREPROCESSING_STATUS_PENDING,
        **dict(payload.quality_flags_json or {}),
    }
    row = _register_imaging_row(
        db,
        case_id=resolved_case_id,
        patient_id=resolved_patient_id,
        trace_id=payload.trace_id,
        modality=payload.modality,
        source_type=payload.source_type,
        storage_uri=payload.storage_uri,
        provenance_json=provenance,
        quality_flags_json=quality_flags,
        deidentified=True,
        not_for_diagnosis=True,
    )
    return ImagingInputPreprocessingStatusResponseV1(
        status='ok',
        route='/cases/{case_id}/imaging-inputs/dicom-series',
        item=_status_item(row),
    )


@router.get('/cases/{case_id}/imaging-inputs', response_model=ImagingInputListResponseV1)
def list_imaging_inputs(
    case_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(imaging_input_read_guard),
) -> ImagingInputListResponseV1:
    resolved_case_id, _resolved_patient_id = _resolve_case_context_or_404(db, case_id)
    require_case_access(db, user, str(resolved_case_id), access_level='summary')

    base_query = select(CaseImagingInput).where(CaseImagingInput.case_id == resolved_case_id)
    total = db.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    rows = db.execute(
        base_query.order_by(CaseImagingInput.created_at.desc(), CaseImagingInput.id.desc()).offset(offset).limit(limit)
    ).scalars().all()
    return ImagingInputListResponseV1(
        status='ok',
        route='/cases/{case_id}/imaging-inputs',
        total=total,
        limit=limit,
        offset=offset,
        items=[_summary_item(row) for row in rows],
    )


@router.get('/imaging-inputs/{input_asset_id}', response_model=ImagingInputDetailResponseV1)
def get_imaging_input(
    input_asset_id: str,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_read_guard),
) -> ImagingInputDetailResponseV1:
    row = db.execute(
        select(CaseImagingInput).where(CaseImagingInput.input_asset_id == input_asset_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'imaging_input_not_found', 'message': 'Imaging input not found'},
        )
    require_case_access(db, user, str(row.case_id), access_level='detail')
    return ImagingInputDetailResponseV1(
        status='ok',
        route='/imaging-inputs/{input_asset_id}',
        item=_detail_item(row),
    )


@router.get('/imaging-inputs/{input_asset_id}/preprocessing-status', response_model=ImagingInputPreprocessingStatusResponseV1)
def get_imaging_input_preprocessing_status(
    input_asset_id: str,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_read_guard),
) -> ImagingInputPreprocessingStatusResponseV1:
    row = db.execute(
        select(CaseImagingInput).where(CaseImagingInput.input_asset_id == input_asset_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'imaging_input_not_found', 'message': 'Imaging input not found'},
        )
    require_case_access(db, user, str(row.case_id), access_level='detail')
    return ImagingInputPreprocessingStatusResponseV1(
        status='ok',
        route='/imaging-inputs/{input_asset_id}/preprocessing-status',
        item=_status_item(row),
    )


@router.post('/imaging-inputs/{input_asset_id}/preprocess', response_model=ImagingPreprocessResponseV1)
def preprocess_imaging_input(
    input_asset_id: str,
    payload: ImagingPreprocessRequestV1,
    db: Session = Depends(get_db),
    user=Depends(imaging_input_write_guard),
) -> ImagingPreprocessResponseV1:
    row = db.execute(
        select(CaseImagingInput).where(CaseImagingInput.input_asset_id == input_asset_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'imaging_input_not_found', 'message': 'Imaging input not found'},
        )
    require_case_access(db, user, str(row.case_id), access_level='detail')

    job_plan = build_imaging_preprocessing_job_plan(
        row,
        dry_run=payload.dry_run,
        execute=payload.execute,
        execution_mode=payload.execution_mode,
    )
    classification = job_plan['classification']

    if payload.execute:
        if payload.allow_real_preprocessing and payload.execution_mode == 'single_demo':
            try:
                execution_result = execute_controlled_single_demo_dicom_preprocessing(
                    row,
                    job_plan,
                    allow_real_preprocessing=payload.allow_real_preprocessing,
                    execution_mode=payload.execution_mode,
                )
            except HTTPException:
                raise
            except Exception as exc:
                row = _persist_preprocess_execution_result(
                    db,
                    row,
                    preprocessing_status='failed',
                    execution_mode=payload.execution_mode,
                    dry_run=payload.dry_run,
                    execute=payload.execute,
                    candidate_kind=classification['candidate_kind'],
                    job_plan=job_plan,
                    error_code='controlled_preprocessing_failed',
                    error_message=str(exc),
                )
                status_item = _status_item(row)
                return ImagingPreprocessResponseV1(
                    status='failed',
                    route='/imaging-inputs/{input_asset_id}/preprocess',
                    dry_run=payload.dry_run,
                    execute=payload.execute,
                    execution_mode=payload.execution_mode,
                    will_execute=True,
                    job_id=job_plan['job_id'],
                    job_state='failed',
                    managed_workspace=job_plan['managed_workspace'],
                    expected_input_kind=job_plan['expected_input_kind'],
                    candidate_kind=classification['candidate_kind'],
                    error_code='controlled_preprocessing_failed',
                    message='Controlled preprocessing failed; temporary outputs were cleaned up',
                    expected_steps=job_plan['expected_steps'],
                    command_plan=job_plan['command_plan'],
                    expected_outputs=job_plan['expected_outputs'],
                    safety_gate=job_plan['safety_gate'],
                    item=status_item,
                    limitations=[
                        'not_for_diagnosis',
                        'shadow_only',
                        'not_formal_recommendation',
                        'controlled_real_preprocessing_requested',
                        'preprocessing_failed',
                        'managed_workspace_only',
                    ],
                )
            row = _persist_preprocess_execution_result(
                db,
                row,
                preprocessing_status='completed',
                execution_mode=payload.execution_mode,
                dry_run=payload.dry_run,
                execute=payload.execute,
                candidate_kind=classification['candidate_kind'],
                job_plan=job_plan,
                execution_result=execution_result,
            )
            status_item = _status_item(row)
            return ImagingPreprocessResponseV1(
                status='completed',
                route='/imaging-inputs/{input_asset_id}/preprocess',
                dry_run=payload.dry_run,
                execute=payload.execute,
                execution_mode=payload.execution_mode,
                will_execute=True,
                job_id=job_plan['job_id'],
                job_state='completed',
                managed_workspace=job_plan['managed_workspace'],
                expected_input_kind=job_plan['expected_input_kind'],
                candidate_kind=classification['candidate_kind'],
                error_code=None,
                message='Controlled single-demo DICOM preprocessing completed',
                expected_steps=job_plan['expected_steps'],
                command_plan=execution_result['command_plan'],
                expected_outputs=job_plan['expected_outputs'],
                safety_gate=job_plan['safety_gate'],
                item=status_item,
                limitations=[
                    'not_for_diagnosis',
                    'shadow_only',
                    'not_formal_recommendation',
                    'controlled_real_preprocessing_executed',
                    'single_demo',
                    'managed_workspace_only',
                    'no_model_run',
                ],
            )
        row = _persist_preprocess_preview(
            db,
            row,
            preprocessing_status='blocked_by_contract',
            execution_mode=payload.execution_mode,
            dry_run=payload.dry_run,
            execute=payload.execute,
            candidate_kind=classification['candidate_kind'],
            job_plan=job_plan,
        )
        status_item = _status_item(row)
        return ImagingPreprocessResponseV1(
            status='blocked_by_contract',
            route='/imaging-inputs/{input_asset_id}/preprocess',
            dry_run=payload.dry_run,
            execute=payload.execute,
            execution_mode=payload.execution_mode,
            will_execute=False,
            job_id=job_plan['job_id'],
            job_state='blocked_by_contract',
            managed_workspace=job_plan['managed_workspace'],
            expected_input_kind=job_plan['expected_input_kind'],
            candidate_kind=classification['candidate_kind'],
            error_code='execution_not_enabled',
            message='This coursework stage only builds a managed preprocessing execution skeleton',
            expected_steps=job_plan['expected_steps'],
            command_plan=job_plan['command_plan'],
            expected_outputs=job_plan['expected_outputs'],
            safety_gate=job_plan['safety_gate'],
            item=status_item,
            limitations=[
                'not_for_diagnosis',
                'shadow_only',
                'not_formal_recommendation',
                'execution_not_enabled',
                'managed_workspace_only',
                'no_external_command_execution',
            ],
        )

    if job_plan['job_state'] == 'blocked_by_contract':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'code': 'blocked_by_contract',
                'message': 'Input is not a supported DICOM series or preprocessed NIfTI candidate',
            },
        )

    if classification['candidate_kind'] == 'already_preprocessed_candidate':
        message = 'Input already looks preprocessed; recording a managed plan only'
        limitations = [
            'not_for_diagnosis',
            'shadow_only',
            'not_formal_recommendation',
            'already_preprocessed_candidate',
            'no_dicom_job',
            'will_execute=false',
            'managed_workspace_only',
            'no_external_command_execution',
        ]
    else:
        message = 'Managed preprocessing plan generated; no DICOM preprocessing was executed'
        limitations = [
            'not_for_diagnosis',
            'shadow_only',
            'not_formal_recommendation',
            'no_dicom_read',
            'dry_run_only',
            'will_execute=false',
            'managed_workspace_only',
            'no_external_command_execution',
            'preprocessing_contract_ready',
        ]

    row = _persist_preprocess_preview(
        db,
        row,
        preprocessing_status=job_plan['job_state'],
        execution_mode=payload.execution_mode,
        dry_run=payload.dry_run,
        execute=payload.execute,
        candidate_kind=classification['candidate_kind'],
        job_plan=job_plan,
    )
    status_item = _status_item(row)
    return ImagingPreprocessResponseV1(
        status='planned',
        route='/imaging-inputs/{input_asset_id}/preprocess',
        dry_run=payload.dry_run,
        execute=payload.execute,
        execution_mode=payload.execution_mode,
        will_execute=False,
        job_id=job_plan['job_id'],
        job_state=job_plan['job_state'],
        managed_workspace=job_plan['managed_workspace'],
        expected_input_kind=job_plan['expected_input_kind'],
        candidate_kind=classification['candidate_kind'],
        error_code=None,
        message=message,
        expected_steps=job_plan['expected_steps'],
        command_plan=job_plan['command_plan'],
        expected_outputs=job_plan['expected_outputs'],
        safety_gate=job_plan['safety_gate'],
        item=status_item,
        limitations=limitations,
    )
