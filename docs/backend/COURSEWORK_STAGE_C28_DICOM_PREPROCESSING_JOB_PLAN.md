# Coursework Stage C28: DICOM Preprocessing Job Plan + Controlled Execution Skeleton

## Verdict
- No new table is required at this stage.
- The existing `case_imaging_inputs` table can carry the preprocessing job preview and contract state in `provenance_json` and `quality_flags_json`.
- This stage is about a safe job boundary, not a real DICOM batch pipeline.

## What We Already Have
- Metadata-only DICOM series registration.
- `GET /api/v1/imaging-inputs/{input_asset_id}/preprocessing-status`.
- A contract helper that distinguishes DICOM series references, preprocessed NIfTI references, and unsupported inputs.
- A preexisting shadow boundary that forbids raw DICOM from going directly into imaging shadow execution.

## Goal of Stage C28
- Express a preprocessing job preview.
- Support `dry_run=true` / `execution_mode=contract_check`.
- Record whether a reference is a DICOM series candidate, an already-preprocessed NIfTI candidate, or an unsafe reference.
- Reject inputs that are not safe for the preprocessing contract.
- Avoid any real `dcm2niix` or N4 execution.

## Non Goals
- No batch preprocessing.
- No real DICOM file reads.
- No `dcm2niix` execution.
- No SimpleITK N4 execution.
- No creation of a real `image.nii.gz`.
- No training.
- No inference.
- No recommendation, trace, or evidence writes.
- No frontend changes.

## Contract Fields
The preprocessing preview should continue to use the existing imaging input row and express state in JSON metadata.

Recommended state fields:
- `source_format = dicom_series`
- `preprocessed_format = nifti_nii_gz`
- `preprocessing_script = dcmtonii_N4.py`
- `conversion_tool = dcm2niix`
- `bias_correction = N4BiasFieldCorrection`
- `raw_output_file = raw_image.nii.gz`
- `model_input_file = image.nii.gz`
- `label_file = label.nii.gz`
- `preprocessing_status = pending / ready_for_preprocessing / already_preprocessed_candidate / not_implemented`
- `preprocessing_execution_mode = contract_check / dry_run`
- `preprocessing_dry_run = true`
- `preprocessing_will_execute = false`
- `preprocessing_requested_at`
- `preprocessing_candidate_kind`
- `expected_steps`
- `expected_preprocessed_format`
- `expected_raw_output_file`
- `expected_model_input_file`
- `expected_label_file`

## API Skeleton
### 1. Register DICOM series metadata
- `POST /api/v1/cases/{case_id}/imaging-inputs/dicom-series`

Purpose:
- Register a DICOM-series reference as metadata.
- Keep the row deidentified and not-for-diagnosis.
- Store the preprocessing contract metadata.

### 2. Dry-run / contract-check preprocessing preview
- `POST /api/v1/imaging-inputs/{input_asset_id}/preprocess`

Request controls:
- `dry_run=true`
- `execution_mode=contract_check` or `dry_run`

Behavior:
- If the input is a DICOM series candidate, return a `ready_for_preprocessing` preview.
- If the input is already preprocessed NIfTI, return an `already_preprocessed_candidate` preview and do not treat it as a DICOM job.
- If the input is neither a DICOM series candidate nor a preprocessed NIfTI candidate, reject it with a clear error.
- No file read, no conversion, no N4, no new image file.

### 3. Read preprocessing status
- `GET /api/v1/imaging-inputs/{input_asset_id}/preprocessing-status`

Purpose:
- Surface the current preprocessing state, including any contract-check preview that was recorded in JSON metadata.

## Validation Rules
- DICOM series references are allowed as preprocessing candidates.
- DICOM directories must not be processed as real files in this stage.
- `.nii` / `.nii.gz` inputs are already-preprocessed candidates, not DICOM jobs.
- The skeleton must refuse any request that implies a real preprocessing execution.
- `label.nii.gz` is a training / evaluation reference only and never a shadow inference input.

## Dry-Run Response Shape
A dry-run or contract-check response should include:
- `dry_run = true`
- `execution_mode = contract_check` or `dry_run`
- `will_execute = false`
- `candidate_kind = dicom_series` or `already_preprocessed_candidate`
- `expected_steps = [dcm2niix, N4BiasFieldCorrection]` for DICOM series candidates
- `expected_steps = []` for already-preprocessed candidates
- a `preprocessing_status` of `ready_for_preprocessing` or `already_preprocessed_candidate`
- a clear message explaining that no real preprocessing occurred

## Why No New Table Yet
The job preview can be represented with the existing imaging input row because:
- this stage is about contract enforcement, not queueing
- the row already has JSON fields for provenance and quality flags
- we do not yet need job retry, worker ownership, or job history

A future table would only be justified if we later need:
- job retries
- worker claims
- multi-step preprocessing history
- failure audits separate from imaging input provenance

## Relationship to Shadow Execution
- The imaging shadow bridge must only accept preprocessed NIfTI references or synthetic fixtures.
- DICOM series metadata is not shadow-ready.
- This preprocessing skeleton sits one layer before imaging shadow execution.

## Relationship to Access / Trace / Evidence
- Access audit may record read or registration actions if needed.
- Trace and evidence tables must not be used for preprocessing registration.
- This stage is still contract / job preview design, not clinical inference.

## Next Step Recommendation
- Keep the preprocessing skeleton dry-run only.
- If the course later needs actual worker execution, introduce a separate preprocessing job table and worker contract then.
- Do not jump from metadata-only registration straight to real preprocessing.

## Compliance Boundary
- No real DICOM reads.
- No `dcm2niix` execution.
- No N4 execution.
- No real image creation.
- No training.
- No inference.
- No recommendation, trace, or evidence writes.
- No default / canary shadow enablement.
- No model file scanning, copying, or moving.
