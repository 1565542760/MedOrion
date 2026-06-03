# MedOrion Real Model Onboarding Stage 45 Contract

Last updated: 2026-06-03 Asia/Shanghai
Owner thread: MedOrion model onboarding and release governance
Scope: Stage 45 defines the preconditions for real model onboarding, artifact registration, evaluation, and safe rollout. This stage does not load real models, does not train, does not enable GPU, does not change database schema, and does not start a real inference service.

## 0. Scope and Non-Goals

Stage 45 goals:
1. Define the contract for bringing real model artifacts into MedOrion in a governed way.
2. Define how stub adapters transition to real adapters without breaking trace, evidence, or rollout policy.
3. Define artifact registration and model registry linkage requirements.
4. Define offline evaluation, shadow, canary, default, rollback, and fallback gates.
5. Define how doctor feedback and quality review inform model quality decisions without triggering automatic training.
6. Define how real inference results enter trace and evidence.
7. Define a release-safe path toward Stage 46 artifact registry and backend preparation.

Stage 45 non-goals:
1. Do not load real `.pth`, `.pt`, `.onnx`, `.ckpt`, or `.safetensors` artifacts.
2. Do not train models.
3. Do not automatically retrain in real time.
4. Do not enable GPU serving.
5. Do not perform real production deployment.
6. Do not execute Alembic.
7. Do not change database schema.
8. Do not enable Nginx.
9. Do not publicize endpoints.
10. Do not replace doctor diagnosis.

## 1. Goals

Stage 44 established the runnable MVP skeleton baseline. Stage 45 is the controlled pre-onboarding layer that prepares MedOrion for real models without actually loading them.

Why this stage is needed:
1. Real models require governed artifact registration, not ad hoc filesystem discovery.
2. The system must know how an artifact maps to `model_id`, `model_version_id`, registry state, and rollout mode.
3. The system must support safe transition from stub adapter to real adapter with traceable gating.
4. The platform must show that a new model is ready for real use only after offline evaluation and governance review.
5. Future real-model onboarding must preserve doctor safety, traceability, and rollback readiness.

## 2. Non Goals

1. No real artifact loading.
2. No `.pth` file scanning.
3. No `.pth` file guessing.
4. No `.pth` file copying or moving.
5. No training.
6. No automatic real-time training.
7. No GPU enablement.
8. No real inference deployment.
9. No production rollout.
10. No database schema changes.
11. No Alembic execution.
12. No Nginx enablement.
13. No silent fallback.

## 3. Artifact Registration Workflow

Real model onboarding must start from a user-provided exact artifact path.

Required workflow:
1. Main controller asks the user to provide the exact artifact path.
2. The system does not scan directories to find candidate artifacts.
3. The system does not guess which file is correct.
4. After the user provides the exact path, the artifact can be registered.
5. Registration stores `artifact_uri`, `artifact_hash`, `model_version_id`, `model_id`, source metadata, and intended use.
6. Only registered artifacts may be linked to model registry records.
7. The artifact remains immutable after registration unless a new version is created.

Artifact registration must capture:
1. exact path provided by user
2. artifact type
3. hash
4. source location
5. source owner or provenance
6. purpose / intended use
7. linked registry version
8. registration timestamp

## 4. Supported Artifact Types and Rules

Supported artifact types for registration are:
1. `.pth`
2. `.pt`
3. `.onnx`
4. `.ckpt`
5. `.safetensors`

Rules:
1. The artifact type must be recorded explicitly.
2. The artifact must not be modified in place after registration.
3. The artifact must not be committed to Git.
4. The artifact must not be silently replaced by another file at the same path.
5. The artifact must be associated with a concrete `model_version_id`.
6. The artifact must be referenced by registry metadata, not by informal path references in business logic.
7. If a conversion artifact is used, the conversion source and target must be recorded.

## 5. Model Registry Association

Stage 45 defines how real artifacts relate to the model registry.

Required association fields:
1. `artifact_uri`
2. `artifact_hash`
3. `model_id`
4. `model_version_id`
5. `approval_status`
6. `evaluation_summary`
7. `limitations`
8. `runtime`
9. `resource_requirements`
10. `created_at`
11. `approved_at`

Association rules:
1. `artifact_uri` points to the registered artifact location.
2. `artifact_hash` proves artifact identity and protects against silent changes.
3. `model_version_id` is the stable version handle used in trace, evidence, and rollout.
4. `model_registry` remains the source of truth for what version is approved, default, shadowed, canaried, deprecated, or archived.
5. Artifact identity is never inferred from a folder name.

## 6. Model Files Must Not Be Committed to Git

1. Real model files must not be committed to Git.
2. Git history must not become the storage location for model binaries.
3. Artifact registration should reference storage, not source control blobs.
4. If a model file must be shared, its location is registered separately from code.
5. The repository should only contain contract, metadata, and adapter code, not model weights.

## 7. Stub Adapter to Real Adapter Minimal Contract

Stage 45 defines the smallest safe transition contract from stub adapter to real adapter.

The adapter transition requires:
1. same request schema
2. same response schema shape
3. same trace propagation behavior
4. same error-code discipline
5. same `no_silent_fallback` rule
6. same evidence emission contract
7. same approval and rollout policy checks

### 7.1 Stub adapter characteristics

1. Returns contract-valid responses.
2. Does not load real artifacts.
3. Marks outputs as stub/demo.
4. Emits trace events that explicitly identify stub mode.

### 7.2 Real adapter characteristics

1. Loads approved model artifact only after registration.
2. Uses the same request/response contract as stub adapter.
3. Produces real inference outputs from approved artifacts.
4. Emits trace events showing real-model execution.
5. Fails closed if artifact, approval, or runtime checks are invalid.

### 7.3 Transition rule

1. Stub and real adapters must be interchangeable from the caller's perspective.
2. The caller should not need to change request shape when moving from stub to real.
3. The adapter switch must be controlled by registry and policy state, not by ad hoc file-path logic.

## 8. Preprocessing and Postprocessing Contracts

Real model onboarding must define preprocessing and postprocessing schemas before the first real call.

### 8.1 Input preprocessing schema

Preprocessing may include:
1. input normalization
2. modality-specific formatting
3. missing-value handling
4. schema validation
5. feature alignment
6. de-identification checks
7. shape or tensor preparation

Preprocessing contract must record:
1. input schema version
2. modality refs
3. normalization rules
4. transformation summary
5. missing-value impact
6. compatibility constraints

### 8.2 Output postprocessing schema

Postprocessing may include:
1. label mapping
2. probability calibration handling
3. uncertainty packaging
4. limitation packaging
5. trace/evidence node generation
6. doctor-facing next-action packaging

Postprocessing contract must record:
1. output schema version
2. raw output summary
3. calibrated output summary
4. uncertainty fields
5. confidence fields
6. model limitations

### 8.3 Error and timeout contract

Required error categories:
1. invalid_input
2. missing_required_input
3. unsupported_modality
4. model_not_found
5. model_version_not_approved
6. inference_timeout
7. resource_exhausted
8. dependency_unavailable
9. internal_error
10. trace_id_missing

Timeout policy:
1. CPU-first timeout defaults remain in place for Stage 45 pre-onboarding.
2. GPU-later may be adopted later, but not in this stage.
3. Any timeout or retry must preserve trace and idempotency.

## 9. CPU-First / GPU-Later Strategy

Stage 45 remains CPU-first.

Rules:
1. CPU is the default runtime assumption.
2. GPU is a later operational option, not a Stage 45 dependency.
3. Batch size should remain conservative.
4. Concurrency should remain conservative.
5. If a future model requires GPU, that fact must be captured as resource requirement metadata and not silently enabled.

## 10. Offline Evaluation Requirements

A real model may only move toward rollout after governed offline evaluation.

Required evaluation inputs:
1. validation set or held-out set
2. metrics summary
3. calibration summary
4. uncertainty behavior summary
5. failure rate summary
6. subgroup performance summary
7. missing-value sensitivity summary
8. latency summary

Required evaluation outputs:
1. quantitative metrics
2. limitations
3. failure patterns
4. calibration notes
5. uncertainty notes
6. subgroup observations
7. recommendation on whether to approve shadow, canary, or hold

Offline evaluation rule:
1. Offline evaluation is required before online consideration.
2. Offline evaluation is not enough by itself to become default.
3. A model with good metrics but poor calibration or subgroup behavior must not be promoted automatically.
4. Evaluation summary must be attached to model version registry metadata.

## 11. Shadow / Canary / Default Gates

### 11.1 Shadow gate

1. Shadow means mirrored or comparison-only traffic.
2. Shadow does not affect doctor-facing outcome.
3. Shadow is useful for comparing real vs prior versions on the same trace-bound inputs.

### 11.2 Canary gate

1. Canary means limited real traffic under policy.
2. Canary requires explicit scope control.
3. Canary requires rollback readiness.
4. Canary results must be recorded and reviewed.

### 11.3 Default gate

1. Default means the promoted version used for the normal policy path.
2. Default promotion requires evidence that the version is better or at least safer and more acceptable for the relevant scope.
3. Default cannot be set by a hidden fallback.

### 11.4 Gate rule

1. `shadow` does not equal `default`.
2. `canary` does not equal `default`.
3. Promotion must be explicit and auditable.

## 12. Doctor Feedback and Quality Review

Doctor feedback and quality review are quality signals, not automatic training triggers.

Rules:
1. Doctor feedback may influence future evaluation and governance.
2. Quality review may identify output issues, conflict patterns, or rollback reasons.
3. Neither doctor feedback nor quality review may trigger automatic real-time training.
4. Both should feed into model quality judgment and rollout decisions.
5. If they indicate regression, the version may be held, deprecated, or rolled back.

## 13. Trace / Evidence Requirements

Real model inference results must be trace-bound and evidence-bound.

Required records:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `model_id`
5. `model_version_id`
6. `runtime_stub_or_real_model`
7. `artifact_hash`
8. `model_registry_ref`
9. `selection_reason`
10. `fallback_reason` nullable
11. `error` nullable
12. `confidence`
13. `uncertainty`
14. `limitations`

Required trace events:
1. `model_selected`
2. `model_invoked`
3. `model_result_received`
4. `orchestrator_decision`

Evidence rules:
1. Model output must become a `model_output` evidence node.
2. The evidence node must reference the `model_version_id` and registry record.
3. If a result contributes to a recommendation, the recommendation node must reference it.
4. If fallback or rollback occurred, the trace and evidence must say so.

## 14. Rollback, Fallback, and `no_silent_fallback`

Rollback and fallback are controlled operations.

Rules:
1. A rollback must point to a prior known-good version.
2. Fallback to a different version or adapter must be explicit.
3. Fallback reason must be emitted to trace.
4. Silent fallback is prohibited.
5. A failed real adapter must not pretend it succeeded.
6. Rollback must preserve traceability of the version that was replaced.

## 15. Safety Statement

MedOrion is a doctor-assistance platform.

Safety rules:
1. Real models do not replace doctor diagnosis.
2. Real model outputs are advisory and traceable.
3. Uncertainty and limitations must remain visible.
4. Doctor review remains the final clinical decision point.

## 16. Stage 46 Recommendation

Stage 46 should prepare the artifact registry and backend integration plan.

Recommended Stage 46 work:
1. artifact registry preparation
2. backend contract for artifact registration and version binding
3. user-facing artifact path collection flow in governance tooling
4. preflight checks for approved artifacts
5. final adapter readiness checks for real-model onboarding

Stage 46 must still wait for user-provided exact artifact paths before any `.pth`-family registration work proceeds.

## 17. Main-Controller Writeback Summary

1. Stage 45 real-model onboarding preface contract is created.
2. This stage is explicitly pre-onboarding only and does not load real artifacts.
3. Artifact registration must begin with a user-provided exact path; the system must not scan, guess, copy, or move model files.
4. Supported artifact types are `.pth`, `.pt`, `.onnx`, `.ckpt`, and `.safetensors`, but none are to be loaded in Stage 45.
5. `artifact_uri`, `artifact_hash`, `model_id`, `model_version_id`, and `model_registry` linkage is defined as the governing association.
6. Stub adapter to real adapter transition must preserve request/response shapes, trace propagation, and `no_silent_fallback`.
7. Offline evaluation, shadow, canary, and default gating are required before real rollout consideration.
8. Doctor feedback and quality review are quality signals only and do not trigger automatic training.
9. Real inference results must enter trace/evidence with version and artifact provenance.
10. Stage 46 should focus on artifact registry and backend preparation, but only after user-provided exact artifact paths are available.
