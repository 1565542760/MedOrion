from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any, Sequence

from fastapi import HTTPException, UploadFile, status

from app.modules.imaging_inputs.preprocess_plan import IMAGING_PREPROCESSING_MANAGED_WORKSPACE_ROOT


def _normalize_component(value: Any) -> str:
    text = str(value or '').strip()
    cleaned = ''.join(ch if ch.isalnum() or ch in {'-', '_', '.'} else '_' for ch in text)
    return cleaned or 'unknown'


def _safe_path_under(root: Path, candidate: Path) -> bool:
    try:
        root_resolved = root.resolve()
        candidate_resolved = candidate.resolve()
    except OSError:
        return False
    return candidate_resolved == root_resolved or root_resolved in candidate_resolved.parents


def build_dicom_series_upload_workspace(case_id: str, input_asset_id: str) -> Path:
    return (
        IMAGING_PREPROCESSING_MANAGED_WORKSPACE_ROOT
        / _normalize_component(case_id)
        / _normalize_component(input_asset_id)
        / 'dicom_series'
    )


def persist_dicom_series_upload(upload_dir: Path, upload_files: Sequence[UploadFile]) -> list[dict[str, Any]]:
    if not upload_files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'invalid_upload_set', 'message': 'At least one DICOM file must be uploaded'},
        )

    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)
    upload_dir.mkdir(parents=True, exist_ok=False)

    seen_names: set[str] = set()
    manifest: list[dict[str, Any]] = []
    try:
        for upload in upload_files:
            filename = Path(upload.filename or '').name.strip()
            if not filename:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={'code': 'invalid_upload_filename', 'message': 'Each uploaded file must have a filename'},
                )
            if filename in seen_names:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={'code': 'duplicate_upload_filename', 'message': f'Duplicate uploaded filename: {filename}'},
                )
            seen_names.add(filename)

            target_path = upload_dir / filename
            if not _safe_path_under(upload_dir, target_path):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={'code': 'upload_path_violation', 'message': 'Uploaded file path is not allowed'},
                )

            digest = hashlib.sha256()
            size_bytes = 0
            with target_path.open('wb') as handle:
                while True:
                    chunk = upload.file.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    digest.update(chunk)
                    size_bytes += len(chunk)

            manifest.append(
                {
                    'filename': filename,
                    'content_type': upload.content_type,
                    'size_bytes': size_bytes,
                    'sha256': digest.hexdigest(),
                    'stored_path': str(target_path),
                }
            )
    except Exception:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise
    finally:
        for upload in upload_files:
            try:
                upload.file.close()
            except Exception:
                pass

    return manifest
