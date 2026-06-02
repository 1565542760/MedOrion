# TRACEABILITY STAGE 39 ORCHESTRATION AUDIT REVIEW

Date: 2026-06-02
Scope: quick traceability and quality review of the orchestration audit migration contract

## Verdict
Pass.

Stage 39 is a good contract-level step toward durable orchestration audit persistence. The document keeps orchestration audit separate from case trace/evidence, defines a reasonable five-table shape, and preserves the key safety rule that only clinically meaningful outputs may later be promoted into the case graph.

## Findings

### 1) Are the five tables necessary and boundary-clear?
Yes, with one nuance.

The five-table set is coherent for a first orchestration audit schema:
- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

They are distinct enough to keep run metadata, step execution, backend calls, conflict summaries, and human-readable summary text apart.

The only nuance is that `llm_summaries` should remain strictly an orchestration-audit record until a later bridge explicitly promotes a clinically relevant subset into the case graph. That is already stated well enough in the contract.

### 2) Are the fields sufficient for future persistence?
Yes.

The draft covers the key future anchors:
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
- `duration_ms`
- `payload_json`
- `runtime_stub`
- `error_code`
- `error_detail_json`

That is enough to support run-level auditing, step-level lineage, and backend invocation review.

### 3) FK and index guidance
Reasonable.

The suggested indexes on `trace_id`, `case_id`, `patient_id`, `orchestration_run_id`, `step_id`, `agent_invocation_id`, `agent_code`, `model_version_id`, `status`, and `started_at` are the right basic access paths for audit and review workflows.

The FK suggestions are also sensible as draft guidance. The only thing to keep flexible is whether the final migration anchors future relations on `id` or on the externally visible run/step identifiers; the contract allows either, which is practical at this stage.

### 4) Boundary with case trace/evidence
Clear and correctly constrained.

The contract explicitly keeps the following out of case trace/evidence:
- ordinary step scheduling details
- endpoint health checks
- retry noise or transport diagnostics
- non-clinical routing details
- adapter plumbing records
- internal timing jitter without clinical consequence

That is exactly the right boundary.

What may eventually flow into the case graph is also correctly narrowed to:
- final recommendation
- key agent outputs that materially influenced the recommendation
- conflict summaries that changed reasoning
- doctor confirmation requirements
- doctor-confirmed overrides or rejections

### 5) no_silent_fallback, agent_unavailable, timeout, retry, fallback
Adequate and auditable.

The contract is explicit that these conditions must remain visible and structured. That is important because orchestration systems can otherwise hide substitution or failure behind a clean final output.

### 6) Mode mapping
Usable.

The mode-to-shape mapping for single, parallel, serial, triage-then-specialist, and conflict-aware flows is enough to support a first migration contract and future review.

### 7) Stage 40 direction
Recommended.

Stage 40 should generate an Alembic review draft, not apply it.

At this point the contract is clear enough to translate into a reviewable migration proposal. The next step should be a schema draft with minimal FKs and indexes, reviewed against Stage 38 runtime behavior.

## Must-fix items
- None for the current Stage 39 review scope.

## Recommendation
- Suitable for Git checkpoint.
- Proceed to Stage 40 as an Alembic review draft stage.
- Do not apply migrations yet.
- Keep orchestration audit separate from case trace/evidence.

## Constraints confirmed
- No schema changes.
- No Alembic execution.
- No Nginx enablement.
- No real-model connection.
- No training.
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations.
