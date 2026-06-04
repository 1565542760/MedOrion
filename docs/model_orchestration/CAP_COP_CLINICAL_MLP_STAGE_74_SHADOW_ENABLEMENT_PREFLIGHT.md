# Stage 74 - CAP/COP Clinical MLP Shadow Enablement Preflight Checklist

## Purpose
This document is a readiness review for the eventual enablement of the CAP/COP clinical MLP controlled shadow path. It does **not** enable shadow execution. It records what is already in place, what still needs to be confirmed, and what must remain disabled until the next stage is explicitly approved.

## Executive Summary
Current status: **not ready for enablement yet**.

The disabled-by-default shadow skeleton is in place, but the enablement gate should remain closed until the remaining readiness gaps are closed and reviewed. The main rule is still: no live inference, no default/canary promotion, no recommendation write, and no case trace/evidence writes from the shadow path.

## 1. Shadow Switch
### Required Checks
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW` default is `false`.
- The switch is controlled only by backend configuration.
- Front-end parameters, LLM output, and ordinary request fields cannot bypass the switch.

### Current Status
- Default `false`: **satisfied**.
- Backend-config-controlled only: **satisfied**.
- No bypass from front end / LLM / request fields: **satisfied by design**.

### Gap / Risk
- The switch remains intentionally off. Any future enablement still requires explicit review and a controlled rollout plan.

## 2. Artifact / Weight
### Required Checks
- The CAP/COP fold5 artifact must be explicitly identified.
- Artifact hash must be registered.
- No scanning, copying, moving, or guessing of other `.pth/.pt/.onnx/.ckpt/.safetensors` files.
- The fold5 artifact must remain unread at this stage.
- No `torch.load`.

### Current Status
- Fold5 candidate is known and tracked as the shadow candidate: **satisfied**.
- Artifact hash formally locked for enablement: **needs final confirmation before Stage 75**.
- No scanning / copying / moving / guessing other model files: **satisfied**.
- No fold5 load: **satisfied**.
- No `torch.load`: **satisfied**.

### Gap / Risk
- Stage 75 should not open the gate until the artifact hash / provenance review is explicitly confirmed in the enablement checklist.

## 3. Model Registry
### Required Checks
- Clinical MLP model registry metadata is complete.
- `model_version_id` is explicit.
- Lifecycle remains non-default / non-canary for shadow candidate.
- A shadow eligibility marker or equivalent operational allowlist is clarified if needed.

### Current Status
- `model_version_id` is explicit: **satisfied**.
- Lifecycle is not default / not canary: **satisfied**.
- Registry metadata completeness for enablement: **partially satisfied**.
- Need for a dedicated `shadow_candidate` / allowlist marker: **open question**.

### Gap / Risk
- If Stage 75 wants a stronger operational gate, it may need an explicit shadow eligibility marker or a documented allowlist rule.

## 4. Model Input Schema
### Required Checks
- `cap_cop_clinical_feature_set_v1` is explicit.
- The 36 CAP/COP task-related attributes are queryable.
- `Striated_shadow.1` is preserved.
- `clinical_mlp_cap_cop_input_schema_v1` is available.
- `clinical_feature_mapping` is sufficient for real-case input mapping.

### Current Status
- `cap_cop_clinical_feature_set_v1`: **satisfied**.
- 36 attributes queryable: **satisfied**.
- `Striated_shadow.1` preserved: **satisfied**.
- `clinical_mlp_cap_cop_input_schema_v1`: **satisfied**.
- `clinical_feature_mapping` available: **partially satisfied / needs final enablement review**.

### Gap / Risk
- The mapping contract exists, but enablement should verify it against the exact production case data surfaces and missing-value handling path.

## 5. Required Feature Missing Handling
### Required Checks
- Missing-value consultation is available.
- Explicit default strategy is available.
- `insufficient_data_for_assessment` is available.
- No silent fallback.

### Current Status
- Missing-value consultation: **satisfied**.
- Explicit default strategy: **satisfied**.
- `insufficient_data_for_assessment`: **satisfied**.
- No silent fallback: **satisfied**.

### Gap / Risk
- None blocking for the shadow skeleton, but Stage 75 must verify the same behavior under the exact shadow enablement flow.

## 6. Shadow Audit
### Required Checks
- `shadow_inference_runs` / `shadow_inference_outputs` exist.
- Read APIs are available.
- Disabled runs are visible.
- Output behavior is clear.
- No recommendations / trace_events / evidence_nodes / evidence_edges are written.

### Current Status
- Tables exist: **satisfied**.
- Read APIs exist: **satisfied**.
- Disabled runs are visible: **satisfied**.
- Output behavior is clear: **satisfied**.
- No recommendation / case trace / evidence writes: **satisfied**.

### Gap / Risk
- None blocking. This is a strong readiness point.

## 7. Runtime Safety
### Required Checks
- CPU-only or equivalent safe runtime posture is defined.
- `batch=1` and `concurrency=1` are defined or planned.
- Timeout policy is defined or planned.
- `no_grad` / `eval` posture is defined or planned.
- A separate GPU-disable control exists if needed.

### Current Status
- CPU-only posture: **partially satisfied / plan exists**.
- `batch=1` and `concurrency=1`: **partially satisfied / plan exists**.
- Timeout policy: **partially satisfied / plan exists**.
- `no_grad` / `eval` posture: **gap if enablement is attempted**.
- Separate GPU-disable env control: **gap if enablement is attempted**.

### Gap / Risk
- Stage 75 should not enable shadow execution until the runtime safety envelope is explicit and testable.

## 8. Front-End Safety Display
### Required Checks
- Shadow audit page is viewable.
- `not_for_diagnosis` is explicit.
- Shadow output is not presented as a formal recommendation.
- Model input pages / small-model pages show clear warnings if needed.

### Current Status
- Shadow audit page viewability: **satisfied**.
- `not_for_diagnosis` explicit: **satisfied**.
- Shadow output not shown as formal recommendation: **satisfied**.
- Input page / small-model page warnings: **partially satisfied / may need copy review**.

### Gap / Risk
- If enablement happens later, UX copy should be checked once more to avoid any impression of live diagnosis.

## 9. Rollback
### Required Checks
- Disabling `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW` is sufficient to turn the path off.
- Existing shadow audit is preserved.
- Model metadata is preserved.
- Recommendation, trace, and evidence are not affected.

### Current Status
- Disable switch is sufficient: **satisfied**.
- Preserve shadow audit: **satisfied**.
- Preserve model metadata: **satisfied**.
- No effect on recommendation / trace / evidence: **satisfied**.

## 10. Stage 75 Recommendation
### If readiness is still incomplete
The missing items to close before any real shadow enablement are:
- Final artifact hash / provenance confirmation.
- Final confirmation that the input mapping covers the real target case surfaces.
- Runtime safety knobs for CPU-only, batch=1, concurrency=1, and timeout.
- A clear no-grad/eval operational posture.
- Optional explicit shadow eligibility marker or documented allowlist rule.
- Any front-end wording review for the shadow display.

### If readiness becomes sufficient
Stage 75 should focus on:
- A final enablement review checklist.
- A tightly bounded controlled activation plan.
- A rollback verification plan.
- A safety check that still forbids default/canary/live recommendation paths.

### Explicitly not recommended
- Do not jump directly to default.
- Do not jump directly to canary.
- Do not enable live inference.

## Decision
Current recommendation: **do not enable yet**.

The system is close, but the safe choice is to keep the switch off until the remaining enablement checks are explicitly closed and reviewed.
