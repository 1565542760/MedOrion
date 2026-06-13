# Coursework Stage C31: DICOM Preprocessing Execution Plan

## Verdict
- This stage stays in the design / execution-skeleton lane.
- Default behavior remains `dry_run=true` and `execute=false`.
- No real DICOM read, no `dcm2niix`, no N4, and no real `image.nii.gz` creation in this stage.
- The existing `case_imaging_inputs` table remains the metadata anchor.

## What We Already Have
- Metadata-only DICOM series registration.
- A preprocessing status contract that can distinguish DICOM series candidates, already-preprocessed NIfTI candidates, and unsafe references.
- A contract helper that rejects raw DICOM or directory-like references from entering imaging shadow execution.
- Case-scoped imaging access control.

## Goal of Stage C31
- Define the minimum execution skeleton needed to move from contract-check / dry-run into a future controlled single-case preprocessing flow.
- Keep the current coursework posture safe: describe execution, but do not actually run it.
- Make the future boundary explicit enough that a later stage can implement one controlled execution path without guessing path policy, cleanup policy, or audit policy.

## Non Goals
- No batch preprocessing.
- No real DICOM reads.
- No `dcm2niix` execution.
- No SimpleITK N4 execution.
- No creation of a real `image.nii.gz`.
- No training.
- No inference.
- No recommendation, trace, or evidence writes.
- No default / canary shadow enablement.
- No model file scanning, copying, or moving.
- No frontend changes.

## Recommended Execution Shape
### 1. Job request
A future preprocessing execution request should be explicit about:
- `input_asset_id`
- `case_id`
- `patient_id`
- `trace_id`
- `dry_run`
- `execute`
- `execution_mode`
- `source_format`
- `preprocessed_format`
- `requested_steps`
- `allow_managed_workspace_only`

### 2. Job state
Recommended state values for a future execution skeleton:
- `not_implemented`
- `pending`
- `ready_for_preprocessing`
- `running`
- `completed`
- `failed`
- `canceled`
- `blocked_by_contract`

### 3. Working directory policy
A future real execution must use a managed workspace only, for example a job-scoped directory under a controlled runtime root.
- Workspace must be created per job.
- Workspace must not be inferred from the input path.
- Workspace must never be a user-controlled arbitrary path.
- Workspace cleanup must be deterministic.

### 4. Output path policy
A future real execution should write only to a managed output directory within the job workspace.
- `raw_image.nii.gz` is an intermediate output.
- `image.nii.gz` is the only model-ready output.
- `label.nii.gz` is a label reference only and must never be treated as shadow input.
- No arbitrary output path should be accepted from the caller.

### 5. Failure cleanup policy
A future execution path must define cleanup rules up front.
- Partial outputs should be removed or quarantined.
- Temporary files should not be left in shared directories.
- Failed jobs should preserve only lightweight metadata and error codes.
- Failed jobs must not pretend that a model-ready `image.nii.gz` exists.

### 6. Audit fields
A future job execution record or metadata payload should preserve:
- `preprocessing_status`
- `execution_mode`
- `dry_run`
- `execute`
- `requested_at`
- `started_at`
- `completed_at`
- `error_code`
- `error_message`
- `source_format`
- `preprocessed_format`
- `preprocessing_script`
- `conversion_tool`
- `bias_correction`
- `raw_output_file`
- `model_input_file`
- `label_file`
- `workspace_root`
- `output_root`
- `cleanup_state`
- `not_for_diagnosis`
- `deidentified`

## Safe Gate for Future Real Execution
Before a real execution can happen, all of the following must be true:
- `deidentified=true`
- `not_for_diagnosis=true`
- the input is a DICOM series reference, not a raw directory scan
- the storage reference is in an allowed managed path or managed object reference
- the output path is inside a managed workspace
- no arbitrary path write is allowed
- no unknown directory scan is allowed
- the caller explicitly opted into `execute=true`
- the job is still single-case and single-run, not a batch flow

## Recommended Execution Skeleton Behavior
A future endpoint or service method should behave like this:
1. Re-read the imaging contract from `case_imaging_inputs`.
2. If `dry_run=true` or `execute=false`, return a plan only.
3. If the contract is unsafe, reject with a contract error.
4. If a later stage enables execution, create a job workspace and record a job state transition.
5. Only then call `dcm2niix` and N4 in a tightly controlled environment.

## Relationship to Existing C21/C28 Contracts
- C21 expressed the DICOM preprocessing contract.
- C28 added a dry-run / contract-check job preview.
- C31 defines the minimal execution skeleton that a future stage can activate.
- C31 does not add a new table because the existing imaging input JSON fields are still enough for coursework-level planning.

## Relationship to `case_imaging_inputs`
The table continues to act as the source of truth for the imaging reference plus preprocessing contract metadata.
Recommended JSON keys for a future execution-ready record:
- `preprocessing_status`
- `preprocessing_execution_mode`
- `preprocessing_dry_run`
- `preprocessing_execute`
- `preprocessing_requested_at`
- `preprocessing_started_at`
- `preprocessing_completed_at`
- `preprocessing_error_code`
- `preprocessing_error_message`
- `preprocessing_workspace_root`
- `preprocessing_output_root`
- `preprocessing_cleanup_state`
- `preprocessing_will_execute`

## Why No New Table Yet
A dedicated preprocessing job table would be justified only if we later need:
- retries
- worker claims
- multiple execution attempts
- execution logs separate from imaging provenance
- long-lived queue state

For now, the coursework can stay lighter by keeping job planning in JSON metadata.

## Suggested Future Endpoint Contract
If execution is later approved, a future endpoint could look like:
- `POST /api/v1/imaging-inputs/{input_asset_id}/preprocess`

The request would need to distinguish:
- `dry_run`
- `contract_check`
- `execute`

The response would need to say whether the job is only planned or actually executed.

## Failure Taxonomy
Recommended error codes for future execution work:
- `preprocessing_not_implemented`
- `preprocessing_not_allowed`
- `imaging_input_not_preprocessed`
- `imaging_input_not_dicom_series`
- `workspace_not_available`
- `output_path_not_allowed`
- `preprocessing_failed`
- `preprocessing_canceled`
- `preprocessing_cleanup_failed`

## Next Step Recommendation
- Keep the current stage as a plan plus skeleton boundary.
- Do not add real execution yet.
- If a future stage wants actual preprocessing, it should add one controlled execution path with a managed workspace and explicit cleanup semantics.

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
