
# MedOrion Stage 39 Orchestration Audit Migration Contract

## 1. Why Stage 39 Starts With a Migration Contract

Stage 38 intentionally shipped a no-schema orchestration skeleton: request/response orchestration planning, unified execution entrypoints, and structured logging, but **no persistent orchestration audit tables**. That was the right constraint for two reasons.

First, the live system still needed a safe proof of shape before persistence. We already had a stable Agent Gateway, a model-service stub, and case trace/evidence pipelines. Adding tables too early would have forced schema decisions before the orchestration semantics were proven.

Second, orchestration audit data is not just another operational log stream. It needs to answer questions such as: which agent was selected, which step failed, which mode was used, whether a conflict existed, and what summary was ultimately surfaced to a doctor. Those semantics need to be designed before any table is introduced, otherwise the project risks storing shallow logs that cannot support traceability, approval, rollback, or review.

This document therefore defines the migration contract first, so the eventual Alembic work can be deliberate, minimal, and aligned with traceability.

## 2. Recommended Table Structure Draft

The Stage 39 target is a small orchestration audit schema with five core tables:

- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

The intent is to keep orchestration audit separate from case trace/evidence, while still allowing selected outputs to be referenced later by case review or clinical audit flows.

### 2.1 `orchestration_runs`

Purpose: the top-level orchestration execution record.

Suggested fields:
- `id`
- `trace_id`
- `case_id`
- `patient_id`
- `orchestration_run_id`
- `mode`
- `requested_task`
- `status`
- `started_at`
- `completed_at`
- `duration_ms`
- `runtime_stub`
- `payload_json`
- `result_json`
- `error_code`
- `error_detail_json`
- `idempotency_key`
- `created_at`
- `updated_at`

Notes:
- `trace_id` is the top-level correlation key.
- `orchestration_run_id` should be stable and externally visible.
- `payload_json` can store the normalized request snapshot.
- `result_json` can store the final summary skeleton.

### 2.2 `orchestration_steps`

Purpose: one row per step in the orchestration plan and execution path.

Suggested fields:
- `id`
- `trace_id`
- `case_id`
- `patient_id`
- `orchestration_run_id`
- `step_id`
- `step_type`
- `step_index`
- `agent_code`
- `agent_version`
- `status`
- `started_at`
- `completed_at`
- `duration_ms`
- `payload_json`
- `output_json`
- `error_code`
- `error_detail_json`
- `runtime_stub`
- `created_at`
- `updated_at`

Notes:
- `step_id` should be stable and can be exposed in logs and APIs.
- `agent_version` may be nullable for stub-only flows or when the orchestration delegates before model selection.
- `payload_json` should capture the step-level request shape.
- `output_json` should store the agent output or a summarized proxy.

### 2.3 `agent_invocations`

Purpose: normalized record of each call into an agent backend, especially `capcop_agent` today.

Suggested fields:
- `id`
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
- `started_at`
- `completed_at`
- `duration_ms`
- `payload_json`
- `response_json`
- `error_code`
- `error_detail_json`
- `runtime_stub`
- `created_at`
- `updated_at`

Notes:
- This table is the practical bridge between orchestration and model-service.
- `endpoint_id` is optional now but useful later if the gateway becomes registry-backed.
- `endpoint_url` should only store explicit configuration or resolved registry value, never inferred file paths.

### 2.4 `orchestration_conflicts`

Purpose: capture disagreement, ambiguity, or multi-agent conflict summaries.

Suggested fields:
- `id`
- `trace_id`
- `case_id`
- `patient_id`
- `orchestration_run_id`
- `conflict_id`
- `mode`
- `status`
- `conflict_type`
- `summary`
- `resolution_strategy`
- `conflict_payload_json`
- `runtime_stub`
- `created_at`
- `updated_at`

Notes:
- This table should store only actual conflicts or conflict-like summaries, not every step.
- It should not be used for generic scheduling output.

### 2.5 `llm_summaries`

Purpose: store the natural-language orchestration summary or recommendation text that would eventually be shown to a reviewer or doctor.

Suggested fields:
- `id`
- `trace_id`
- `case_id`
- `patient_id`
- `orchestration_run_id`
- `summary_id`
- `summary_type`
- `summary_text`
- `recommendation_text`
- `limitations_text`
- `source_step_id`
- `source_agent_invocation_id`
- `status`
- `runtime_stub`
- `payload_json`
- `created_at`
- `updated_at`

Notes:
- This table is where the final natural-language product of orchestration can live.
- It should remain distinct from clinical recommendation records until a later contract explicitly bridges them.

## 3. Field Guidance and Cross-Cutting Conventions

Across all orchestration tables, the following fields should be treated as common anchors when relevant:

- `id`
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
- `started_at`
- `completed_at`
- `duration_ms`
- `payload_json`
- `runtime_stub`
- `error_code`
- `error_detail_json`

Recommended conventions:
- Use `*_json` for flexible payloads and snapshots.
- Use explicit timestamps rather than inferring timing from logs.
- Keep `runtime_stub` visible in the row so reviewers can distinguish staged behavior from real behavior.
- Avoid embedding file-system artifact assumptions in any field.

## 4. FK and Index Recommendations

Key foreign-key relationships to consider in the future migration:

- `orchestration_steps.orchestration_run_id -> orchestration_runs.orchestration_run_id` or `orchestration_runs.id`
- `agent_invocations.orchestration_run_id -> orchestration_runs.orchestration_run_id` or `orchestration_runs.id`
- `agent_invocations.step_id -> orchestration_steps.step_id`
- `orchestration_conflicts.orchestration_run_id -> orchestration_runs.orchestration_run_id`
- `llm_summaries.orchestration_run_id -> orchestration_runs.orchestration_run_id`

Suggested indexes:
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

Indexing guidance:
- `trace_id` and `orchestration_run_id` should be first-class indexes because they are the main audit join points.
- `case_id` and `patient_id` should be indexed for clinician-facing filtering.
- `agent_code` and `model_version_id` should be indexed for gateway and registry review workflows.
- `status` and `started_at` should support operational triage and timeline queries.

## 5. What May Eventually Flow Into Case Trace/Evidence

Only a narrow subset of orchestration outputs should later be eligible for case trace/evidence linkage:

- Final recommendation or summary intended for clinical review
- Key agent output that materially influenced the final recommendation
- Conflict summary that changed the path of reasoning
- Doctor confirmation request that requires a user decision
- Doctor-confirmed override or rejection that modifies the final recommendation

The later bridge into case trace/evidence should preserve clinical meaning and should be explicit about who generated or confirmed each item.

## 6. What Should Not Flow Into Case Trace/Evidence

The following orchestration details should stay out of case trace/evidence:

- Ordinary step scheduling details
- Endpoint health checks
- Retry noise or transport-level diagnostics
- Non-clinical internal routing details
- Pure adapter plumbing records
- Internal timing jitter with no clinical consequence

These belong in orchestration audit tables or logs, not in the clinical case graph.

## 7. no_silent_fallback and agent_unavailable Audit Expectations

`no_silent_fallback` should remain a first-class contract rule.

For audit purposes:
- If an agent is unavailable, record the structured error code and the failing step or invocation.
- If a fallback is explicitly chosen by policy, record it as an explicit resolution, not as a hidden retry.
- If the system aborts because a candidate is unsupported, record the capability mismatch clearly.

Recommended error fields:
- `error_code`
- `error_detail_json`
- `status`
- `runtime_stub`

Recommended error codes to preserve:
- `agent_unavailable`
- `unsupported_agent_task`
- `unsupported_modality`
- `orchestration_timeout`
- `orchestration_plan_invalid`

## 8. Mode Mapping Guidance

The orchestration modes should map to audit shape as follows:

- `single_agent`: one run, one step, one agent invocation
- `parallel_agents`: one run, multiple steps/invocations with a parallel intent
- `serial_agents`: one run, multiple steps/invocations in sequence
- `triage_then_specialist`: at least two conceptual steps, typically triage then specialist
- `conflict_aware_summary`: multiple outputs may be summarized into one conflict-aware summary row

The mode should be stored on the run record and, when useful, echoed into step or conflict records.

## 9. Lifecycle Event Tables: Recommendation Only

Stage 39 does **not** create lifecycle event tables yet, but they may be useful later.

Suggested future tables:
- `model_lifecycle_events`
- `agent_lifecycle_events`

Recommendation:
- Do not build these in Stage 39.
- Keep them as a later phase if model governance or agent governance needs a durable audit trail separate from operational runs.

## 10. Downgrade and Migration Risk

Risks to call out before any Alembic work:
- Adding orchestration tables introduces new joins and migration ordering concerns.
- Retrofitting historical orchestration logs may not be necessary and could become noisy.
- If schemas for future JSON payloads are over-constrained too early, the system may become brittle.
- Downgrade from a filled orchestration table set may be lossy if downstream data starts referencing run IDs externally.

Mitigation guidance:
- Keep the first migration minimal.
- Start with nullable JSON payloads where appropriate.
- Prefer explicit enums only where semantics are stable.
- Avoid hard dependency on case trace/evidence until a later contract defines the bridge.

## 11. Stage 40 Recommendation

Stage 40 should be the first Alembic review candidate for this orchestration audit schema.

Suggested Stage 40 focus:
- Draft the Alembic revision for the five orchestration audit tables.
- Include only the minimum FKs and indexes needed for safe lookup.
- Keep the case trace/evidence bridge out of scope unless explicitly approved.
- Add downgrade notes that explain any unavoidable data-loss risk.
- Re-review against runtime behavior from Stage 38 so the migration reflects actual execution patterns, not guesswork.

In short: Stage 39 defines the contract; Stage 40 can turn it into a reviewable migration draft.
