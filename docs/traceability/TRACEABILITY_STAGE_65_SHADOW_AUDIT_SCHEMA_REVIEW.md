# MedOrion Stage 65 - Shadow Audit Schema Review

Date: 2026-06-04

Scope:
- Review only
- No source changes
- No database changes
- No Alembic execution
- No Nginx enablement
- No model loading
- No training
- No inference execution
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations

Reviewed artifacts:
- `/home/sygxdg/MedOrion/docs/backend/SHADOW_AUDIT_STAGE_64_SCHEMA_PLAN.md`
- `/home/sygxdg/MedOrion/app/backend/alembic/versions/7a3b2d1f4c60_stage65_shadow_audit_schema.py`
- `/home/sygxdg/MedOrion/app/backend/app/db/models.py`

## Review verdict

Stage 65 is **approved at the review level**.

The candidate schema is a coherent shadow-audit layer. It stores shadow runs and outputs separately from the case trace/evidence chain, which is exactly the right boundary for shadow outputs.

## Findings

### 1. `shadow_inference_runs` field coverage

The run table is sufficiently expressive for the current shadow-audit purpose.
It captures:
- `shadow_run_id`
- `trace_id`
- `case_id`
- `patient_id`
- `model_version_id`
- `artifact_hash`
- `adapter_code`
- `model_input_schema_id`
- `input_snapshot_id`
- `status`
- `runtime_env_json`
- `runtime_stub`
- `not_for_diagnosis`
- `started_at`
- `completed_at`
- `duration_ms`
- `error_code`
- `error_detail_json`

This is enough to audit shadow execution without pretending it is a diagnostic path.

### 2. `shadow_inference_outputs` field coverage

The output table is also sufficiently expressive for the current stage.
It captures:
- `output_id`
- `shadow_run_id`
- `trace_id`
- `case_id`
- `model_version_id`
- `prediction_raw_json`
- `prediction_probability_json`
- `candidate_label`
- `confidence_json`
- `uncertainty_json`
- `limitations_json`
- `input_quality_flags_json`
- `created_at`

This is enough for replayable shadow comparison without entering the formal diagnosis chain.

### 3. FK review

The FK design is reasonable:
- `case_id -> cases.id`
- `patient_id -> patients.id`
- `model_version_id -> model_versions.id`
- `shadow_run_id -> shadow_inference_runs.shadow_run_id`

That set is sufficient for audit linkage. The output table does not need its own `patient_id` because the run table already anchors the case/patient pair.

### 4. Index review

The index set is appropriate for audit access paths:
- `trace_id`
- `case_id`
- `patient_id`
- `model_version_id`
- `status`
- `started_at`
- `(case_id, started_at)`
- `(trace_id, model_version_id)`

The chosen indexes support trace lookup, case review, version comparison, and time-ordered audit review without being obviously overbuilt.

### 5. Shadow boundary vs case trace/evidence

The audit boundary is correct.
Shadow results should not, by default, enter:
- doctor-facing recommendation flow
- case evidence chain
- formal diagnosis claims

Normal shadow calls, failures, timings, adapter details, and other operational information should stay in shadow audit storage.
Only an explicitly approved clinical summary may later be referenced in case trace/evidence, and even then only as a summary reference rather than a full execution dump.

### 6. Additional fields

No additional fields are required for approval at this review stage.
However, the following are reasonable future enhancements if the project wants slightly richer provenance:
- `disease_task`
- `adapter_version`
- `model_input_schema_version`
- `shadow_mode`
- `trigger_source`
- `preprocess_artifact_ref`

These are useful, but not required to make the current schema acceptable.

## Must-fix items

None found at review level.

## Suggested items

- Consider adding `adapter_version` or `shadow_mode` later if the team wants more explicit comparison metadata.
- Consider a `status` + `started_at` composite index only if operational query patterns show a need.
- Keep any future clinical summaries that arise from shadow runs out of the default case evidence path unless separately approved.

## Boundary ruling

Shadow audit is audit-only storage.
It should remain separate from case trace/evidence by default.

Allowed to remain in shadow audit:
- ordinary shadow calls
- failed shadow calls
- latency and timing
- adapter runtime detail
- retries
- comparison metadata
- error detail payloads

May only enter case trace/evidence later if explicitly approved and clinically meaningful:
- concise summary
- clinically relevant comparison result
- doctor-facing note derived from approved review

Must not enter case trace/evidence by default:
- raw shadow prediction payloads
- operational logs
- adapter plumbing details
- non-clinical timing noise

## Apply recommendation

The schema is suitable for a **restricted apply approval** discussion.
There are no must-fix items identified in this review.

## Compliance confirmation

This review did not change the database, did not execute Alembic, did not load a model, did not train, did not run inference, did not enable Nginx, and did not inspect, copy, move, or guess any `.pth/.pt/.onnx/.ckpt/.safetensors` files.
