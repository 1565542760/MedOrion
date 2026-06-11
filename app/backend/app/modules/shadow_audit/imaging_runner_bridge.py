from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings

LOGGER = logging.getLogger("app.shadow_audit.imaging_runner_bridge")

IMAGING_RUNNER_PYTHON_PATH = Path(settings.cap_cop_clinical_mlp_runner_python_path)
IMAGING_RUNNER_SCRIPT_PATH = Path("/srv/medorion/app/model-runners/cap_cop_imaging_resnet18_runner.py")
IMAGING_RUNNER_TIMEOUT_SECONDS = max(int(settings.cap_cop_clinical_mlp_shadow_timeout_seconds), 300)


@dataclass(frozen=True)
class RunnerInvocationResult:
    command: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    payload: dict[str, Any] | None
    error_code: str | None = None
    error_message: str | None = None


def _build_env() -> dict[str, str]:
    return {
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONUNBUFFERED": "1",
        "PYTHONNOUSERSITE": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def _runner_missing_reason() -> tuple[str, str] | None:
    if not IMAGING_RUNNER_PYTHON_PATH.exists():
        return "runner_unavailable", f"Runner Python not found at {IMAGING_RUNNER_PYTHON_PATH}"
    if not IMAGING_RUNNER_SCRIPT_PATH.exists():
        return "runner_unavailable", f"Runner script not found at {IMAGING_RUNNER_SCRIPT_PATH}"
    return None


def invoke_imaging_runner(payload: dict[str, Any] | None = None, *, check_artifact: bool = False) -> RunnerInvocationResult:
    missing = _runner_missing_reason()
    command = [str(IMAGING_RUNNER_PYTHON_PATH), str(IMAGING_RUNNER_SCRIPT_PATH)]
    if check_artifact:
        command.append("--check-artifact")
    if missing is not None:
        error_code, error_message = missing
        LOGGER.warning("Imaging runner unavailable: %s", error_message)
        return RunnerInvocationResult(
            command=command,
            exit_code=None,
            stdout="",
            stderr="",
            payload=None,
            error_code=error_code,
            error_message=error_message,
        )

    stdin_text = None
    if not check_artifact:
        stdin_text = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":"))

    try:
        completed = subprocess.run(
            command,
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=IMAGING_RUNNER_TIMEOUT_SECONDS,
            check=False,
            cwd=str(IMAGING_RUNNER_SCRIPT_PATH.parent),
            env=_build_env(),
        )
    except subprocess.TimeoutExpired:
        LOGGER.warning("Imaging runner timed out after %s seconds", IMAGING_RUNNER_TIMEOUT_SECONDS)
        return RunnerInvocationResult(
            command=command,
            exit_code=None,
            stdout="",
            stderr="",
            payload=None,
            error_code="runner_timeout",
            error_message=f"Runner timed out after {IMAGING_RUNNER_TIMEOUT_SECONDS} seconds",
        )
    except FileNotFoundError as exc:
        LOGGER.warning("Imaging runner unavailable: %s", exc)
        return RunnerInvocationResult(
            command=command,
            exit_code=None,
            stdout="",
            stderr="",
            payload=None,
            error_code="runner_unavailable",
            error_message=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        LOGGER.exception("Unexpected failure invoking imaging runner")
        return RunnerInvocationResult(
            command=command,
            exit_code=None,
            stdout="",
            stderr="",
            payload=None,
            error_code="runner_unavailable",
            error_message=str(exc),
        )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if not stdout.strip():
        return RunnerInvocationResult(
            command=command,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            payload=None,
            error_code="invalid_runner_response",
            error_message="Runner returned empty stdout",
        )

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return RunnerInvocationResult(
            command=command,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            payload=None,
            error_code="invalid_runner_response",
            error_message=f"Runner returned invalid JSON: {exc.msg}",
        )

    if not isinstance(parsed, dict):
        return RunnerInvocationResult(
            command=command,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            payload=None,
            error_code="invalid_runner_response",
            error_message="Runner response must be a JSON object",
        )

    return RunnerInvocationResult(
        command=command,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
        payload=parsed,
    )
