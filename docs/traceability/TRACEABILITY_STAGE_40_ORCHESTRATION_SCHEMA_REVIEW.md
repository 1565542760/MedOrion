# TRACEABILITY STAGE 40 ORCHESTRATION SCHEMA REVIEW

Date: 2026-06-02
Scope: quick traceability and quality review of the orchestration audit schema candidate

## Verdict
Conditional pass.

The Stage 40 candidate is directionally correct and keeps orchestration audit separate from case trace/evidence, but it is not yet ready for a limited apply approval because the migration and ORM are not fully aligned on several field-level shapes.

## Findings

### 1) Should the five tables be kept?
Yes.

The five-table shape remains the right audit boundary:
- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

They are still the right separation for run metadata, step flow, backend invocations, conflicts, and human-readable summaries.

No additional orchestration table is required for this stage, and none of these tables should be collapsed into the case graph.

### 2) Are the fields sufficient for audit?
Mostly yes.

The candidate covers the core audit anchors:
- `trace_id`
- `case_id`
- `patient_id`
- `orchestration_run_id`
- `step_id`
- `agent_invocation_id`
- `agent_code`
- `agent_version`
- `endpoint_id`
- `endpoint_url`
- `model_version_id`
- `status`
- `started_at` / `completed_at` / `duration_ms`
- `payload_json`
- `runtime_stub`
- `error_code`
- `error_detail_json`

That is enough for run-level and step-level traceability.

### 3) Must-fix migration / ORM alignment issues
Yes.

These are the items that should be corrected before any apply approval:

1. `orchestration_runs.result_json`
   - Present in the migration candidate.
   - Missing from the ORM model.
   - This should be aligned so the runtime contract and persistence model match.

2. `orchestration_steps.step_index`
   - Present in the migration contract draft, but missing from the ORM model.
   - If the team wants stable ordering beyond timestamps, this should be added to the ORM or intentionally removed from the migration.

3. `llm_summaries` field shape mismatch
   - The migration uses `summary_text`, `recommendation_text`, `limitations_text`, `source_step_id`, `source_agent_invocation_id`.
   - The ORM model uses `summary_text`, `summary_json`, `step_id`, `agent_invocation_id`, `model_version_id`.
   - This is the clearest drift in the current candidate and should be reconciled before apply approval.

These mismatches are not about case trace pollution; they are about keeping the code model and the migration contract in sync.

### 4) FK and index review
The FK and index strategy is broadly good.

The following are appropriate and useful:
- `trace_id`
- `case_id`
- `patient_id`
- `orchestration_run_id`
- `step_id`
- `agent_invocation_id`
- `agent_code`
- `model_version_id`
- `status`
- `started_at`

That said, the migration should avoid over-coupling where it is not needed. The current `model_version_id` references are acceptable because they preserve governance lineage, but the table shapes should stay focused on audit, not model lifecycle ownership.

### 5) Boundary with case trace/evidence
Clear and correct.

This migration candidate does not write to `trace_events`, `evidence_nodes`, or `evidence_edges`, and that is exactly right.

The following are legitimate future sources for case-level promotion, but not direct case evidence yet:
- final orchestration recommendation / summary
- key agent outputs that materially influenced the recommendation
- conflict summaries that changed the reasoning path
- doctor confirmation requests
- doctor-confirmed overrides or rejections

The following should remain orchestration audit only:
- step scheduling details
- endpoint health checks
- retry and transport noise
- internal routing details
- adapter plumbing records
- timing jitter with no clinical consequence

### 6) Runtime stub and error fields
Adequate for skeleton safety.

`runtime_stub`, `error_code`, and `error_detail_json` are sufficient to keep the skeleton from being mistaken for real clinical inference, provided the caller-facing UI or logs keep the stub labeling visible.

### 7) no_silent_fallback and audit semantics
Good.

The candidate preserves structured error and status fields and does not suggest hidden fallback behavior. That is the correct audit posture.

## Must-fix items
1. Align migration and ORM for `orchestration_runs.result_json`.
2. Align migration and ORM for `orchestration_steps.step_index`.
3. Reconcile `llm_summaries` field naming and shape between migration and ORM before apply approval.

## Suggested modifications
1. Keep the five-table set as-is.
2. Keep the current FK and index strategy, but ensure the ORM and migration use the same field names.
3. Prefer minimal JSON payloads for the first applied migration so the schema stays flexible.
4. Do not expose orchestration audit tables as case trace/evidence sources yet.

## Apply recommendation
- Do not enter limited apply approval yet.
- Stage 40 should first be revised to remove the ORM/migration drift, then re-reviewed.
- After that, a limited apply approval discussion would be reasonable.

## Constraints confirmed
- No schema changes were executed.
- No Alembic execution was performed.
- No Nginx enablement.
- No real-model connection.
- No training.
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations.
