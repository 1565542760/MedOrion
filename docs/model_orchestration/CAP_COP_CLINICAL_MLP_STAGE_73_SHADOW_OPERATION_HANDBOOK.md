# Stage 73 - Clinical MLP Controlled Shadow Operation Handbook

## Purpose
This handbook describes how to operate the CAP/COP clinical MLP controlled shadow skeleton that was introduced in Stage 72. The goal is to keep the shadow path disabled by default, auditable, and clearly separated from live diagnosis or formal recommendation generation.

## Current Position
- The shadow API is a controlled backend skeleton, not a live inference path.
- The default safe state is `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false`.
- When the switch is off, a `shadow_disabled` audit run is the expected and safe outcome.
- `not_for_diagnosis=true` must always be preserved.
- `runtime_stub=true` must always be preserved.
- The shadow path writes only to `shadow_inference_runs` and `shadow_inference_outputs`.
- The shadow path must not write to `recommendations`.
- The shadow path must not write to case `trace_events`, `evidence_nodes`, or `evidence_edges`.
- The shadow path must not load the fold5 weight file, must not call `torch.load`, must not train, and must not use GPU resources.
- The shadow path must not promote the CAP/COP fold5 candidate into `default`, `canary`, or any live recommendation path.

## Operating Model
The shadow execution path is intentionally conservative:
1. Validate case existence.
2. Validate model version and model-input schema.
3. Validate required features through the model-input validation contract.
4. If the shadow switch is disabled, fail closed with `shadow_disabled` and record the shadow audit state.
5. If the switch is enabled in a future controlled environment, continue only as a shadow audit flow.
6. Never reuse shadow output as a formal recommendation.
7. Never bypass validation with front-end parameters, LLM suggestions, or model registry metadata.

## Required Safety State
The following values are mandatory for this stage:
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false` by default
- `not_for_diagnosis=true`
- `runtime_stub=true`
- no silent fallback
- no live inference
- no default/canary promotion
- no recommendation write

## Future Preconditions Before Any Shadow Enablement
Before any future change to enable the shadow switch, all of the following must be satisfied:

- Artifact hash has been registered and reviewed.
- Model registry metadata is complete.
- The model input schema is available and versioned.
- `clinical_feature_mapping` is available.
- Required feature handling is implemented.
- `insufficient_data_for_assessment` behavior is implemented and tested.
- `no_silent_fallback` remains enforced.
- Execution is constrained to `batch=1` and `concurrency=1` until reviewed.
- Shadow audit read APIs are available and verified.
- The front end explicitly labels the flow as `not_for_diagnosis`.
- The shadow path remains isolated from recommendation generation and case evidence.

## Required Feature Handling
If a required feature is missing, the system must choose one of the following paths only:
- missing-value consultation
- explicit default strategy
- `insufficient_data_for_assessment`

The system must not invent values, must not reinterpret defaults as doctor-provided inputs, and must not silently continue with incomplete data.

## Audit Boundary
Shadow audit records are the authoritative record for this path.
- Keep `shadow_inference_runs` for run lifecycle, status, timing, and error detail.
- Keep `shadow_inference_outputs` for prediction-shaped outputs and quality flags.
- Do not mirror ordinary shadow control flow into the case trace/evidence chain.
- Do not convert shadow output into a doctor-facing recommendation unless a future approved review step explicitly authorizes a separate summary workflow.

## Rollback / Disable Procedure
If the shadow path must be turned off:
1. Set `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false`.
2. Keep existing shadow audit rows for review.
3. Do not delete model metadata.
4. Do not alter recommendations.
5. Do not alter case trace/evidence records.

## Checklist for Future Operators
- Confirm the shadow switch is disabled unless the run is explicitly approved.
- Confirm the requested case exists.
- Confirm the model version and schema are compatible.
- Confirm the path is audit-only.
- Confirm outputs stay in the shadow audit tables.
- Confirm the path is not being used as a diagnosis or recommendation source.

## Out of Scope
This handbook does not enable:
- live inference
- model training
- automatic training
- GPU execution
- default or canary rollout
- public Nginx exposure
- front-end changes

## Notes
This stage is intentionally conservative. If any future implementation step requires reading the fold5 weights, that step must be separately justified, explicitly named, and reviewed before execution. For the current stage, weight loading is intentionally out of scope.
