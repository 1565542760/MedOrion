# MedOrion

MedOrion is a multimodal medical intelligent-agent assisted diagnosis platform for doctors. It is designed to support clinical workflows and does not replace physician diagnosis.

CAP/COP is the first-stage demonstration disease task, not the only long-term system target.

## Core Principles

- Multi-disease extensibility is a first-class requirement.
- Multimodal inputs include CT, MRI, clinical tables, EMR, lab indicators, and future wearable dynamic data.
- Disease-specific agents run on top of a shared capability foundation.
- Small models focus on disease-specific judgment; large models focus on orchestration, explanation, Q&A, and recommendation generation.
- Every recommendation must carry a `trace_id` evidence chain.
- Missing values must first trigger active doctor confirmation; default handling is allowed only after unresolved confirmation and must be recorded.
- Continuous learning is governed offline learning, not automatic real-time training.
- Dynamic condition feedback triggers reassessment, not real-time model retraining.

## Current Stage

Current stage: `Stage 30: MVP workflow skeleton through quality review completed`

Completed:

- Auth/RBAC skeleton.
- Frontend login/proxy flow.
- Formal patient/case creation.
- Model-service stub integration.
- Trace/evidence persistence.
- Missing-value consultation.
- Doctor feedback.
- Quality review.
- Infrastructure and runtime layout established.
- Backend FastAPI stub, migration baseline, stub APIs, and trace/request logging fields completed.
- Frontend doctor workstation skeleton completed with backend-mode integration.
- Frontend small-models page can trigger `POST /api/v1/cases/{case_id}/inference-tasks`.
- Frontend displays `trace_id`, `task_id`, `model_invocation_id`, `model_version_id`, `confidence`, `uncertainty`, `limitations`, `evidence_refs`.

Not completed:

- Real model inference and real model loading.
- Full production backend business CRUD coverage.
- Public Nginx entry.
- GPU inference enablement.
- Full model lifecycle management.
- Real-time or automatic learning.

## Repository Layout

- `app/backend`
- `app/frontend`
- `app/model-service`
- `deploy`
- `docs`
- `docs/architecture`
- `docs/backend`
- `docs/traceability`
- `docs/model_orchestration`
- `docs/decisions`

## Runtime Layout

- `/home/sygxdg/MedOrion` is the Git source repository.
- `/srv/medorion` is the runtime/deployment directory.
- Runtime data, logs, secrets, and model weights must not be committed to Git.

## Local Service Endpoints

- frontend: `127.0.0.1:3000`
- backend: `127.0.0.1:8000`
- model-service stub: `127.0.0.1:8100`
- PostgreSQL: `127.0.0.1:5432`
- Redis: `127.0.0.1:6379`
- MinIO: `127.0.0.1:9000/9001`

## Access From Local Machine

SSH tunnel:

```bash
ssh -L 3000:127.0.0.1:3000 sygxdg@100.73.42.19
```

Browser:

```text
http://127.0.0.1:3000
```

## Verified Stub Loop

Verified flow:

`frontend -> backend inference task -> model-service /infer stub -> backend recommendation stub -> frontend display`

This is stub-only validation and is not a medical diagnosis system.

## Development Boundaries

- Do not commit `.env` files.
- Do not commit secrets.
- Do not commit `data/logs/object-storage/backups` artifacts.
- Do not commit `.pth/.pt/.onnx/.ckpt/.safetensors` artifacts.
- Do not scan, copy, move, or guess model file paths; ask controller/user first if model files are required.
- Do not implement automatic real-time training.
- Do not treat dynamic condition feedback as real-time training.
- Keep Nginx disabled and avoid public exposure at this stage.
- Keep GPU inference disabled at this stage.

## Conversation Responsibilities

- General architecture and decision control: single source of truth, scheduling center, architecture arbitration.
- Deployment and MLOps: server, Docker, Compose, Nginx, backup, runtime environment.
- Backend API and database: FastAPI, database, API, Alembic, case/patient/task/feedback.
- Small model and agent orchestration: model-service, disease agent, model schemas, orchestration flow.
- Traceability and quality control: `trace_id`, evidence chain, missing-value audit, quality rules.
- Frontend doctor workstation: doctor UI, multimodal views, missing-value confirmation, recommendation/trace/feedback display.

## Version Baseline

- baseline commit: `b7f3268`
- baseline tag: `v0.1.0-foundation-stub`
- current checkpoint: Stage 30 MVP workflow skeleton through quality review completed
