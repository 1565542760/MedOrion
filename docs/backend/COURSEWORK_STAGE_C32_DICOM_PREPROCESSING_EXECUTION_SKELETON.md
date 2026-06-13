# Coursework Stage C32: DICOM Preprocessing Execution Skeleton

## Verdict
- This stage adds a managed preprocessing execution skeleton.
- Default behavior remains `dry_run=true` and `execute=false`.
- No real DICOM read, no `dcm2niix`, no N4, and no real `image.nii.gz` creation are allowed in this stage.
- The existing `case_imaging_inputs` row remains the source of truth for imaging provenance and preprocessing metadata.

## What C32 Adds
- A job plan that can be attached to a DICOM-series imaging input.
- A managed workspace path derived from the case and input asset.
- A command plan that describes the intended `dcm2niix` and N4 steps without executing them.
- A clear `execute=true` rejection path so the skeleton cannot silently become a real worker.

## Job Request Shape
A future request or plan call should carry:
- `input_asset_id`
- `case_id`
- `patient_id`
- `trace_id`
- `dry_run`
- `execute`
- `execution_mode`

Recommended execution modes:
- `contract_check`
- `dry_run`
- `plan_only`

## Job State Taxonomy
Recommended job states for the skeleton:
- `not_implemented`
- `pending`
- `ready_for_preprocessing`
- `running`
- `completed`
- `failed`
- `canceled`
- `blocked_by_contract`

## Managed Workspace Policy
- Every preprocessing plan gets a job-scoped managed workspace.
- The workspace path is derived from the case and input asset, not from a caller-provided arbitrary path.
- The workspace lives under a controlled runtime root.
- No user-supplied directory may be used as the write destination.
- No directory scan is permitted to discover workspaces or outputs.

## Output Path Policy
- `raw_image.nii.gz` is an intermediate output only.
- `image.nii.gz` is the model-ready output.
- `label.nii.gz` is label-reference metadata only and must not enter the inference payload.
- Output paths are fixed by the contract and must remain inside the managed workspace.
- Arbitrary output writes are forbidden.

## Command Plan
The skeleton records the intended steps only:
1. `dcm2niix -z y -f raw_image -o <managed_workspace>/raw <dicom_series_reference>`
2. `SimpleITK.N4BiasFieldCorrectionImageFilter -> <managed_workspace>/image.nii.gz`

These are only planned strings in this stage. They must not be executed here.

## Safety Gate
A plan is only considered valid if all of the following are true:
- `deidentified=true`
- `not_for_diagnosis=true`
- the source is a controlled DICOM-series reference
- the source is not treated as a raw directory scan
- the workspace is managed
- arbitrary path writes are forbidden
- directory scanning is forbidden
- raw DICOM reads are forbidden
- external commands are not executed in this stage

## `execute=true` Behavior
- `execute=true` is explicitly not enabled in this stage.
- A request with `execute=true` must return `execution_not_enabled` or an equivalent blocked response.
- The job plan may still be persisted as metadata, but no external command is run.

## State / Metadata Storage
The skeleton continues to use `case_imaging_inputs.provenance_json` and `quality_flags_json` for job-plan metadata.
Recommended keys:
- `preprocessing_job_id`
- `preprocessing_job_state`
- `preprocessing_managed_workspace`
- `preprocessing_expected_input_kind`
- `preprocessing_command_plan`
- `preprocessing_expected_outputs`
- `preprocessing_safety_gate`
- `preprocessing_execute`
- `preprocessing_dry_run`
- `preprocessing_execution_mode`
- `preprocessing_will_execute`
- `preprocessing_requested_at`

## Failure / Blocked Handling
- Inputs that do not qualify as DICOM series or already-preprocessed NIfTI candidates should be rejected as `blocked_by_contract`.
- If a later stage ever enables real execution, failed jobs must clean up or quarantine partial outputs.
- This stage does not create real output files, so cleanup is only metadata-level.

## Relationship to Earlier Coursework Stages
- C21 defined the DICOM preprocessing contract.
- C28 added the dry-run / contract-check skeleton.
- C31 defined the minimal execution boundary and the managed workspace policy.
- C32 instantiates that boundary in backend code while still preventing real external command execution.

## Relationship to `case_imaging_inputs`
- The table remains the anchor for imaging provenance and preprocessing metadata.
- No new table is needed yet.
- A future job table would only be justified if retries, worker claims, or multi-step execution history become necessary.

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
- No frontend changes.
