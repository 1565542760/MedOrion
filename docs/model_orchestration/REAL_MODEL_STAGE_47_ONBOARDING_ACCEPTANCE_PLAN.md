# MedOrion Real Model Stage 47 Onboarding Acceptance Plan

Last updated: 2026-06-03 Asia/Shanghai
Owner thread: MedOrion real-model onboarding and acceptance governance
Scope: Stage 47 defines the acceptance checklist and preflight rules for real model onboarding. This stage does not load real models, does not train, does not change database schema, does not execute Alembic, does not enable Nginx, and does not scan, copy, move, or guess any model artifact paths.

## 0. Scope and Non-Goals

Stage 47 goals:
1. Define when the main controller may ask the user for an exact model path.
2. Define the acceptance checklist that must pass before a real model can be loaded later.
3. Define artifact metadata requirements and hash verification boundaries.
4. Define adapter enablement checks before a real model adapter can be switched on.
5. Define minimum offline evaluation, trace, evidence, shadow, canary, rollback, and safety checks.
6. Define failure handling for invalid path, hash mismatch, loading failure, and resource insufficiency.
7. Define the route to Stage 48.

Stage 47 non-goals:
1. Do not load real models.
2. Do not train models.
3. Do not automatically retrain.
4. Do not enable GPU.
5. Do not change database schema.
6. Do not execute Alembic.
7. Do not enable Nginx.
8. Do not scan or guess artifact files.
9. Do not copy or move artifact files.
10. Do not replace doctor judgement.

## 1. Goals

Stage 45 defined the real-model onboarding preface. Stage 46 prepared registry-oriented groundwork. Stage 47 is the acceptance checklist that gates the first real artifact from going anywhere near a live adapter.

This stage exists so the team can answer:
1. When is it appropriate to ask the user for a model path?
2. What exactly must be registered before a real model can ever be loaded later?
3. What must be checked before a real adapter can be enabled?
4. What evidence is required to support safe promotion?
5. What should happen if the path is wrong, the hash differs, the model fails to load, or the runtime lacks resources?

## 2. Non Goals

1. No real artifact loading.
2. No artifact path scanning.
3. No artifact guessing.
4. No artifact copying or moving.
5. No training.
6. No automatic real-time training.
7. No GPU enablement.
8. No production rollout.
9. No database migration execution.
10. No silent fallback.
11. No doctor replacement.

## 3. When It Is Allowed To Ask The User For An Exact Model Path

The main controller may ask the user for an exact model path only when all of the following are true:
1. The team has already determined that real model onboarding is the next intended step.
2. The target disease-agent, task, and intended artifact type are known.
3. The system has a registry plan for the target `model_id` / `model_version_id`.
4. The request is for a concrete onboarding task, not for directory exploration.
5. The controller has no valid registered artifact for the requested version.
6. The controller is not attempting to infer a path from folder names, prior projects, or naming patterns.

Questioning rule:
1. Ask for one exact path, not a folder list.
2. Ask for the artifact type if it is not already known.
3. Ask for provenance notes if the source is unclear.
4. Do not ask the user to upload random candidates or search directories for the system.

## 4. User Path Provided Does Not Mean Immediate Load

Even after the user provides an exact path, the model must not be loaded immediately.

Required sequence:
1. Receive exact path from user.
2. Register artifact metadata.
3. Verify artifact identity metadata.
4. Record hash or pending-hash state.
5. Attach the artifact to a specific `model_version_id`.
6. Run acceptance prechecks.
7. Only after all gates pass may a later stage enable a real adapter.

Rule:
1. Path provided is not the same as onboarding complete.
2. Path provided is not the same as model approved for load.
3. Path provided is not the same as runtime-ready.

## 5. Artifact Metadata Required Fields

Every real artifact onboarding record must include the following fields:
1. `artifact_uri`
2. `artifact_type`
3. `artifact_hash` or `hash_pending`
4. `hash_algorithm`
5. `file_size_bytes` or `file_size_pending`
6. `adapter_type`
7. `preprocess_schema_version`
8. `postprocess_schema_version`
9. `source_note`
10. `safety_notes`

### 5.1 Field notes

`artifact_uri`:
1. Exact path or governed object URI supplied by the user or approved storage reference.
2. Must not be guessed.

`artifact_type`:
1. Must be one of the supported artifact types already governed by Stage 45.

`artifact_hash` or `hash_pending`:
1. If the hash has already been computed on the exact user-authorized path, store the hash value.
2. If the hash has not yet been computed, store a pending state.
3. A pending state must be explicit and auditable.

`hash_algorithm`:
1. Must be explicit when hash is computed or planned.
2. Example values may include `sha256`.

`file_size_bytes` or `file_size_pending`:
1. File size must be stored or marked pending.
2. Pending must be explicit, not implied.

`adapter_type`:
1. Must state which adapter family is expected to load or wrap the artifact.
2. Example: `stub_adapter`, `real_cpu_adapter`, `onnxruntime_cpu_adapter`.

`preprocess_schema_version` and `postprocess_schema_version`:
1. Must match the adapter and model contract.
2. Must be validated before enablement.

`source_note`:
1. Must explain provenance or source context.

`safety_notes`:
1. Must contain safety limits, known caveats, and doctor-warning statements.

## 6. Hash Verification Boundary

Hash computation is allowed only after the user has explicitly authorized the exact path.

Rules:
1. Compute hash only for the exact file path provided.
2. Do not scan directories looking for files to hash.
3. Do not hash candidates found by guessing.
4. Do not substitute a nearby file with a similar name.
5. Record the hash algorithm and the resulting hash in the artifact metadata.
6. If the hash cannot be computed at the time of onboarding, mark it as pending and hold the artifact from load enablement.

## 7. Real Model Adapter Enablement Checks

Before a real model adapter can be enabled, all of the following checks must pass:
1. `model_version` state is eligible for real loading.
2. approval status is valid for the target rollout mode.
3. default/shadow/canary policy is satisfied.
4. CPU-first runtime assumptions are satisfied.
5. timeout configuration is present and reasonable.
6. batch size is `1` unless a later stage explicitly approves otherwise.
7. concurrency is `1` unless a later stage explicitly approves otherwise.
8. preprocessing schema version matches the adapter.
9. postprocessing schema version matches the adapter.
10. artifact hash is present or the pending state has been resolved.
11. resource requirements fit the approved runtime plan.
12. safety notes are present.
13. trace and evidence mapping is ready.

## 8. Input Preprocessing Acceptance

Input preprocessing must be validated before a real adapter can be enabled.

Acceptance checks:
1. schema version is known
2. required fields are present
3. missing-value handling is explicit
4. modality references are valid
5. normalization rules are documented
6. shape or tensor expectations are documented if applicable
7. de-identification or privacy requirements are respected
8. failure behavior is defined

A preprocessing failure must not be silently ignored.

## 9. Output Postprocessing Acceptance

Output postprocessing must be validated before a real adapter can be enabled.

Acceptance checks:
1. output schema version is known
2. class or label mapping is documented
3. confidence packaging is documented
4. uncertainty packaging is documented
5. limitation packaging is documented
6. evidence node creation mapping is documented
7. doctor-facing next-action packaging is documented
8. failure behavior is defined

Postprocessing must not invent certainty that the model did not provide.

## 10. Trace / Evidence Acceptance

Every future real-model invocation must be trace-bound and evidence-bound.

Required trace/evidence fields:
1. `model_version_id`
2. `artifact_hash`
3. `input_refs`
4. `output_refs`
5. `runtime_env`
6. `model_invocation_id`
7. `trace_id`
8. `approval_status`
9. `fallback_reason` nullable
10. `runtime_stub_or_real_model`

Acceptance rule:
1. The system must be able to point from a trace event to the exact model version and exact artifact identity.
2. Input and output references must be stored as references, not heavy payload copies.
3. If the runtime is stub, the trace must say stub.
4. If the runtime is real, the trace must say real.

## 11. Offline Evaluation Minimum Requirements

A real model may only be considered for later enablement after the following minimum offline evidence exists:
1. validation or held-out set used
2. metrics summary available
3. calibration summary available
4. uncertainty summary available
5. failure rate summary available
6. subgroup performance summary available
7. missing-value sensitivity summary available
8. latency summary available

Offline evaluation rule:
1. No offline evaluation means no real enablement consideration.
2. A weak calibration result blocks promotion even if headline metrics look good.
3. A subgroup regression blocks default promotion until resolved.
4. Evaluation results must be attached to the version record.

## 12. Shadow / Canary / Default Gates

Shadow / canary / default are strict rollout gates.

Shadow gate:
1. comparison-only or mirrored traffic
2. no doctor-facing effect
3. comparison evidence only

Canary gate:
1. limited traffic only
2. explicit scope
3. rollback ready
4. visible in trace

Default gate:
1. explicit promotion required
2. evidence-backed
3. safer or better for the intended scope
4. never achieved by hidden fallback

## 13. Fallback, Rollback, and `no_silent_fallback`

Rules:
1. Any fallback must be explicit.
2. Any rollback must identify the prior version.
3. Any adapter or version swap must emit trace events.
4. Silent fallback is prohibited.
5. The user and doctor-facing workflow must be able to see why a fallback happened.

Rollback reasons may include:
1. load failure
2. hash mismatch
3. compatibility failure
4. resource insufficiency
5. offline regression
6. canary regression

## 14. Doctor Safety Statement

MedOrion remains a doctor-assistance platform.

Rules:
1. Real model onboarding does not change the fact that doctors remain the final decision makers.
2. Real model output must remain advisory.
3. Uncertainty and limitations must be visible.
4. Safety notes must be preserved in registry and trace.

## 15. Failure Handling

If a problem occurs, the system must behave conservatively.

### 15.1 Invalid path

1. Reject onboarding.
2. Do not guess an alternate file.
3. Ask for the exact path again if needed.
4. Record the failure.

### 15.2 Hash mismatch

1. Reject real enablement.
2. Hold the artifact from promotion.
3. Recompute only on the exact authorized path if allowed.
4. Preserve audit logs.

### 15.3 Model loading failure

1. Keep the adapter in stub or disabled state.
2. Record the error and reason.
3. Do not silently switch to a different artifact.
4. Do not pretend the model is ready.

### 15.4 Resource insufficiency

1. Keep CPU-first conservative mode.
2. Do not force GPU.
3. Do not overcommit concurrency.
4. Do not promote if runtime requirements are not met.

## 16. Stage 48 Recommendation

Stage 48 should prepare the metadata registration and hash-verification readiness flow.

Recommended Stage 48 work:
1. metadata registration readiness checklist
2. exact-path intake flow for user-provided artifact references
3. hash verification bookkeeping
4. backend contract preparation for artifact registry integration
5. rollout and evaluation preflight packaging

Stage 48 should only proceed after the user has provided an exact model path for the intended artifact.

## 17. Main-Controller Writeback Summary

1. Stage 47 onboarding acceptance plan is created.
2. The controller may ask the user for an exact model path only when the onboarding target is known and registry intent exists.
3. User-provided path does not permit immediate load; metadata registration and preflight checks must happen first.
4. Required artifact metadata includes `artifact_uri`, `artifact_type`, `artifact_hash` or pending state, `hash_algorithm`, `file_size_bytes` or pending state, `adapter_type`, preprocessing/postprocessing schema versions, `source_note`, and `safety_notes`.
5. Hash computation is allowed only for the exact user-authorized path and never through directory scanning.
6. Real adapter enablement requires version, approval/default, CPU-first, timeout, batch, concurrency, schema, and resource checks.
7. Offline evaluation, shadow/canary/default gates, fallback, rollback, and `no_silent_fallback` are all mandatory preconditions.
8. Trace and evidence must bind `model_version_id`, `artifact_hash`, input refs, output refs, and runtime env.
9. Stage 48 should focus on metadata registration and hash-verification readiness, but only after a user provides an exact artifact path.
