# Coursework Stage C35 One-Click CAP/COP Shadow Workflow Endpoint

## Goal
Provide a single backend orchestration endpoint for CAP/COP shadow workflow. It must reuse the C33 readiness gate and may either preview the workflow or execute only the branches that are actually ready.

## Endpoint
`POST /api/v1/cases/{case_id}/cap-cop-shadow/workflow`

## Request
- `mode`: `preview | execute`
- `requested_branches`: optional list of `clinical_mlp`, `imaging_resnet18`, `multimodal_resnet18`
- `dry_run_label`: optional
- `not_for_diagnosis=true`
- `shadow_only=true`

Default branch selection is all three branches when `requested_branches` is omitted.

## Preview behavior
- Reuses the C33 readiness gate.
- Does not call any runner.
- Does not write shadow rows.
- Does not write recommendation, trace, or evidence.
- Returns an execution plan with branch items marked `planned` for ready branches and `skipped` for blocked or unrequested branches.

## Execute behavior
- Reuses the C33 readiness gate first.
- Only runs branches with `can_run=true` and included in `requested_branches`.
- No silent fallback.
- Blocked branches are returned as `skipped` with reasons.
- Only `shadow_inference_runs` / `shadow_inference_outputs` may be written by the executed branch helpers.
- No recommendation, trace, or evidence writes are allowed.

## Branch rules
### clinical_mlp
- Must have a latest ready clinical snapshot.
- The snapshot must be `validation_status=ready_for_inference` and `current_assessment_status=ready_for_inference`.
- If not ready, skip it.

### imaging_resnet18
- Must have a ready imaging input.
- DICOM series is only usable after preprocessing is completed.
- Already preprocessed `.nii/.nii.gz` or synthetic/demo inputs are eligible.
- Must remain `deidentified=true` and `not_for_diagnosis=true`.

### multimodal_resnet18
- Requires both clinical and imaging readiness.
- The clinical snapshot and imaging input must belong to the same case/patient context.
- If either side is missing or blocked, the branch is skipped.

## Response
The response includes:
- `workflow_run_id`
- `mode`
- `overall_status`
- `case_id`
- `patient_id`
- `branches[]`
- `checked_at`
- `limitations[]`

Each branch item includes:
- `branch`
- `status` (`planned`, `executed`, `skipped`, `failed`)
- `shadow_run_id`
- `output_id`
- `candidate_label`
- `probabilities`
- `disabled_reasons`
- `limitations`

## Safety and limitations
All workflow outputs must preserve the shadow-only safety boundary:
- `shadow_only`
- `not_for_diagnosis`
- `not_formal_recommendation`
- `probability_uncalibrated`
- `requires_doctor_review`
- `requires_quality_review_before_clinical_use`

Preview responses additionally include:
- `preview_only`
- `no_runner_invocation`
- `no_trace_or_evidence`

## Non-goals
- No model loading.
- No DICOM/NIfTI reads.
- No preprocessing execution.
- No recommendation writes.
- No trace/evidence writes.
- No default/canary enablement.
- No schema or Alembic changes.

## Validation notes
The endpoint should be validated against a fixture-ready case where the clinical and imaging branches are ready, but the multimodal branch is only runnable when the selected clinical snapshot satisfies the exact 36-feature artifact-order contract. If the clinical payload is incomplete or schema-unverified, preview must mark multimodal as blocked/skipped and execute must skip that branch without invoking the runner. Preview must leave counts unchanged. Execute should write only the branch shadow artifacts for ready branches.
