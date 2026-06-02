# MedOrion Model Registry Stage 32 Contract

Last updated: 2026-06-02 Asia/Shanghai
Owner thread: MedOrion model registry and version lifecycle
Scope: Stage 32 defines model registration, version lifecycle, approval, promotion, rollback, and trace/evidence/feedback linkage contracts only. No real `.pth` loading, no training, no automatic real-time training, no GPU enablement, and no production model rollout.

## 0. Scope and Non-Goals

Stage 32 goals:
1. Define why MedOrion now needs a model registry and version lifecycle.
2. Define how new models enter the system.
3. Define how orchestrator and disease agents discover available model capabilities without scanning files.
4. Define how new versions are approved, shadowed, canaried, promoted, deprecated, archived, and rolled back.
5. Define how model lifecycle connects to trace, evidence, doctor feedback, and quality review.
6. Define the contract surface for future backend CRUD, frontend model management, and MLOps preparation.

Stage 32 non-goals:
1. Do not load real `.pth` artifacts.
2. Do not train models.
3. Do not automatically retrain in real time.
4. Do not enable GPU serving.
5. Do not perform real model evaluation execution in this stage.
6. Do not publish a production model release.
7. Do not change database schema in this stage.
8. Do not perform Alembic migrations in this stage.

## 1. Goals

MedOrion needs a model registry and version lifecycle because the platform is now beyond a single stub flow.

The registry solves four operational problems:
1. New disease-specific models must be introduced without changing the orchestration contract every time.
2. Orchestrators and disease agents must know which models are available, approved, shadowed, canaried, or deprecated.
3. New versions must replace old versions without service downtime.
4. The platform must show evidence that a newer model is actually better before it becomes the default.

This registry is not a file browser. It is a governed control plane for capability, approval, version policy, and auditability.

## 2. Non Goals

1. No real `.pth` loading.
2. No training.
3. No automatic real-time training.
4. No GPU enablement.
5. No real model evaluation execution.
6. No production rollout.
7. No database migration execution.
8. No silent model replacement.
9. No file-path discovery by scanning project folders.

## 3. Core Concepts

### 3.1 `disease_agent`
A disease-specific orchestration unit that owns task logic, modality expectations, and model selection rules for one clinical domain, for example `cap_cop`.

### 3.2 `model_registry`
The governed catalog of available model families and version records. It answers: what models exist, what they support, what state they are in, and what artifact metadata is attached.

### 3.3 `model_versions`
Versioned records beneath a model family. Each version can have different artifact metadata, evaluation summary, approval state, and rollout state.

### 3.4 `model_version_policy`
The runtime selection policy used by orchestrator or disease agent when choosing a version for an inference task.

### 3.5 `model_invocation`
A trace-bound execution attempt against one selected model version, including status, runtime, fallback reason, and emitted evidence.

### 3.6 `shadow`
A rollout mode where a new version receives mirrored traffic or offline replay for comparison, but does not affect doctor-facing results.

### 3.7 `canary`
A rollout mode where a new version receives limited real traffic under guarded policy before becoming default.

### 3.8 `default`
The current version used for normal doctor-facing inference for a specific disease-agent/task/modality contract.

### 3.9 `rollback`
A deliberate policy change that moves the default selection back to a prior approved version.

### 3.10 `offline_evaluation`
A governed, non-production assessment using a frozen dataset, held-out set, or historical replay. It is not live online training.

### 3.11 `doctor_feedback`
Doctor response on model output, recommendation, or missing-value handling. It is a quality signal, not an automatic model update.

### 3.12 `quality_review`
A formal review record that evaluates whether a model output, trace, recommendation, or workflow decision needs correction, escalation, or audit closure.

## 4. Model Lifecycle Status

### 4.1 Status machine

Allowed lifecycle states:
1. `draft`
2. `offline_evaluated`
3. `approved`
4. `shadow`
5. `canary`
6. `default`
7. `deprecated`
8. `archived`

### 4.2 State meanings

`draft`:
1. Model/version metadata exists.
2. Artifact metadata may be incomplete.
3. Not eligible for online use.

`offline_evaluated`:
1. Version has passed a governed offline evaluation step.
2. Results exist for review.
3. Not yet allowed for general online use unless approved.

`approved`:
1. Review and governance have accepted the version.
2. Eligible for shadow or canary depending on policy.
3. Not necessarily the default.

`shadow`:
1. May receive mirrored calls or offline replay.
2. Must not change doctor-facing result.
3. Used for comparison only.

`canary`:
1. May receive limited real traffic.
2. Must be constrained by policy, disease, and task scope.
3. Requires trace visibility and rollback readiness.

`default`:
1. Current normal production selection for the approved scope.
2. Eligible for online calls.
3. Must always remain traceable.

`deprecated`:
1. No longer preferred for new calls.
2. May remain available for rollback or historical comparison.
3. New calls should be blocked unless policy explicitly allows rollback use.

`archived`:
1. Historical record only.
2. Not eligible for online calls.
3. Retained for audit and reproducibility.

### 4.3 Online-callability rules

1. `draft`: no online calls.
2. `offline_evaluated`: no online calls unless promoted to approved.
3. `approved`: yes, but only if selected by policy as shadow or canary or promoted default.
4. `shadow`: yes, mirrored or comparison-only.
5. `canary`: yes, limited traffic only.
6. `default`: yes.
7. `deprecated`: no new online calls unless explicitly used for rollback or controlled exception.
8. `archived`: no.

## 5. Model Registration Metadata

Every new model version must register the following metadata before it can participate in governance:

1. `model_id`
2. `model_version_id`
3. `disease_agent_code`
4. `agent_contract_version`
5. `supported_diseases`
6. `supported_tasks`
7. `supported_modalities`
8. `input_schema_version`
9. `output_schema_version`
10. `artifact_uri`
11. `artifact_hash`
12. `runtime`
13. `resource_requirements`
14. `approval_status`
15. `evaluation_summary`
16. `limitations`
17. `created_by`
18. `approved_by`
19. `created_at`
20. `approved_at`

### 5.1 Required field notes

`model_id`:
1. Stable family identifier.
2. Shared across versions.

`model_version_id`:
1. Immutable version identifier.
2. Referenced in trace, evidence, and rollout records.

`disease_agent_code`:
1. The primary disease-agent owner of the version.
2. Example: `cap_cop`.

`agent_contract_version`:
1. Must match the agent contract the model version was built for.
2. Prevents version drift.

`supported_diseases`:
1. May contain multiple disease labels if the model family is designed for them.
2. Must be explicit, not inferred.

`supported_tasks`:
1. For example `classification`, `risk_scoring`, `segmentation`, `detection`.
2. Must be explicit.

`supported_modalities`:
1. For example `ct_image`, `clinical_table`, `emr_text`.
2. Must be explicit.

`input_schema_version` and `output_schema_version`:
1. Bind model version to contract versioning.
2. Protect orchestrator and frontend from silent breakage.

`artifact_uri`:
1. Must point to a registered, user-provided artifact location.
2. Must not be guessed by scanning the filesystem.

`artifact_hash`:
1. Used to prove artifact immutability.
2. Required for governance and audit.

`runtime`:
1. Example values: `cpu`, `onnxruntime_cpu`, `torch_cpu`, `tensorrt_gpu`.
2. Stage 32 itself does not enable GPU.

`resource_requirements`:
1. Capture expected CPU, memory, and optional GPU needs.
2. Must inform deployment planning and rollout policy.

`approval_status`:
1. Must reflect lifecycle state and governance state.

`evaluation_summary`:
1. Captures offline validation, shadow comparison, canary summary, and known caveats.

`limitations`:
1. Must state known failure modes and scope limits.

`created_by`, `approved_by`, `created_at`, `approved_at`:
1. Provide governance accountability.

## 6. `.pth / Model Artifact Rule`

1. The system must not scan, copy, move, or guess paths for `.pth`, `.pt`, `.onnx`, `.ckpt`, or `.safetensors` artifacts.
2. If a future feature needs a model file, the main controller must ask the user to provide the exact path first.
3. Only after the user provides the exact path may the artifact be registered as `artifact_uri`.
4. Before entry into the registry, the artifact must have a recorded `artifact_hash`, version, source, and intended use.
5. Model files must not be committed to Git.
6. Artifact registration is a controlled governance step, not a filesystem discovery step.

## 7. How LLM / Orchestrator Knows New Models

1. The LLM does not discover `.pth` files by itself.
2. The orchestrator reads `model_registry` and `disease_agent` registry metadata.
3. The LLM only sees capability summaries, version states, and policy-safe metadata.
4. The LLM must not see or choose local file paths.
5. The final call selection is constrained by backend policy and approval state.
6. If a model is not registered, approved, and policy-eligible, the orchestrator must not select it.

## 8. Version Selection Policy

### 8.1 Selection modes

1. `approved_only`
2. `latest_approved`
3. `pinned_version`
4. `shadow`
5. `canary`
6. `default`
7. `rollback_to_version`
8. `no_silent_fallback`

### 8.2 Policy meaning

`approved_only`:
1. Only versions in approved family states can be selected.

`latest_approved`:
1. Select the newest approved version within the disease/task/modality scope.

`pinned_version`:
1. Select exactly one version by ID.
2. Used for controlled comparisons or rollback.

`shadow`:
1. Allow mirrored execution against the selected version.
2. Results do not drive doctor-facing recommendations.

`canary`:
1. Allow limited real traffic.
2. Must be constrained by rollout policy.

`default`:
1. Use the current promoted default version.

`rollback_to_version`:
1. Move selection back to a prior approved version.
2. Must be explicit and auditable.

`no_silent_fallback`:
1. Any fallback must be visible in trace and evidence.
2. No hidden model substitution is allowed.

## 9. No Downtime Model Iteration

The lifecycle must support nonstop operation while new versions are introduced.

Recommended path:
1. Register a new version as `draft`.
2. Attach artifact metadata and governance metadata.
3. Perform `offline_evaluated` review.
4. Mark as `approved`.
5. Run `shadow` comparison against the current default.
6. Run limited `canary` traffic if policy allows.
7. Promote to `default` if results are better and acceptable.
8. Keep the previous default version available as a rollback target.
9. Record every invocation with `model_version_id` in trace.

Operational consequences:
1. No service downtime is required for version promotion.
2. Rollback is a policy change, not a redeploy requirement.
3. Historical versions remain queryable for trace and audit.
4. Old versions are not deleted prematurely.

## 10. How To Know New Model Is Better

A new model cannot become default based on a single successful example or an informal impression.

Required evidence sources:
1. Offline validation set metrics.
2. Shadow run comparison.
3. Canary performance.
4. Doctor feedback.
5. Quality review outcomes.
6. Missing-value sensitivity analysis.
7. Calibration and uncertainty behavior.
8. Latency and failure rate.
9. Subgroup performance.

Policy rule:
1. A version must show an improvement pattern across the relevant evidence set before it can replace the default.
2. A single trace or a handful of manual approvals is not enough.
3. If uncertainty or calibration worsens, the version must not be promoted just because one headline metric improved.
4. If subgroup performance regresses, the version should remain approved but not default until resolved.

Decision inputs:
1. `evaluation_summary`.
2. `doctor_feedback` aggregation.
3. `quality_review` closure outcomes.
4. `trace` evidence of real-world behavior.
5. `missing-value` sensitivity and failure rate signals.

## 11. Trace / Evidence Requirements

Every model selection and every model invocation must emit trace-bound records.

Required events:
1. `model_selected`
2. `model_invoked`
3. `model_result_received`
4. `orchestrator_decision`

Required identifiers and fields:
1. `trace_id`
2. `inference_task_id`
3. `model_version_id`
4. `model_invocation_id`
5. `model_id`
6. `fallback_reason` nullable
7. `runtime_stub_or_real_model_flag`
8. `artifact_hash` or registry reference
9. `model_registry_ref`
10. `approval_state`

Rules:
1. `trace_id` must be inherited from upstream and never replaced.
2. `model_version_id` must be stored on every invocation and result.
3. Fallback reasons must be explicit.
4. If a stub path is used, the trace must say so.
5. Evidence must link the invocation to the registry record and not to an untracked file path.

## 12. Database / API Draft

This stage does not execute migrations. The following API surface is the contract draft for later backend work.

### 12.1 Proposed APIs

1. `GET /api/v1/model-registry`
2. `POST /api/v1/model-registry`
3. `GET /api/v1/model-registry/{model_id}`
4. `POST /api/v1/model-registry/{model_id}/versions`
5. `POST /api/v1/model-versions/{version_id}/approve`
6. `POST /api/v1/model-versions/{version_id}/promote`
7. `POST /api/v1/model-versions/{version_id}/rollback`
8. `GET /api/v1/model-versions/{version_id}/evaluations`

### 12.2 Suggested contract objects

`model_registry`:
1. Model family metadata.
2. Available task and modality capabilities.
3. Default version pointer.

`model_versions`:
1. Version metadata.
2. Artifact metadata.
3. Lifecycle state.
4. Evaluation and approval metadata.
5. Rollout flags such as shadow, canary, default.

`model_version_evaluations`:
1. Evaluation summary references.
2. Offline metrics.
3. Shadow/canary outcomes.
4. Quality review links.

`model_version_rollouts`:
1. Current rollout mode.
2. Promotion and rollback events.
3. Scope restrictions.

### 12.3 Relationship to trace and quality systems

1. Model registry records must reference trace IDs when a rollout decision comes from observed behavior.
2. Quality review records must be able to point back to the model version that produced the problematic recommendation or output.
3. Doctor feedback must be aggregatable by model version.

## 13. Frontend Impact

Future model management pages must display:
1. Model list.
2. Version list.
3. Lifecycle state.
4. Supported diseases, tasks, and modalities.
5. Evaluation metrics.
6. Shadow, canary, and default status.
7. Rollback controls.
8. Approval history.
9. Trace linkage.

Display rule:
1. Frontend should show registry state and governance state, not file-system paths.
2. Users should see version policy and rollout state clearly.
3. Artifact hash and registry references should be visible to authorized users for audit.

## 14. Stage Plan

Recommended next stages:
1. Stage 33: backend model registry CRUD skeleton.
2. Stage 34: frontend model management page integration.
3. Stage 35: shadow/canary strategy skeleton.
4. Stage 36: model artifact registration workflow.
5. Stage 37: real model integration prep, which requires the user to provide an exact artifact path.

## 15. Main-Controller Writeback Summary

1. Stage 32 model registry and version lifecycle contract is now defined.
2. Lifecycle states `draft`, `offline_evaluated`, `approved`, `shadow`, `canary`, `default`, `deprecated`, and `archived` are frozen for contract design.
3. No-downtime iteration is defined as register -> offline evaluate -> approve -> shadow -> canary -> promote default -> retain old version -> rollback if needed.
4. New model superiority must be proven with offline metrics, shadow/canary behavior, doctor feedback, quality review, missing-value sensitivity, calibration, latency, failure rate, and subgroup performance.
5. LLM/orchestrator discovery must come from registry metadata, never from filesystem scanning or file-path guessing.
6. `.pth` artifacts remain user-provided, hash-tracked, Git-excluded, and never guessed or scanned.
7. Stage 33 backend registry skeleton is the recommended next step if the main controller wants implementation after this contract.
