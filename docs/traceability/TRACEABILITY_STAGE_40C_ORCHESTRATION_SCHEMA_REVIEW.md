# TRACEABILITY STAGE 40C ORCHESTRATION SCHEMA REVIEW

Date: 2026-06-02
Scope: quick re-review of the orchestration audit schema candidate after Stage 40B fixes

## Verdict
Pass.

The Stage 40B candidate resolves the previously identified migration/ORM drift and now presents a coherent five-table orchestration audit schema. The candidate remains audit-only, keeps the case trace/evidence graph untouched, and maintains the correct boundary between orchestration bookkeeping and clinical evidence.

## Findings

### 1) Are the five tables still worth keeping?
Yes.

The five-table shape should be retained:
- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

They remain the right decomposition for run-level records, step-level execution, backend invocations, conflict summaries, and human-readable orchestration summaries.

### 2) Stage 40R must-fix items
The previously identified must-fix items are now resolved in the reviewed files:

1. `orchestration_runs.result_json`
   - Present in both ORM and migration.
   - The run-level result snapshot is now aligned.

2. `orchestration_steps.step_index`
   - Present in both ORM and migration.
   - The ordering field now has a matching index: `ix_orchestration_steps_run_step_index(orchestration_run_id, step_index)`.

3. `llm_summaries` field scheme
   - The current unified shape uses `summary_text`, `summary_json`, `step_id`, `agent_invocation_id`, and `model_version_id`.
   - This is consistent across ORM and migration and fits the Stage 39 audit boundary.

### 3) Is the `llm_summaries` scheme acceptable for Stage 39 boundary?
Yes.

The unified `summary_text / summary_json / step_id / agent_invocation_id / model_version_id` shape is appropriate because it keeps the table squarely in orchestration audit territory:
- it stores the orchestration-produced summary artifact,
- it preserves the source step and invocation lineage,
- it retains model governance linkage where available,
- and it does not itself become a case trace/evidence object.

That is the right boundary for Stage 39 and Stage 40.

### 4) FK and index review
The FK and index strategy is broadly good and not overbuilt for the current stage.

Useful access paths remain:
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

The `ix_orchestration_steps_run_step_index(orchestration_run_id, step_index)` index is a good addition because it supports stable step ordering within a run without forcing the system to infer order from timestamps.

### 5) Boundary with case trace/evidence
Still correct.

This candidate does not write to `trace_events`, `evidence_nodes`, or `evidence_edges`. That is exactly what we want.

The following orchestration outputs may later be promoted into case trace/evidence, but only as a narrow clinical subset:
- final recommendation / summary intended for review
- key agent outputs that materially influenced the recommendation
- conflict summaries that changed reasoning
- doctor confirmation requests
- doctor-confirmed overrides or rejections

The following must remain orchestration audit only:
- ordinary step scheduling details
- endpoint health checks
- retry and transport noise
- internal routing details
- adapter plumbing records
- timing jitter without clinical consequence

### 6) Runtime safety fields
Adequate.

`runtime_stub`, `error_code`, and `error_detail_json` are sufficient to keep the skeleton from being misread as real clinical inference, provided the runtime and UI continue to label stub behavior clearly.

### 7) Should this enter restricted apply approval?
Yes, reasonable to discuss now.

At this point the previous drift has been corrected, and the schema candidate is coherent enough for a limited apply approval discussion. That discussion should still remain cautious and should not imply immediate application.

## Must-fix items
- None identified in the Stage 40B-reviewed state.

## Suggested modifications
1. Keep the five-table set as-is.
2. Keep the current FK and index strategy.
3. Preserve the audit-only boundary; do not bridge to case trace/evidence yet.
4. Maintain explicit `runtime_stub` labeling in runtime outputs and logs.

## Apply recommendation
- It is now reasonable to enter restricted apply approval discussion.
- Do not apply yet until the approval path explicitly authorizes it.

## Constraints confirmed
- No schema changes were executed.
- No Alembic execution was performed.
- No Nginx enablement.
- No real-model connection.
- No training.
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations.
