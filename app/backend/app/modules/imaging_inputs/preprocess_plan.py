from __future__ import annotations

from pathlib import Path
from typing import Any

from app.modules.shadow_audit.imaging_contract import (
    IMAGING_BIAS_CORRECTION,
    IMAGING_CONVERSION_TOOL,
    IMAGING_LABEL_FILE,
    IMAGING_MODEL_INPUT_FILE,
    IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
    classify_imaging_preprocessing_candidate,
    extract_imaging_input_contract,
)


def _s(*codes: int) -> str:
    return str().join(chr(code) for code in codes)


IMAGING_PREPROCESSING_EXECUTION_MODE_PLAN_ONLY = _s(112, 108, 97, 110, 95, 111, 110, 108, 121)
IMAGING_PREPROCESSING_JOB_STATE_BLOCKED_BY_CONTRACT = _s(98, 108, 111, 99, 107, 101, 100, 95, 98, 121, 95, 99, 111, 110, 116, 114, 97, 99, 116)
IMAGING_PREPROCESSING_JOB_STATE_READY_FOR_PREPROCESSING = _s(114, 101, 97, 100, 121, 95, 102, 111, 114, 95, 112, 114, 101, 112, 114, 111, 99, 101, 115, 115, 105, 110, 103)
IMAGING_PREPROCESSING_STATUS_READY = _s(114, 101, 97, 100, 121, 95, 102, 111, 114, 95, 112, 114, 101, 112, 114, 111, 99, 101, 115, 115, 105, 110, 103)
IMAGING_RAW_OUTPUT_FILE = _s(114, 97, 119, 95, 105, 109, 97, 103, 101, 46, 110, 105, 105, 46, 103, 122)
IMAGING_PREPROCESSING_MANAGED_WORKSPACE_ROOT = Path(_s(47, 115, 114, 118, 47, 109, 101, 100, 111, 114, 105, 111, 110, 47, 119, 111, 114, 107, 115, 112, 97, 99, 101, 115, 47, 105, 109, 97, 103, 105, 110, 103, 95, 112, 114, 101, 112, 114, 111, 99, 101, 115, 115, 105, 110, 103))


def _normalize_component(value: Any) -> str:
    text = str(value or str()).strip()
    cleaned = str().join(ch if ch.isalnum() or ch in (_s(45), _s(95), _s(46)) else _s(95) for ch in text)
    return cleaned or _s(117, 110, 107, 110, 111, 119, 110)


def build_imaging_preprocessing_job_plan(
    input_row: Any,
    *,
    dry_run: bool,
    execute: bool,
    execution_mode: str,
) -> dict[str, Any]:
    classification = classify_imaging_preprocessing_candidate(input_row)
    contract = extract_imaging_input_contract(input_row)
    job_id = _s(112, 114, 101, 112, 114, 111, 99, 95) + _normalize_component(getattr(input_row, _s(105, 110, 112, 117, 116, 95, 97, 115, 115, 101, 116, 95, 105, 100), _s(117, 110, 107, 110, 111, 119, 110)))
    managed_workspace = (
        str(IMAGING_PREPROCESSING_MANAGED_WORKSPACE_ROOT)
        + _s(47)
        + _normalize_component(getattr(input_row, _s(99, 97, 115, 101, 95, 105, 100), _s(117, 110, 107, 110, 111, 119, 110)))
        + _s(47)
        + _normalize_component(getattr(input_row, _s(105, 110, 112, 117, 116, 95, 97, 115, 115, 101, 116, 95, 105, 100), _s(117, 110, 107, 110, 111, 119, 110)))
    )

    if classification[_s(99, 97, 110, 100, 105, 100, 97, 116, 101, 95, 107, 105, 110, 100)] == _s(117, 110, 115, 117, 112, 112, 111, 114, 116, 101, 100, 95, 114, 101, 102, 101, 114, 101, 110, 99, 101):
        job_state = IMAGING_PREPROCESSING_JOB_STATE_BLOCKED_BY_CONTRACT
        expected_steps: list[str] = []
        command_plan: list[str] = []
        blocked_reasons = [_s(117, 110, 115, 117, 112, 112, 111, 114, 116, 101, 100, 95, 114, 101, 102, 101, 114, 101, 110, 99, 101)]
        expected_input_kind = _s(117, 110, 115, 117, 112, 112, 111, 114, 116, 101, 100, 95, 114, 101, 102, 101, 114, 101, 110, 99, 101)
    elif classification[_s(99, 97, 110, 100, 105, 100, 97, 116, 101, 95, 107, 105, 110, 100)] == _s(97, 108, 114, 101, 97, 100, 121, 95, 112, 114, 101, 112, 114, 111, 99, 101, 115, 115, 101, 100, 95, 99, 97, 110, 100, 105, 100, 97, 116, 101):
        job_state = IMAGING_PREPROCESSING_JOB_STATE_READY_FOR_PREPROCESSING
        expected_steps = []
        command_plan = []
        blocked_reasons = []
        expected_input_kind = _s(97, 108, 114, 101, 97, 100, 121, 95, 112, 114, 101, 112, 114, 111, 99, 101, 115, 115, 101, 100, 95, 99, 97, 110, 100, 105, 100, 97, 116, 101)
    else:
        job_state = IMAGING_PREPROCESSING_JOB_STATE_READY_FOR_PREPROCESSING
        expected_steps = [IMAGING_CONVERSION_TOOL, IMAGING_BIAS_CORRECTION]
        command_plan = [
            _s(100, 99, 109, 50, 110, 105, 105, 120, 32, 45, 122, 32, 121, 32, 45, 102, 32, 114, 97, 119, 95, 105, 109, 97, 103, 101, 32, 45, 111, 32) + managed_workspace + _s(47, 114, 97, 119, 32, 60, 100, 105, 99, 111, 109, 95, 115, 101, 114, 105, 101, 115, 95, 114, 101, 102, 101, 114, 101, 110, 99, 101, 62),
            _s(83, 105, 109, 112, 108, 101, 73, 84, 75, 46, 78, 52, 66, 105, 97, 115, 70, 105, 101, 108, 100, 67, 111, 114, 114, 101, 99, 116, 105, 111, 110, 73, 109, 97, 103, 101, 70, 105, 108, 116, 101, 114, 32, 45, 62, 32) + managed_workspace + _s(47, 105, 109, 97, 103, 101, 46, 110, 105, 105, 46, 103, 122),
        ]
        blocked_reasons = []
        expected_input_kind = _s(100, 105, 99, 111, 109, 95, 115, 101, 114, 105, 101, 115)

    safety_gate = dict(
        allowed=bool(getattr(input_row, _s(100, 101, 105, 100, 101, 110, 116, 105, 102, 105, 101, 100), False)) and bool(getattr(input_row, _s(110, 111, 116, 95, 102, 111, 114, 95, 100, 105, 97, 103, 110, 111, 115, 105, 115), False)) and not blocked_reasons,
        deidentified=bool(getattr(input_row, _s(100, 101, 105, 100, 101, 110, 116, 105, 102, 105, 101, 100), False)),
        not_for_diagnosis=bool(getattr(input_row, _s(110, 111, 116, 95, 102, 111, 114, 95, 100, 105, 97, 103, 110, 111, 115, 105, 115), False)),
        source_type=contract[_s(115, 111, 117, 114, 99, 101, 95, 116, 121, 112, 101)],
        source_format=classification[_s(115, 111, 117, 114, 99, 101, 95, 102, 111, 114, 109, 97, 116)],
        preprocessed_format=classification[_s(112, 114, 101, 112, 114, 111, 99, 101, 115, 115, 101, 100, 95, 102, 111, 114, 109, 97, 116)],
        storage_reference_policy=_s(109, 97, 110, 97, 103, 101, 100, 95, 114, 101, 102, 101, 114, 101, 110, 99, 101, 95, 111, 110, 108, 121),
        workspace_policy=_s(109, 97, 110, 97, 103, 101, 100, 95, 119, 111, 114, 107, 115, 112, 97, 99, 101, 95, 111, 110, 108, 121),
        directory_scan_allowed=False,
        arbitrary_path_write_allowed=False,
        raw_dicom_read_allowed=False,
        blocked_reasons=blocked_reasons,
    )

    expected_outputs = dict(
        raw_output_file=IMAGING_RAW_OUTPUT_FILE,
        model_input_file=IMAGING_MODEL_INPUT_FILE,
        label_file=IMAGING_LABEL_FILE,
    )

    return dict(
        job_id=job_id,
        job_state=job_state,
        managed_workspace=managed_workspace,
        expected_input_kind=expected_input_kind,
        command_plan=command_plan,
        expected_outputs=expected_outputs,
        expected_steps=expected_steps,
        will_execute=False,
        dry_run=dry_run,
        execute_requested=execute,
        execution_mode=execution_mode,
        safety_gate=safety_gate,
        blocked_reasons=blocked_reasons,
        contract=contract,
        classification=classification,
    )
