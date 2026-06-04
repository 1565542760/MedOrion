# CAP/COP Real Model Stage 70 Controlled Shadow Execution Plan

## Goals

Stage 70 defines the controlled plan for a future CAP/COP clinical MLP shadow execution path.

This is a planning checkpoint only. It does not implement live shadow execution, does not load model weights, does not run inference, and does not promote any model lifecycle state.

The purpose is to make sure that if MedOrion later enables clinical MLP fold5 in shadow mode, the behavior is explicit, auditable, reversible, and clearly separated from doctor-facing recommendations.

## Non Goals

Stage 70 does not:

- load `.pth/.pt/.onnx/.ckpt/.safetensors` files
- run real inference
- train or retrain models
- enable GPU serving
- promote fold5 to `default`
- write formal recommendations
- write case evidence nodes by default
- change patient/case database schema
- enable Nginx or public deployment
- make any shadow output visible as a diagnostic result

## Current Candidate

The only current candidate discussed by this plan is:

- disease task: `cap_cop`
- model family: `clinical_mlp_cap_cop_classifier`
- adapter: `clinical_mlp_cap_cop_adapter`
- recommended candidate fold: `fold5`
- candidate status: `shadow_candidate`
- evidence level: `low evidence / internal retrospective check`

Fold5 is not approved as default and must not be presented as a clinical diagnosis model.

## Required Preconditions Before Any Shadow Execution

A later execution stage must verify all of the following before running the model:

1. The exact artifact path is explicitly approved.
2. Artifact hash is registered and matches the expected value.
3. Model registry metadata references the intended artifact and adapter.
4. Model version lifecycle is at least approved for shadow evaluation.
5. Shadow execution switch is explicitly enabled by backend configuration.
6. `model_input_schema` is available for the chosen model version.
7. `clinical_feature_mapping` can map the case data into required model features.
8. Required input features are present or explicitly resolved through missing-value consultation/default strategy.
9. `insufficient_data_for_assessment` is returned when required inputs cannot be satisfied.
10. Timeout, batch size, and concurrency limits are configured.
11. Shadow audit write path is available.
12. The UI labels all shadow outputs as not for diagnosis.

## Enable Switch

The default state must be disabled.

A future implementation should require a backend-controlled configuration flag, for example:

```text
ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=true
```

The switch must not be controlled by:

- frontend query params
- ordinary user input
- LLM scheduler output
- model registry metadata alone
- artifact metadata alone

The registry can say a model is shadow eligible, but runtime execution still requires backend configuration.

## Runtime Limits

Recommended first execution limits:

- CPU-only unless explicitly reviewed otherwise
- `batch_size=1`
- `max_concurrency=1`
- strict timeout
- no gradient
- no training mode
- deterministic preprocessing where possible
- single case execution at a time

If the model environment requires a CUDA-capable package, CPU-only behavior should still be forced by runtime configuration where possible. GPU use should be a separate explicit stage.

## Input Flow

The future shadow execution should follow this order:

1. Receive case context and trace id.
2. Resolve disease task as `cap_cop`.
3. Identify candidate model version for clinical MLP fold5 shadow.
4. Load model input schema.
5. Build model input preview.
6. Validate required features.
7. If required features are missing:
   - ask doctor, or
   - apply explicit default strategy when allowed, or
   - return `insufficient_data_for_assessment`.
8. Only after valid input is available, run shadow execution.
9. Store result in shadow audit tables.
10. Do not create formal recommendation.

## Output Flow

Shadow output should be stored in:

- `shadow_inference_runs`
- `shadow_inference_outputs`

It should include:

- `shadow_run_id`
- `trace_id`
- `case_id`
- `patient_id`
- `model_version_id`
- `artifact_hash`
- `adapter_code`
- `model_input_schema_id`
- `input_snapshot_id` when available
- `status`
- `runtime_env_json`
- `runtime_stub=false` only when a real shadow execution is actually performed
- `not_for_diagnosis=true`
- probability output
- candidate label
- confidence/uncertainty
- limitations
- input quality flags

Until real execution is approved, any development write must keep `runtime_stub=true`.

## Trace and Evidence Boundary

Shadow execution can be associated with `trace_id`, `case_id`, and `patient_id`, but it must not automatically write into:

- `recommendations`
- `trace_events`
- `evidence_nodes`
- `evidence_edges`

A later stage may define a controlled promotion path where an approved shadow summary is referenced from case trace/evidence. That must be a separate governance decision.

## Failure Handling

Failures must be explicit and auditable. No silent fallback is allowed.

Expected failure states:

- `shadow_disabled`
- `shadow_model_not_enabled`
- `shadow_insufficient_input`
- `shadow_timeout`
- `shadow_failed`

A failed shadow run must not alter the formal recommendation path.

## Doctor-Facing Safety Text

Any UI that displays shadow output must clearly state:

- Shadow output is not a diagnosis.
- Shadow output does not replace doctor judgment.
- Shadow output does not modify formal recommendation.
- Shadow output is used for audit, evaluation, and future governance only.

## Rollback Plan

Rollback should be simple:

1. Turn off the backend shadow switch.
2. Keep existing shadow audit records for review.
3. Do not delete model registry metadata.
4. Do not delete artifact metadata.
5. Do not alter formal case trace/evidence.
6. Do not alter formal recommendations.

## Minimum Acceptance Before Implementation

Before Stage 71 or any implementation stage proceeds, the team should confirm:

- exact candidate model version and fold
- expected artifact hash
- runtime environment
- input schema id/version
- mapping strategy
- shadow status semantics
- failure code semantics
- whether development-only write endpoint should be environment gated

## Recommended Stage 71

Stage 71 should be one of two options:

1. **Controlled shadow execution implementation draft**, still disabled by default; or
2. **Environment-gated shadow dev write hardening**, if the team wants to strengthen the current dev-record endpoint before any real execution work.

The safer default is option 2 if there is any concern about dev-only endpoints being mistaken for production behavior.

## Main-Controller Writeback Summary

- Stage 70 is a planning-only checkpoint.
- It defines how CAP/COP clinical MLP fold5 may later enter controlled shadow execution.
- It keeps fold5 as shadow candidate only, not default and not live diagnosis.
- It requires explicit backend switch, validated model input schema, feature mapping, no-silent-fallback, and shadow audit storage.
- It keeps shadow output out of formal recommendations and case evidence by default.
- It performs no model loading, no inference, no training, no database migration, and no frontend changes.
