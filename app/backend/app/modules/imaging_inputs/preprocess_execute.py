
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import Any

from fastapi import HTTPException, status

from app.modules.shadow_audit.imaging_contract import (
    IMAGING_BIAS_CORRECTION,
    IMAGING_CONVERSION_TOOL,
    IMAGING_MODEL_INPUT_FILE,
    IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
    IMAGING_PREPROCESSING_SCRIPT,
    IMAGING_PREPROCESSING_STATUS_COMPLETED,
    IMAGING_RAW_OUTPUT_FILE,
    IMAGING_SOURCE_FORMAT_DICOM_SERIES,
    extract_imaging_input_contract,
)

MRI3D_PYTHON_CANDIDATES = (
    Path('/home/sygxdg/miniconda3/envs/MRI3D/bin/python3'),
    Path('/home/sygxdg/miniconda3/envs/MRI3D/bin/python'),
    Path('/usr/bin/python3'),
)
MRI3D_DCM2NIIX_CANDIDATES = (
    Path('/usr/local/bin/dcm2niix'),
    Path('/home/sygxdg/miniconda3/envs/MRI3D/bin/dcm2niix'),
    Path('/usr/bin/dcm2niix'),
)
MANAGED_WORKSPACE_ROOT = Path('/srv/medorion/workspaces/imaging_preprocessing')
ALLOWED_REAL_PREPROCESSING_SOURCE_TYPES = {'synthetic', 'demo', 'real_deidentified'}
DEFAULT_TIMEOUT_SECONDS = 1800


def _controlled_env() -> dict[str, str]:
    env = {
        'CUDA_VISIBLE_DEVICES': '',
        'OMP_NUM_THREADS': '1',
        'ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS': '1',
        'PYTHONNOUSERSITE': '1',
        'PATH': os.environ.get('PATH', ''),
    }
    return env


def _run_command(command: list[str], *, cwd: Path | None = None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=_controlled_env(),
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _resolve_tool(candidates: tuple[Path, ...], *, tool_name: str) -> Path:
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={'code': f'{tool_name}_unavailable', 'message': f'{tool_name} is not available in the controlled MRI3D runtime'},
    )


def _safe_path_under(root: Path, candidate: Path) -> bool:
    try:
        root_resolved = root.resolve()
        candidate_resolved = candidate.resolve()
    except OSError:
        return False
    return candidate_resolved == root_resolved or root_resolved in candidate_resolved.parents


def _n4_code() -> str:
    return dedent(
        """
        from pathlib import Path
        import sys
        import SimpleITK as sitk

        raw_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])

        image = sitk.ReadImage(str(raw_path))
        image = sitk.Cast(image, sitk.sitkFloat32)
        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        corrector.SetMaximumNumberOfIterations([50, 50, 30, 20])
        corrected = corrector.Execute(image)
        sitk.WriteImage(corrected, str(output_path))
        """
    ).strip()


def execute_controlled_single_demo_dicom_preprocessing(
    input_row: Any,
    job_plan: dict[str, Any],
    *,
    allow_real_preprocessing: bool,
    execution_mode: str,
) -> dict[str, Any]:
    contract = extract_imaging_input_contract(input_row)
    source_type = contract['source_type']
    source_format = contract['source_format']
    source_dir = Path(contract['storage_uri']).expanduser()
    if not allow_real_preprocessing or execution_mode != 'single_demo':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'execution_not_enabled', 'message': 'Real preprocessing is only enabled for explicit single-demo execution'},
        )
    if source_type not in ALLOWED_REAL_PREPROCESSING_SOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'imaging_input_source_type_not_allowed', 'message': 'Controlled real preprocessing is limited to synthetic/demo/deidentified inputs'},
        )
    if source_format != IMAGING_SOURCE_FORMAT_DICOM_SERIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'imaging_input_not_preprocessed', 'message': 'Controlled real preprocessing requires a DICOM series reference'},
        )
    if not bool(getattr(input_row, 'deidentified', False)) or not bool(getattr(input_row, 'not_for_diagnosis', False)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'imaging_input_safety_gate_failed', 'message': 'Controlled preprocessing requires deidentified=true and not_for_diagnosis=true'},
        )
    if not source_dir.exists() or not source_dir.is_dir():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'imaging_input_not_preprocessed', 'message': 'Controlled preprocessing requires an existing DICOM directory reference'},
        )

    workspace = Path(job_plan['managed_workspace'])
    if not _safe_path_under(MANAGED_WORKSPACE_ROOT, workspace):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'managed_workspace_policy_violation', 'message': 'Workspace must live under the managed imaging preprocessing root'},
        )
    raw_dir = workspace / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    raw_image_path = raw_dir / IMAGING_RAW_OUTPUT_FILE
    image_output_path = workspace / IMAGING_MODEL_INPUT_FILE
    dcm2niix_bin = _resolve_tool(MRI3D_DCM2NIIX_CANDIDATES, tool_name='dcm2niix')
    python_bin = _resolve_tool(MRI3D_PYTHON_CANDIDATES, tool_name='python')
    dcm2niix_cmd = [
        str(dcm2niix_bin),
        '-z', 'y',
        '-f', 'raw_image',
        '-o', str(raw_dir),
        str(source_dir),
    ]
    n4_cmd = [
        str(python_bin),
        '-c', _n4_code(),
        str(raw_image_path),
        str(image_output_path),
    ]

    try:
        dcm2niix_result = _run_command(dcm2niix_cmd, cwd=workspace)
        if not raw_image_path.exists():
            raise RuntimeError('dcm2niix_output_missing')
        n4_result = _run_command(n4_cmd, cwd=workspace)
        if not image_output_path.exists():
            raise RuntimeError('n4_output_missing')
    except HTTPException:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise RuntimeError(f'controlled_preprocessing_failed: {exc}') from exc

    return {
        'status': 'completed',
        'job_state': 'completed',
        'managed_workspace': str(workspace),
        'source_storage_uri': str(source_dir),
        'raw_output_uri': str(raw_image_path),
        'image_output_uri': str(image_output_path),
        'command_plan': [
            ' '.join(dcm2niix_cmd),
            f"{python_bin} -c <N4BiasFieldCorrection> {raw_image_path} {image_output_path}",
        ],
        'dcm2niix_stdout': dcm2niix_result.stdout,
        'dcm2niix_stderr': dcm2niix_result.stderr,
        'n4_stdout': n4_result.stdout,
        'n4_stderr': n4_result.stderr,
        'source_format': source_format,
        'preprocessed_format': IMAGING_PREPROCESSED_FORMAT_NIFTI_NII_GZ,
        'preprocessing_script': IMAGING_PREPROCESSING_SCRIPT,
        'conversion_tool': IMAGING_CONVERSION_TOOL,
        'bias_correction': IMAGING_BIAS_CORRECTION,
        'raw_output_file': IMAGING_RAW_OUTPUT_FILE,
        'model_input_file': IMAGING_MODEL_INPUT_FILE,
        'preprocessing_status': IMAGING_PREPROCESSING_STATUS_COMPLETED,
    }
