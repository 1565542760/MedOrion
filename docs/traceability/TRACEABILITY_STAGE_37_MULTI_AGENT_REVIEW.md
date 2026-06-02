# TRACEABILITY STAGE 37 MULTI-AGENT REVIEW

Date: 2026-06-02
Scope: quick traceability and quality review of the multi-agent orchestration contract

## Verdict
Pass.

Stage 37 draws a largely correct boundary between orchestration audit and case-level clinical trace/evidence. It defines a dedicated orchestration vocabulary, keeps the scheduler as a bounded coordinator, and clearly states that the orchestration layer must not replace doctor decision-making, generate or replace trace IDs, or auto-train.

## Findings

### 1) Are `orchestration_runs`, `orchestration_steps`, `agent_invocations`, `orchestration_conflicts`, and `llm_summaries` suitable as a separate orchestration audit structure?
Yes.

These entities are the right abstraction for multi-agent orchestration because they capture run-level context, step-level ordering, agent calls, conflicts, and human-readable summaries without overloading the case trace model.

### 2) Boundary between orchestration audit and case trace/evidence
The boundary is mostly clear and should be kept that way.

- `orchestration_runs` and `orchestration_steps` belong in orchestration audit.
- `agent_invocations` belong in orchestration audit.
- `orchestration_conflicts` belong primarily in orchestration audit, with only the clinically relevant summary or doctor-action requirement promoted into case trace.
- `llm_summaries` belong in orchestration audit, while only the summary outcome that directly affects a recommendation or doctor action should be reflected in the case trace/evidence graph.

This avoids the common failure mode of dumping every agent step into the clinical evidence chain.

### 3) What must enter case trace?
The case trace should receive only the clinically meaningful outputs, especially:
- final recommendation
- key agent outputs that materially influenced the recommendation
- conflict summary when it changes or explains the recommendation
- doctor-confirmation-required signals
- doctor-confirmed overrides or rejections

Intermediate orchestration bookkeeping should stay in orchestration audit.

### 4) Conflict handling
Adequate.

The contract correctly preserves `supports`, `contradicts`, `uncertain`, and `needs_doctor_confirmation`. That is enough to support conflict-aware routing without pretending conflicts never happened.

### 5) LLM scheduler boundary
Safe enough for the skeleton contract.

The scheduler is allowed to propose a plan, but it may not:
- replace doctor decisions
- generate or replace `trace_id`
- bypass approval policy
- auto-train or self-update
- silently choose unapproved agents or models

That is the right constraint set for a governed coordinator.

### 6) Failure, retry, fallback semantics
Good and auditable.

The contract is explicit about `no_silent_fallback`, `agent_unavailable`, timeout, retry, and fallback visibility. That is important because multi-agent systems can otherwise hide substitution or partial failure behind a glossy final answer.

### 7) Public interoperability profile
Acceptable as an adapter layer only.

OpenAPI, JSON Schema, Agent Card or A2A-like metadata, FHIR, DICOMweb, Model Card, and MLflow-like metadata are useful interoperability surfaces, but they must remain adapters. They must not override MedOrion trace/evidence rules, approval gates, or safety constraints.

### 8) Stage 38 implementation shape
Recommend a no-schema skeleton first.

Stage 38 should first prove the orchestration flow, request/response boundaries, logging, and trace promotion behavior without creating tables yet. Once the skeleton behavior is stable, the table design can be finalized with much less risk.

## Must-fix items
- None for the Stage 37 contract review scope.

## Recommended follow-up
- Proceed to Stage 38 as a no-schema backend orchestration skeleton.
- Keep orchestration audit separate from case trace/evidence.
- Later, add tables only if the skeleton flow and promotion rules are stable.

## Constraints confirmed
- No schema changes.
- No Alembic execution.
- No Nginx enablement.
- No real-model connection.
- No training.
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations.
