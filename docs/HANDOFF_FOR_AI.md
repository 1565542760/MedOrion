# HANDOFF FOR AI

## Purpose

This document is the handoff guide for a new AI session or a new specialized conversation taking over MedOrion.

Its purpose is to prevent drift, unsafe changes, unintended service operations, and accidental interaction with model artifact files.

## Project Identity

- Project: MedOrion
- Positioning: A multimodal medical intelligent-agent assisted diagnosis platform for doctors. It does not replace physician diagnosis.
- CAP/COP is the first-stage demonstration disease task, not the only target of the system.

## Must Read First

Read in this order before making changes:

1. `README.md`
2. `docs/architecture/SOURCE_OF_TRUTH.md`
3. `docs/PROJECT_BOARD.md`
4. `docs/backend/BACKEND_STAGE_02_SCHEMA_API_PLAN.md`
5. `docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md`
6. `docs/traceability/TRACEABILITY_STAGE_14_REVIEW.md`
7. `docs/traceability/TRACEABILITY_STAGE_15_QUICK_REVIEW.md`
8. `docs/model_orchestration/MODEL_ORCHESTRATION_STAGE_01_CONTRACT.md`

## Current Stage

- Current stage: Stage 30: MVP workflow skeleton through quality review completed
- Latest commit: `09591b9`

Current capabilities:

- `frontend -> backend -> model-service stub -> backend -> frontend`
- Minimal trace/evidence persistence loop is in place.
- `model_selected` plus five-class trace event audit semantics are present.
- Formal patient/case creation is in place.
- Missing-value consultation, doctor feedback, and quality review flows are in place.

Current system is not:

- A real diagnosis system
- A real model inference system
- A real training system
- A public production deployment

## Remote Server

- Remote server: `ssh sygxdg@100.73.42.19`
- All implementation work must run on the remote server, not on the local workstation.

## Repository vs Runtime

- Git repository: `/home/sygxdg/MedOrion`
- Runtime/deployment directory: `/srv/medorion`
- Update repository code first, verify, then sync/deploy to runtime directory.
- Do not commit runtime data, logs, secrets, or model weights.

## Current Running Services

- frontend: `127.0.0.1:3000`
- backend: `127.0.0.1:8000`
- model-service stub: `127.0.0.1:8100`
- PostgreSQL: `127.0.0.1:5432`
- Redis: `127.0.0.1:6379`
- MinIO: `127.0.0.1:9000/9001`
- Nginx: disabled/inactive

## Access Pattern

SSH tunnel:

```bash
ssh -L 3000:127.0.0.1:3000 sygxdg@100.73.42.19
```

Browser:

```text
http://127.0.0.1:3000
```

## Conversation Responsibilities

- General architecture and decision control: single source of truth, scheduling center, architecture arbitration.
- Deployment and MLOps: server, Docker, Compose, Nginx, backup, runtime environment, Git checkpoints.
- Backend API and database: FastAPI, database, API, Alembic, case/patient/task/feedback, trace API.
- Small model and agent orchestration: model-service, disease agent, model schema, orchestration flow.
- Traceability and quality control: trace_id, evidence chain, missing-value audit, quality rules.
- Frontend doctor workstation: doctor-side pages, multimodal views, missing-value confirmation, recommendation/trace/feedback display.

## Non-Negotiable Rules

- Do not commit `.env`.
- Do not commit secrets.
- Do not commit `data/logs/object-storage/backups`.
- Do not commit model weights: `.pth/.pt/.onnx/.ckpt/.safetensors`.
- Do not scan, copy, move, or guess model file paths. Ask controller/user first when model files are needed.
- Do not implement automatic real-time training.
- Do not treat dynamic condition feedback as real-time training.
- Do not enable Nginx or public exposure unless explicitly approved by controller.
- Do not enable GPU unless entering a dedicated GPU stage.
- Do not change schema or run Alembic unless explicitly allowed by task scope.

## Trace and Evidence Invariants

- Every recommendation must bind to a `trace_id`.
- model-service must not generate or replace `trace_id`.
- Backend inference task is the canonical `trace_id` owner.
- Current event order:
  1. `inference_task_created`
  2. `model_selected`
  3. `model_invoked`
  4. `model_result_received`
  5. `recommendation_generated`
- Current minimal evidence graph:
  - `model_output`
  - `recommendation`
  - `supports`
- All stub outputs must include `runtime_stub:true` or equivalent limiting semantics.

## Known Temporary Risks

- `case-001` stub anchor is temporary and should later be replaced by formal case creation flow.
- model-service is stub-only.
- Frontend lineage is MVP-level.
- Frontend quality review UI may still need polish and deeper validation.
- Real model lifecycle management is not in place.
- Login/permission system is not in place.
- Externalized database backup/restore drills are not yet completed.
- No causal analysis module exists yet; it is reserved for future expansion.

## Recommended Next Steps

- Design the minimum authentication and authorization scheme.
- Implement formal case creation flow and replace `case-001` stub anchoring.
- Continue with frontend UI polish.
- Add the first round of frontend quality review integration.
- Proceed to model registry/version lifecycle management.
- Strengthen deployment with Nginx/HTTPS, backup restoration, and database externalization drills.
- Real `.pth` model integration must wait for controller-approved, user-provided path input.
- Investigate causal analysis / counterfactual reasoning only in a later stage.
