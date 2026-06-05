# Stage 95: Clinical MLP Fold5 Shadow Execution Next-Step Decision Package

## Current State
- Fold5 metadata/provenance is ready.
- Adapter alias governance is ready.
- allowlist is currently empty.
- shadow switch is false.
- no model loading has occurred.
- no torch.load has occurred.
- no real inference has occurred.
- no recommendation integration has occurred.

## Decision Options

### A. Pause
- Keep the governance baseline.
- Make no configuration changes.
- Perform no execution.

### B. Clean Config-Only Rehearsal
- Temporarily allowlist the fold5 model_version_id.
- Keep the shadow switch false.
- Verify eligibility now passes the allowlist and adapter gates.
- The next blocker may be input_insufficient or another metadata/input gate.
- Roll back the allowlist to empty after verification.
- No model load.

### C. Real Shadow Load Design Only
- Write a design for a one-shot CPU-only model load rehearsal.
- Do not execute it.
- Do not call torch.load yet.
- Prepare risk and rollback plans.

### D. One-Shot CPU-Only Shadow Load Rehearsal
- Requires separate explicit main-controller approval.
- Would read and load the model.
- Would still not write recommendations.
- Higher risk and not the default recommendation.

## Recommended Default
- Recommend B or C.
- Do not recommend D unless the main controller explicitly accepts the higher risk.
- A is acceptable if the user wants to pause.

## What B Would Prove
- The allowlist and adapter alias governance chain is clean.
- No model loading occurs.
- No torch.load occurs.
- No inference occurs.
- The path remains safe and controlled.

## What C Would Prepare
- Exact runtime plan.
- CPU-only execution.
- batch=1.
- concurrency=1.
- Timeout.
- no_grad.
- Eval mode.
- Artifact hash re-check before any future load.
- Shadow-audit-only flow.
- Rollback plan.

## What D Would Require
- Explicit approval.
- Exact artifact path.
- Confirmation to load the model.
- Confirmation that it remains not_for_diagnosis.
- Confirmation of no recommendation, trace, or evidence writes.
- Runtime kill and rollback plan.

## Go/No-Go Matrix
- A: no approval needed.
- B: approval to run a config-only rehearsal.
- C: approval to write a design only.
- D: strong explicit approval to load the model.

## Stage 96 Recommendation
- If A: update the project board and pause.
- If B: run a clean config-only rehearsal.
- If C: write the real shadow load design.
- If D: only after explicit approval, prepare a one-shot CPU-only load rehearsal plan.

## Final Guidance
Stage 95 is a decision package only. It does not authorize shadow enablement, model loading, or live execution. Any later step must still be explicit, governed, and fail closed.
