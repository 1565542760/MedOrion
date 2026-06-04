# SOURCE_OF_TRUTH

## Purpose

This document defines the architectural source of truth for MedOrion at the current stage. It should be used to prevent confusion between runnable MVP skeleton capabilities, shadow/onboarding work, and real clinical deployment.

## Current Architecture Stage

**Stage 69: MVP skeleton with CAP/COP clinical MLP shadow readiness and shadow audit UI completed.**

The platform is a local-only, traceable clinical AI workflow skeleton. It can demonstrate the structure of a doctor-facing AI workbench, but it is not a real diagnostic system.

## System Components

```text
Browser
  -> Next.js frontend on 127.0.0.1:3000
      -> /backend-api rewrite
          -> FastAPI backend on 127.0.0.1:8000
              -> PostgreSQL / Redis / MinIO
              -> model-service on 127.0.0.1:8100
```

Nginx is disabled. There is no public production exposure.

## Backend Responsibilities

Backend owns:

- Auth/RBAC skeleton.
- Patient and case records.
- Inference task orchestration into model-service stub/agent gateway.
- Trace/evidence persistence for clinically meaningful skeleton outputs.
- Missing-value consultation.
- Doctor feedback.
- Quality review.
- Model registry and lifecycle metadata.
- Model input schema and feature mapping skeleton.
- Orchestration audit persistence.
- Shadow audit storage and read/write skeleton.

Backend must not silently fallback between models or agents.

## Frontend Responsibilities

Frontend owns doctor-facing workflow pages:

- Login and route protection.
- Dashboard and cases.
- Missing-value consultation.
- Small-model analysis stub.
- Lineage/trace viewing.
- Feedback and quality review.
- Model registry UI.
- Model input preview and validation UI.
- Shadow audit UI.

Frontend must label stub/shadow/not-for-diagnosis states clearly.

## Model-Service Responsibilities

Model-service currently provides:

- Existing stub inference behavior.
- CAP/COP real adapter skeletons.
- Registry metadata for CAP/COP skeleton versions.
- Explicit disabled responses for real adapters.

Model-service currently does not provide live real-model diagnosis. Normal operation must not load `.pth/.pt/.onnx/.ckpt/.safetensors` files.

## Data Boundary

The global patient/case model must not be shaped around one historical model input table.

Use layered contracts:

1. `disease_task_feature_set`: disease/task-level clinical attributes.
2. `model_input_schema`: model-version-specific required input shape.
3. `clinical_feature_mapping`: mapping from system data to model feature names.
4. `case_model_input_snapshot`: future audit object for exact model input used.

For CAP/COP:

- `cap_cop_clinical_feature_set_v1` has 36 task-related clinical fields.
- `Striated_shadow.1` is intentionally preserved as part of the historical training schema.
- Clinical MLP and multimodal ResNet18 may reference this feature set.
- Future models may define different schema requirements.

## Audit Boundary

### Case Trace/Evidence

Formal case trace/evidence should include clinically meaningful events and evidence, such as:

- inference task creation/result
- missing-value consultation answer/default
- recommendation generation
- doctor feedback
- quality review

### Orchestration Audit

Orchestration audit is stored separately:

- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

This should not be dumped wholesale into case evidence.

### Shadow Audit

Shadow audit is stored separately:

- `shadow_inference_runs`
- `shadow_inference_outputs`

Shadow audit is for background/offline comparison and governance. It is not a formal recommendation and not a diagnosis.

## Real Model Governance

Real model onboarding must follow this order:

1. Explicit user-provided artifact path.
2. Metadata registration.
3. Hash verification for that single authorized artifact.
4. CPU-only dry-run structure check.
5. Offline evaluation.
6. Registry approval.
7. Shadow candidate decision.
8. Shadow execution behind explicit switch.
9. Canary only after review.
10. Default only after stronger validation and approval.

Dry-run and internal retrospective evaluation do not justify default promotion.

## CAP/COP Current Governance State

Clinical MLP:

- fold1 dry-run passed.
- fold1-fold5 retrospective evaluation completed.
- fold5 is current shadow candidate.
- evidence level is low/internal retrospective.
- not live.
- not default.

Imaging ResNet18 and multimodal ResNet18:

- artifacts organized and metadata planned.
- adapter skeletons exist.
- no real loading or inference.

## No-Silent-Fallback Rule

If a required model, agent, modality, feature, or artifact is unavailable, the system must return an explicit status/error. It must not silently switch to another model or pretend a missing input was valid.

Allowed missing-data outcomes:

- ask doctor
- apply explicit default strategy if allowed by schema
- return `insufficient_data_for_assessment`

## Production Boundary

Before any production-like deployment, MedOrion still needs:

- HTTPS/Nginx plan and approval.
- Secret management.
- Backup and restore rehearsal.
- External database migration/rehearsal if desired.
- Strong RBAC/admin workflows.
- Independent validation for real models.
- Operational monitoring.
- Safety and clinical governance review.

## Latest Pre-Stage-69 Checkpoint

`2d19ae8 feat: add shadow audit UI`
