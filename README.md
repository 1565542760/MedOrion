# MedOrion

MedOrion is a local-first clinical AI workflow skeleton for doctor-facing decision support research. The project currently provides a runnable MVP skeleton with backend, frontend, model-service, traceability, model registry, agent gateway, orchestration audit, model input validation, and shadow audit UI.

This repository is not a real diagnostic product. It is a governed integration skeleton for gradually connecting small models, LLM orchestration, doctor feedback, quality review, provenance, and shadow evaluation.

## Current Stage

**Stage 123: CAP/COP clinical MLP shadow usable baseline.**

The system can run end-to-end in local tunnel mode and now includes a usable CAP/COP clinical MLP fold5 shadow baseline. This shadow path can load the authorized fold5 artifact through a temporary CPU-only runner bridge, execute a one-shot shadow run from a validated input snapshot, write shadow audit run/output records, and display the result in the frontend shadow audit page with explicit safety warnings.

The system supports the following MVP skeleton capabilities:

- Auth/RBAC skeleton with development user login.
- Formal patient and case creation.
- Stub inference through backend -> model-service.
- Trace/evidence persistence for inference, missing-value consultation, feedback, and quality review.
- Missing-value consultation with doctor answer and default strategy paths.
- Doctor feedback loop and quality review loop.
- Model registry lifecycle skeleton with model/version metadata and lifecycle state management.
- Agent Gateway skeleton with capability validation and explicit no-silent-fallback behavior.
- Multi-agent orchestration skeleton with persistent orchestration audit tables.
- Model input schema / feature mapping skeleton with CAP/COP validation and selection preview.
- Shadow audit schema, read API, controlled development write skeleton, one-shot clinical MLP shadow bridge, and frontend shadow audit page. Clinical MLP fold5 is usable as a shadow baseline only.
- CAP/COP clinical MLP onboarding artifacts documented through dry-run, offline evaluation, metadata/provenance finalization, runner review, bridge review, output metadata review, and shadow UI review.

## What This Is Not

MedOrion is still not:

- A real diagnosis system.
- A production medical device.
- A formal real-model diagnosis service.
- An automatic training system.
- A public internet deployment.
- A GPU production serving stack.
- A system that can silently choose a fallback model when the requested model or agent is unavailable.

Real model work remains gated. CAP/COP clinical MLP fold5 is now a **usable shadow baseline**, not a default model, not canary, not a formal recommendation path, not production deployment, not externally validated, not an automatic training system, and not a doctor replacement.

## Repository Layout

```text
/home/sygxdg/MedOrion
??? app/
?   ??? backend/          # FastAPI backend, API contracts, DB models, Alembic migrations
?   ??? frontend/         # Next.js frontend doctor workbench
?   ??? model-service/    # FastAPI model-service stub and CAP/COP adapter skeletons
??? deploy/               # Local deployment / compose assets
??? docs/
    ??? architecture/     # Source-of-truth architecture notes
    ??? backend/          # Backend contracts and migration plans
    ??? model_orchestration/
    ??? releases/
    ??? traceability/
```

Runtime files live under `/srv/medorion`. The Git repository is the source of truth; runtime is the deployed/synchronized working tree.

## Runtime Layout

```text
/srv/medorion
??? app/backend
??? app/frontend
??? app/model-service
??? models/agents/cap_cop_classifier_agent/v1.0.0
??? model-evaluation/cap_cop_clinical_mlp/stage56
```

The isolated CAP/COP agent artifact area contains copied model research artifacts needed for onboarding. It exists to avoid polluting the original MRI3DModel research folder. Datasets are not copied into the system artifact area.

## Local Service Endpoints

All services are local-only unless explicitly changed in a later approved deployment stage.

- Frontend: `127.0.0.1:3000`
- Backend: `127.0.0.1:8000`
- Model-service: `127.0.0.1:8100`
- PostgreSQL: local compose service
- Redis: local compose service
- MinIO: local compose service
- Nginx: disabled / inactive

Frontend calls backend through same-origin proxy:

```text
/backend-api -> http://127.0.0.1:8000
```

## Access From Local Machine

Use SSH tunneling:

```bash
ssh -L 3000:127.0.0.1:3000 sygxdg@100.73.42.19
```

Then open:

```text
http://127.0.0.1:3000/login
```

Only port `3000` needs to be tunneled for normal UI testing because the frontend proxies backend requests through `/backend-api`.

## Core Workflow Skeleton

### Auth

The backend exposes minimal development auth. The frontend stores development session material in localStorage and protects doctor workbench routes client-side. This is sufficient for local MVP skeleton testing, not production security hardening.

### Patient and Case

Patients and cases are real database records. Inference, trace, evidence, missing-value consultation, feedback, quality review, orchestration audit, and shadow audit all bind back to case and patient identifiers where relevant.

### Inference and Trace/Evidence

The current regular inference path still uses stub/model-service behavior. It writes trace and evidence records for the doctor-facing recommendation skeleton. The result is explicitly not for diagnosis.

### Missing Values

Missing-value consultation supports:

- Detect/query missing value.
- Doctor-provided answer.
- Explicit default strategy application.
- Traceable distinction between `doctor_provided` and `default_applied`.

Required fields must not silently fall back. If a required feature is missing and cannot be supplied or defaulted, the system must return `insufficient_data_for_assessment`.

### Feedback and Quality Review

Doctor feedback and quality review are independent audit objects. They do not overwrite recommendations. They can be queried by case and trace, and they emit appropriate trace events.

### Model Registry

The model registry stores model and version metadata, lifecycle state, approval/promote/rollback metadata, and artifact metadata. It does not load model files by itself.

Lifecycle states include:

```text
draft, offline_evaluated, approved, shadow, canary, default, deprecated, archived
```

### Agent Gateway and Orchestration

The Agent Gateway is a unified entry layer for agent capability validation and model-service calls. It does not silently fallback.

The orchestration skeleton supports single and multi-agent run shapes. Persistent orchestration audit is stored separately in:

- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

This audit trail is intentionally separate from case trace/evidence. Only clinically meaningful final outputs may later be promoted into case trace/evidence after explicit design and approval.

## CAP/COP Model Onboarding Status

The CAP/COP disease task currently has three planned small-model families:

- `clinical_mlp_cap_cop_classifier`
- `imaging_resnet18_cap_cop_classifier`
- `multimodal_resnet18_cap_cop_classifier`

Adapter codes:

- `clinical_mlp_cap_cop_adapter`
- `imaging_resnet18_cap_cop_adapter`
- `multimodal_resnet18_cap_cop_adapter`

Current real-model status:

- Clinical MLP fold5 has a usable shadow baseline through a temporary CPU-only runner bridge.
- Clinical MLP fold5 metadata/provenance has been finalized and the authorized artifact hash has been verified.
- Clinical MLP fold5 can produce one-shot shadow audit runs/outputs from a validated `case_model_input_snapshot`.
- The frontend shadow audit page can display the clinical MLP shadow result with calibration and clinical-use warnings.
- Imaging ResNet18 and multimodal ResNet18 remain unconnected to real shadow execution.
- No model is approved as default or canary.
- No real model is live in formal doctor-facing recommendation or diagnosis.

### CAP/COP Feature Contract

`cap_cop_clinical_feature_set_v1` is a disease-task-level clinical feature set, not a global case table shape.

The current CAP/COP clinical feature set has 36 task-related fields. `Striated_shadow.1` is intentionally preserved because it reflects the historical pandas duplicate-column handling used by the training pipeline. It belongs to the CAP/COP feature set, not to a global case table.

Model input schemas may reference the full feature set or a subset. Future models can define different feature requirements and mappings without changing the global patient/case storage model.

## Shadow Audit

Shadow audit is available as a controlled subsystem:

- Backend schema exists.
- Read APIs exist.
- Controlled development write endpoint exists.
- CAP/COP clinical MLP fold5 one-shot shadow bridge exists and writes only shadow audit records.
- Frontend shadow audit page exists at `/cases/{case_id}/shadow-audit`. It is for shadow audit visibility only, not for live diagnosis.

Shadow audit does not write formal recommendations, does not write case evidence chains by default, and does not imply clinical validity.

## Development Boundaries

Do not do any of the following without explicit approval:

- Enable Nginx or public exposure.
- Commit sensitive credentials, logs, data directories, or model files.
- Scan, guess, copy, move, or load model files outside an explicitly authorized path and stage.
- Train or automatically retrain models.
- Enable live real-model diagnosis.
- Promote a model to default based on dry-run or low-evidence retrospective checks alone.
- Mix orchestration audit noise into case evidence chains.


## Course Project Integration

MedOrion is also being organized as a course-project substrate for `???????????`. The course-facing work is documented under `docs/coursework/` and maps the existing CAP/COP doctor workbench, shadow audit, model registry, provenance, and future imaging/digital-twin visualization work to the assessment requirements.

Coursework integration must remain scientifically conservative: the CAP/COP clinical MLP path is a shadow baseline only, and the course still needs an explicit machine vision component and a digital twin visualization layer before it can be presented as a complete machine-vision-driven digital twin project.

## Important Docs

- `docs/HANDOFF_FOR_AI.md`
- `docs/PROJECT_BOARD.md`
- `docs/architecture/SOURCE_OF_TRUTH.md`
- `docs/releases/MVP_SKELETON_STAGE_44_RELEASE.md`
- `docs/releases/STAGE_123_CAP_COP_CLINICAL_MLP_SHADOW_BASELINE.md`
- `docs/traceability/TRACEABILITY_STAGE_122_CLINICAL_MLP_SHADOW_UX_REVIEW.md`
- `docs/model_orchestration/CAP_COP_REAL_MODEL_STAGE_57_CLINICAL_MLP_SHADOW_READINESS.md`
- `docs/backend/MODEL_INPUT_SCHEMA_STAGE_58_CONTRACT.md`
- `docs/backend/SHADOW_AUDIT_STAGE_64_SCHEMA_PLAN.md`

## Version Baseline

- MVP skeleton release tag: `v0.2.0-mvp-skeleton`
- Current post-release capability includes model input preview and shadow audit UI.
- Latest pre-Stage-69 checkpoint before this documentation update: `2d19ae8 feat: add shadow audit UI`
