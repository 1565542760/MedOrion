# HANDOFF_FOR_AI

## Purpose

This document is for a new AI assistant or engineer taking over MedOrion. It summarizes the current stage, hard boundaries, and safe next actions.

## Project Identity

MedOrion is a local-first doctor workbench and clinical AI orchestration skeleton. It is designed to support traceable, governed small-model and LLM-assisted workflows. The current system is a runnable MVP skeleton, not a real diagnostic product.

## Must Read First

Read these before changing code:

1. `README.md`
2. `docs/architecture/SOURCE_OF_TRUTH.md`
3. `docs/PROJECT_BOARD.md`
4. `docs/releases/MVP_SKELETON_STAGE_44_RELEASE.md`
5. `docs/model_orchestration/REAL_MODEL_ONBOARDING_STAGE_45_CONTRACT.md`
6. `docs/model_orchestration/CAP_COP_REAL_MODEL_STAGE_57_CLINICAL_MLP_SHADOW_READINESS.md`
7. `docs/backend/MODEL_INPUT_SCHEMA_STAGE_58_CONTRACT.md`
8. `docs/backend/MODEL_INPUT_SCHEMA_STAGE_59_SKELETON.md`
9. `docs/backend/SHADOW_AUDIT_STAGE_64_SCHEMA_PLAN.md`
10. `docs/traceability/TRACEABILITY_STAGE_67_SHADOW_WRITE_REVIEW.md`

## Current Stage

**Stage 80: CAP/COP clinical MLP shadow governance baseline fixed.**

The system has passed MVP skeleton acceptance and now includes a governed path toward real CAP/COP model shadow evaluation. Clinical MLP fold5 is only a shadow candidate. It is not live, not default, and not doctor-facing diagnosis. The governance state is NO-GO / pending sign-off / not enabled.

## Remote Server

- Host: `100.73.42.19`
- SSH user: `sygxdg`
- Repository: `/home/sygxdg/MedOrion`
- Runtime root: `/srv/medorion`

## Repository vs Runtime

Use `/home/sygxdg/MedOrion` as source of truth for committed work.

Use `/srv/medorion` as the running application tree. When code changes are intended to run, synchronize deliberately and verify the runtime service.

Do not assume a change is live just because it exists in the repository. Several past issues were caused by container/runtime code lagging behind repository code.

## Current Running Services

Expected services:

- frontend dev server on `127.0.0.1:3000`
- backend on `127.0.0.1:8000`
- model-service on `127.0.0.1:8100`
- postgres
- redis
- minio

Nginx should remain disabled/inactive unless a specific deployment stage approves it.

## Access Pattern

From the local machine:

```bash
ssh -L 3000:127.0.0.1:3000 sygxdg@100.73.42.19
```

Open:

```text
http://127.0.0.1:3000/login
```

The frontend uses `/backend-api` rewrites, so a separate `8000` tunnel is normally unnecessary.

## Conversation Responsibilities

The project has often been advanced through specialized conversations. Keep responsibilities clean:

- **Main controller:** decides stage order, validates summaries, owns documentation and checkpoints.
- **Backend/deployment thread:** implements backend, database, containers, and runtime checks.
- **Frontend thread:** implements UI, route, and browser-facing issues.
- **Traceability/review thread:** reviews provenance, audit semantics, and case trace/evidence boundaries.
- **Model/onboarding thread:** handles real model metadata, dry-run plans, and adapter contracts.

If work is sent to the wrong thread, it usually does not corrupt the project, but it can cause the wrong thread to review rather than implement. Re-route clearly.

## Non-Negotiable Rules

Do not:

- Enable Nginx or public exposure casually.
- Commit sensitive credentials, data, logs, or model files.
- Scan or guess model file paths.
- Touch model files except under explicit user-approved path and stage.
- Train, retrain, or enable automatic training.
- Promote a model to `default` based only on dry-run or low-evidence retrospective evaluation.
- Hide failures through silent fallback.
- Put orchestration or shadow audit noise into formal case evidence chains.

## Trace and Evidence Invariants

Case trace/evidence currently records clinically meaningful skeleton events for inference, missing values, feedback, and quality review.

Orchestration audit is separate:

- `orchestration_runs`
- `orchestration_steps`
- `agent_invocations`
- `orchestration_conflicts`
- `llm_summaries`

Shadow audit is separate:

- `shadow_inference_runs`
- `shadow_inference_outputs`

Shadow and orchestration records can be queried by trace or case, but they are not automatically formal evidence chain nodes.

## CAP/COP Current Model State

CAP/COP classification is currently represented by three planned small-model families:

- Clinical MLP
- Imaging ResNet18
- Multimodal ResNet18

Current status:

- Clinical MLP fold1 single-file dry-run succeeded.
- Clinical MLP fold1-fold5 internal retrospective evaluation completed.
- Fold5 is the current shadow candidate.
- Evidence level is low/internal retrospective; no independent held-out test has been established.
- Adapters remain disabled for normal live inference.
- No real model is used for doctor-facing diagnosis.

## Model Input Rule

`cap_cop_clinical_feature_set_v1` is a disease-task feature set, not a global patient/case table. Current CAP/COP clinical attributes include 36 fields and intentionally preserve `Striated_shadow.1`.

Use `model_input_schema` and `clinical_feature_mapping` to map system data to model-specific inputs. Future models may have very different feature requirements.

Single-model disease-task scenarios should validate the one model instead of pretending to select among models. Multi-model disease-task scenarios may rank/select candidates, but required missing fields must not silently fall back.

Allowed missing-required-field outcomes:

- ask the doctor through missing-value consultation
- apply an explicit default strategy when allowed
- return `insufficient_data_for_assessment`

## Known Temporary Risks

- Dev auth remains local/MVP-level.
- Clinical MLP fold5 is not clinically validated for production.
- Shadow write endpoint is controlled/development-oriented and must not be treated as production inference.
- Shadow and orchestration audit visibility exists, but the product UX is still skeletal.
- Real deployment hardening is not done: no HTTPS, no externalized DB plan applied, no backup/restore rehearsal.

## Recommended Next Steps

Reasonable next stages:

1. Stage 80 shadow governance status update and release note.
2. Stage 81 manual sign-off / enablement checklist or governed rehearsal planning, only if explicit approval is later granted.
3. Frontend refinement for model input and shadow audit readability.
4. Admin/RBAC hardening.
5. Production deployment plan only after local MVP boundaries are frozen.

Do not jump straight to real clinical diagnosis or default model serving.

## Latest Checkpoint Before This Document

`2d19ae8 feat: add shadow audit UI`
