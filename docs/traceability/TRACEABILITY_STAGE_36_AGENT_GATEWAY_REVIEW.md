# TRACEABILITY STAGE 36 AGENT GATEWAY REVIEW

Date: 2026-06-02
Scope: quick architecture / traceability review of the agent gateway skeleton

## Verdict
Pass.

The Stage 36 agent gateway behaves as a thin orchestration shell and keeps the correct provenance boundary. It validates capabilities, preserves the incoming trace_id, forwards requests to the model-service stub, and avoids creating a new case-level trace narrative that could blur provenance.

## Findings

### 1) Should the gateway write case trace_events now?
No. That is acceptable for the skeleton stage.

The gateway is currently a routing and validation layer, not the canonical source of clinical trace events. Writing case trace events here would risk duplicating or confusing provenance while the orchestration contract is still evolving.

### 2) Is logging-only agent invocation acceptable?
Yes, for Stage 36.

The backend logs already provide a useful operational trail for the skeleton. They are not a replacement for future audit tables, but they are sufficient for a stub-only gateway whose purpose is to validate the surface contract.

### 3) trace_id passthrough
Correct.

The gateway requires an incoming trace_id and forwards it unchanged. It does not mint a new trace_id and does not rewrite provenance, which is the right boundary for this stage.

### 4) agent_unavailable and no silent fallback
Good.

When the model-service is unavailable or times out, the gateway raises `agent_unavailable` with explicit backend details. That is preferable to silently switching agents or fabricating a successful result.

### 5) Stub registry sufficiency
Sufficient for the skeleton.

A single `capcop_agent` registry entry with supported diseases, tasks, modalities, endpoint, and health URL is enough to exercise the gateway contract and keep the surface readable.

### 6) Capability validation
Reasonable.

The gateway rejects unsupported agents, tasks, and modalities early. That helps prevent invalid calls from flowing downstream and keeps the stub boundary honest.

### 7) No new agent table
Acceptable for Stage 36.

Introducing a persistent agent table now would be premature. The skeleton is better served by a static registry until the orchestration model is finalized.

### 8) Stage 37 should design a dedicated orchestration audit model
Yes, recommended.

A future stage should likely define independent structures such as:
- `agent_invocations`
- `orchestration_runs`
- `orchestration_steps`
- `agent_lifecycle_events`

That is the right place to persist multi-agent lineage, step-level decisions, retries, and downstream effects.

### 9) Risk of contaminating case trace or bypassing model registry
Low in the current skeleton.

The gateway preserves trace_id, uses the existing model-service path, and does not claim to be a clinical inference engine. The main remaining risk is only future expansion, where we should make sure orchestration events stay separate from the core case trace until the contract is explicit.

## Must-fix items
- None for the current Stage 36 review scope.

## Recommendation
- Suitable for Git checkpoint.
- Stage 37 can take the next step and design a dedicated agent/orchestration audit contract.

## Constraints confirmed
- No schema changes.
- No Alembic execution.
- No Nginx enablement.
- No real-model connection.
- No training.
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations.
