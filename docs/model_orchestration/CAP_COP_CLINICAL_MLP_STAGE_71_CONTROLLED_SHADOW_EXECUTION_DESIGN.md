# Stage 71A: CAP/COP Clinical MLP Controlled Shadow Execution Design

## Goal and Boundary

Stage 71 is a design-first step for controlled shadow execution of the CAP/COP clinical MLP fold5 candidate.

The implementation must stay disabled by default, must never affect formal recommendations, and must only write shadow audit records.

This stage does not enable live inference, does not train models, does not load models by default, and does not write case trace/evidence.

## Running Invariant

Any future Stage 71/72 shadow execution path must enforce these invariants:

- `not_for_diagnosis=true`
- disabled by default
- explicit backend configuration gate required
- no silent fallback
- no formal recommendation writes
- no case `trace_events` / `evidence_nodes` / `evidence_edges` writes
- shadow output is audit material only

`not_for_diagnosis=true` is not a display hint. It is a required runtime invariant for every shadow run and every shadow output.

## Existing Assets Reviewed

Reviewed backend surfaces:

- `app/backend/app/modules/model_input/router.py`
- `app/backend/app/modules/model_input/catalog.py`
- `app/backend/app/modules/model_registry/router.py`
- `app/backend/app/modules/model_registry/schemas.py`
- `app/backend/app/modules/shadow_audit/router.py`
- `app/backend/app/modules/shadow_audit/schemas.py`
- `app/backend/app/modules/shadow_audit/service.py`
- `app/backend/app/db/models.py`

Reviewed runtime contracts:

- CAP/COP clinical feature set v1 contains 36 task-level clinical attributes.
- `Striated_shadow.1` must remain present.
- The CAP/COP feature set can be reused by multiple CAP/COP models.
- The clinical MLP schema is a model-specific input schema that may reuse the CAP/COP feature set.
- Shadow audit storage already exists with `shadow_inference_runs` and `shadow_inference_outputs`.
- Shadow audit read and controlled write skeleton already exist.
- Model input preview / validation / selection skeleton already exists.
- Model registry metadata and artifact-only fields already exist.

## Recommended Implementation Shape

If Stage 71 proceeds from design into code, the minimal safe shape is:

1. A backend configuration gate that defaults to disabled.
2. A controlled shadow runner that only executes when the gate is explicitly enabled.
3. A single, explicit, approved artifact reference for the fold5 candidate.
4. Input validation that reuses the model-input validation API before any shadow execution.
5. A write-only audit path that stores run/output records in the shadow audit tables.
6. No write path into recommendations or case trace/evidence.

This stage should remain separate from the live recommendation flow.

## Scope of Code Changes if Implementation Is Later Approved

Suggested files for a later implementation pass only:

- `app/backend/app/core/config.py`
- `app/backend/app/modules/shadow_audit/service.py`
- `app/backend/app/modules/shadow_audit/router.py`
- `app/backend/app/modules/shadow_audit/schemas.py`
- `app/backend/app/modules/model_input/router.py`
- `app/backend/app/modules/model_registry/router.py`
- optional future model-service adapter code if a dedicated shadow execution entrypoint is introduced later

No frontend changes are required for this stage.

## Enable Switch and Disabled-By-Default Rule

The shadow path must be off unless an explicit backend configuration flag is enabled.

Recommended gate:

```text
ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false
```

The flag must be read only from backend configuration.

It must not be overrideable by:

- frontend parameters
- generic request fields
- LLM suggestions
- model registry metadata alone
- artifact metadata alone

If the gate is off, shadow requests must fail closed with a clear `shadow_disabled` style status and must not run any model code.

## Artifact Path Handling

The implementation must not discover model files by scanning directories.
It must not glob, search, infer, copy, move, or hash files on its own.

The only acceptable source for a shadow artifact reference is a single, explicit, approved metadata value, such as:

- `model_versions.artifact_ref_json.artifact_uri`
- a backend config value that is explicitly set to the approved single artifact URI

The artifact reference must identify exactly one approved artifact. It must not be a directory, prefix, wildcard, glob pattern, adjacent-file hint, or user-facing free-form guess.

The path must be treated as governed metadata, not as a signal that the model is live. The implementation must never assume a `.pth` file is a live model.

If the explicit artifact reference is missing or does not match the approved model version metadata, the system must return `shadow_model_not_enabled` or an equivalent explicit error.

## Input Schema and Feature Mapping

The controlled shadow run must first resolve the model input schema and then validate the case input against it.

For CAP/COP fold5:

- task feature set: `cap_cop_clinical_feature_set_v1`
- schema: `clinical_mlp_cap_cop_input_schema_v1`
- feature count: 36
- `Striated_shadow.1` must be preserved

The mapping flow should be:

1. Gather structured case inputs from clinical observations, lab results, EMR documents, and other structured tables.
2. Map source fields to model feature names via the existing mapping contract.
3. Run model-input validation.
4. If required features are missing, use only one of the approved paths:
   - missing-value consultation
   - explicit default strategy
   - `insufficient_data_for_assessment`
5. Only proceed to shadow execution when the required-input rule is satisfied for the chosen policy.

No silent fallback is allowed.

## Required-Feature Failure Handling

If a required feature is missing, the shadow runner must not invent a value.

The allowed paths are:

- ask the doctor
- apply an explicit default strategy and audit it
- stop with `insufficient_data_for_assessment`

The implementation must preserve the distinction between:

- doctor-provided values
- default-applied values
- unsupported / insufficient data

Shadow execution must not proceed by hard-coding an assumed replacement value.

## Shadow Audit Write Scope

A successful or failed shadow execution may write only to:

- `shadow_inference_runs`
- `shadow_inference_outputs`

The following must remain untouched by Stage 71 runtime execution:

- `recommendations`
- case `trace_events`
- `evidence_nodes`
- `evidence_edges`

Shadow output is audit material, not a clinical recommendation.

## Status and Error Semantics

Recommended run statuses:

- `shadow_success`
- `shadow_failed`
- `shadow_disabled`
- `shadow_timeout`
- `shadow_insufficient_input`
- `shadow_model_not_enabled`

Recommended error codes:

- `case_not_found`
- `model_version_not_found`
- `model_input_schema_not_found`
- `insufficient_data_for_assessment`
- `shadow_disabled`
- `shadow_model_not_enabled`
- `shadow_timeout`
- `shadow_inference_failed`

The implementation must not convert these into recommendation-like statuses.

## no_silent_fallback Rule

The system must fail closed.

If the gate is off, the model is not approved for shadow, the input is insufficient, or the explicit artifact reference is missing, the system must return an explicit failure state.

It must not silently pick another model, silently swap a different task family, silently use another artifact, or silently create a formal recommendation.

## Rollback and Disable Strategy

Rollback should be a pure config operation:

- disable `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW`
- keep existing audit rows immutable
- keep the read APIs available

Disabling shadow must not delete data and must not rewrite prior audit entries.

## What This Stage Is Not

Stage 71 is not:

- live clinical inference
- a recommendation path
- a default/canary promotion path
- a training workflow
- a frontend workflow
- a case evidence writer
- a real model loader by default

## Suggested Next Step

If this design is accepted, a later implementation stage can add a strictly disabled-by-default controlled shadow runner.

That later step should be reviewed again before any code path is activated.
