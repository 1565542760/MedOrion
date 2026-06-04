# Stage 75 - CAP/COP Clinical MLP Shadow Enablement Gap Closure Plan

## Purpose
This document closes the gap between the Stage 74 preflight checklist and any future decision to enable `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW`. It does **not** enable shadow execution. It defines what is still missing, what module should own each gap, and what kind of follow-up review is needed before the switch can ever be opened.

## Executive Position
Current recommendation: **keep the shadow switch disabled**.

Stage 72 established a disabled-by-default controlled shadow skeleton. Stage 73 documented the operating handbook. Stage 74 showed that most safety and contract pieces exist, but enablement still needs a few explicit closures before any controlled activation is safe.

## 1. Artifact Hash / Provenance Gap
### Current Understanding
The CAP/COP fold5 candidate is already tracked as the shadow candidate and the model registry metadata stores artifact-related fields in `artifact_ref_json`.

### What Still Needs Final Closure
Before enablement, the following fields must be explicitly reviewed and frozen as the authoritative artifact record:
- `artifact_uri`
- `artifact_hash`
- `hash_algorithm`
- `file_size_bytes`
- `model_version_id`
- `adapter_code`
- `registered_at`
- `registered_by`

### Ownership
- Primary owner: `model_registry`
- Supporting owner: `shadow_audit`
- Review owner: orchestration / model onboarding review thread

### Required Action
- Do **not** re-hash the file in Stage 75.
- Do **not** open or load `.pth`.
- Do **not** scan, copy, move, or guess any other model file.
- If the artifact identity needs a final sign-off, capture it as a review checklist item and keep the actual enablement gated.

### Gap Status
- Metadata is present, but enablement should still require an explicit provenance confirmation step.

## 2. Clinical Feature Mapping Gap
### Current Understanding
The current CAP/COP task-level feature set is `cap_cop_clinical_feature_set_v1` and it contains 36 CAP/COP task-related clinical attributes, including `Striated_shadow.1`. The model-level input schema `clinical_mlp_cap_cop_input_schema_v1` is already available in the backend skeleton.

### What Still Needs Final Closure
The real enablement path must confirm that the mapping from clinical case data to model input can reliably cover the intended production surfaces:
- clinical observations
- lab results
- EMR / structured table sources
- missing-value consultation path
- explicit default strategy path
- `insufficient_data_for_assessment` path

### Ownership
- Primary owner: `model_input`
- Supporting owner: `shadow_audit`
- Review owner: CAP/COP clinical owner / onboarding review

### Required Action
- Keep `Striated_shadow.1` preserved exactly.
- Keep `no_silent_fallback` as a hard rule.
- Ensure missing required features still go through only the allowed paths:
  - missing-value consultation
  - explicit default strategy
  - `insufficient_data_for_assessment`

### Gap Status
- The mapping skeleton exists.
- Final enablement should still validate the mapping against the exact real case data surfaces and the expected missing-value behavior.

## 3. Runtime Safety Gap
### Current Understanding
The current skeleton is intentionally disabled and audit-only. A future enablement still needs an explicit runtime safety envelope.

### Stage 76-Level Runtime Safety Plan
The enablement path should define the following runtime controls before the switch can ever be opened:
- CPU-only execution posture
- `batch=1`
- `concurrency=1`
- explicit timeout budget
- `no_grad` posture
- `eval` mode posture
- GPU disable strategy via configuration

### Ownership
- Primary owner: backend runtime / configuration
- Supporting owner: shadow audit service
- Review owner: backend release gate

### Recommended Configuration Draft
Suggested future config items, for documentation / later implementation review only:
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false` by default
- `CAP_COP_CLINICAL_MLP_SHADOW_DEVICE=cpu`
- `CAP_COP_CLINICAL_MLP_SHADOW_BATCH_SIZE=1`
- `CAP_COP_CLINICAL_MLP_SHADOW_CONCURRENCY=1`
- `CAP_COP_CLINICAL_MLP_SHADOW_TIMEOUT_SECONDS=10`
- `CAP_COP_CLINICAL_MLP_SHADOW_NO_GRAD=true`
- `CAP_COP_CLINICAL_MLP_SHADOW_EVAL_MODE=true`
- `CAP_COP_CLINICAL_MLP_SHADOW_DISABLE_GPU=true`

### Gap Status
- The plan exists.
- The runtime safety controls are not yet a fully enforced enablement gate.

## 4. Shadow Eligibility Marker / Allowlist Gap
### Question
Do we need an explicit `shadow_eligible` marker / allowlist, or is the combination of lifecycle state + artifact metadata + backend config enough?

### Recommendation
Use a **three-part control model**:
1. **Model registry lifecycle state** to exclude non-eligible versions.
2. **Artifact metadata** to prove the artifact identity and provenance.
3. **Backend config allowlist** to control which model versions or adapters are permitted to run shadow.

### Why This Is Better Than Any Single Control
- Lifecycle state alone is not enough to prevent a misconfigured enablement.
- Artifact metadata alone is not enough to choose runtime activation.
- Backend config alone is not enough to capture provenance and model intent.
- The front end and LLM must remain incapable of opening the switch.

### Ownership
- Primary owner: model registry + backend config
- Supporting owner: shadow audit service
- Review owner: backend release gate

### Gap Status
- A dedicated allowlist is **recommended** for future enablement.
- This does not need to be exposed as a front-end control.

## 5. Front-End Safety Messaging Gap
### Current Understanding
The shadow audit UI already exists, but the wording can be made safer before any future enablement.

### Recommended Messaging
Future front-end copy should explicitly say:
- `not_for_diagnosis`
- `shadow only`
- `not a formal recommendation`
- `not a doctor replacement`

### Where Future Copy Review Would Matter
- model input pages
- small-model pages
- shadow audit pages
- any place that shows a shadow result or preview

### Gap Status
- Current display is acceptable for disabled-by-default operation.
- Before any future enablement, a short copy review is still recommended.

## 6. What Stage 75 Is Closing
Stage 75 is not enabling the shadow switch. It is closing the documentation and control gaps so that a later stage can safely decide whether to enable it.

Stage 75 should confirm that:
- artifact provenance is explicitly approved
- feature mapping is sufficiently exact for the intended cases
- runtime controls are explicit and testable
- the eligibility gate cannot be bypassed by LLM or front-end input
- the front end clearly communicates non-diagnostic usage

## 7. What Stage 76 Should Do
If Stage 75 is judged sufficiently complete, Stage 76 should be limited to one of these narrowly scoped tasks:
- runtime safety config skeleton
- eligibility gate skeleton
- final enablement readiness review

Stage 76 should **not**:
- enable live inference
- promote to default
- promote to canary
- write recommendations
- write case trace/evidence

## 8. Decision Summary
### Recommend to Keep Disabled
Yes. The safest current choice is to keep `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false`.

### What Is Still Missing Before Any Future Enablement
- final artifact provenance sign-off
- final mapping validation against real case surfaces
- explicit runtime controls
- explicit allowlist / eligibility gate decision
- a final front-end wording pass

### Future Review Needed
A small Stage 75R / Stage 76 review is recommended before any attempt to open the switch.
