# MedOrion Stage 63: Controlled Shadow Adapter Switch Plan

Last updated: 2026-06-04

## Purpose
Stage 63 designs how the CAP/COP clinical MLP may be moved from disabled into shadow in a controlled way. This stage is only a planning artifact. It does not enable the shadow path, does not load a model, and does not change live inference behavior.

## Shadow Switch Preconditions
Before any shadow switch could be considered, all of the following must exist:
- fold5 artifact hash has been registered
- model registry metadata is complete
- adapter enable switch has been designed
- `model_input_schema` is available
- `clinical_feature_mapping` is available
- timeout / batch=1 / concurrency=1 are defined
- trace/evidence provenance plan is defined
- `no_silent_fallback` is defined
- doctor-facing UI clearly marks shadow / `not_for_diagnosis`

## Switch Strategy
The default state remains disabled.

Shadow may only be enabled through an explicit configuration flag, for example:
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=true`

It must not be enabled through:
- ordinary request parameters
- LLM decisions
- frontend self-service toggles
- hidden magic behavior

## Runtime Boundary
When enabled in a future controlled deployment, shadow mode means:
- background-only side computation
- no change to the doctor-facing formal recommendation
- no replacement of the stub path
- no default recommendation
- outputs go only to shadow audit / evaluation
- failure must be recorded as `shadow_inference_failed`
- no silent fallback to success

## Rollback Strategy
Rollback is intentionally simple:
- turn the shadow switch off
- return to disabled
- no backend or frontend behavior change beyond that switch state
- no model registry lifecycle change
- no artifact deletion
- no training-result modification

## Audit Fields
A future shadow run must be able to record at least the following fields:
- `shadow_run_id`
- `trace_id`
- `case_id`
- `model_version_id`
- `artifact_hash`
- `model_input_schema_id`
- `input_snapshot_id`
- `prediction_raw`
- `prediction_probability`
- `candidate_label`
- `runtime_env`
- `error_code`
- `not_for_diagnosis`

## Explicit Prohibitions
This stage does not:
- execute a real switch
- load a model
- train
- run real inference
- change the database
- execute Alembic
- change the frontend
- enable Nginx
- promote to default
- start canary
- give doctors a formal recommendation

## Current State Reminder
- fold5 is the current shadow candidate
- fold5 is not default
- fold5 is not live inference
- fold5 is not a diagnostic claim
- MedOrion remains doctor-assisted, not doctor-replacing

## Stage 64 Recommendation
Stage 64 should define the shadow audit schema and storage plan so that a future controlled shadow switch has a clear destination for audit data.

## Main-Controller Writeback Summary
- Stage 63 defines a controlled shadow switch plan only.
- Shadow requires explicit configuration, not request-time toggles.
- The runtime boundary is background-only and non-diagnostic.
- Rollback is just disabling the shadow switch.
- Audit fields are identified for future storage design.
