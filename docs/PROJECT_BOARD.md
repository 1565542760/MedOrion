# MedOrion Project Board

Last updated: 2026-06-02 Asia/Shanghai
Owner: MedOrion general architecture and scheduling thread

## Current Stage

Stage 42 preparation is now the current focus. The platform has moved beyond the initial stub-only demo loop and now includes authentication, frontend login/proxy flow, formal patient/case creation, model-service stub integration, trace/evidence persistence, missing-value consultation, doctor feedback, quality review, model registry lifecycle skeleton, agent gateway skeleton, multi-agent orchestration skeleton, and orchestration audit persistence.

## Global Blocker

No hard blocker is currently preventing continuation. The system remains stub-only and must not be treated as a real diagnosis platform.

## Backend Status

- Backend container: medorion-backend-1 running
- Binding: 127.0.0.1:8000 -> 8000/tcp
- /health/live: 200
- /health/ready: 200
- /health: 200
- Domain API stubs: implemented
- Pydantic schema stubs: implemented
- request_id/trace_id logging: verified in container logs

## Implemented Backend Stub Groups

- /api/v1/auth
- /api/v1/patients
- /api/v1/cases
- /api/v1/cases/{case_id}/traces
- /api/v1/cases/{case_id}/inputs
- /api/v1/cases/{case_id}/missing-values
- /api/v1/cases/{case_id}/recommendations
- /api/v1/cases/{case_id}/inference-tasks
- /api/v1/inference-tasks/{task_id}
- /api/v1/reassessment-jobs
- /api/v1/model-registry
- /api/v1/feedback
- /api/v1/traces/{trace_id}
- /api/v1/traces/{trace_id}/events
- /api/v1/traces/{trace_id}/evidence-chain
- /api/v1/quality-reviews

## Current Rule

Frontend may initialize under `/srv/medorion/app/frontend` and use local backend stubs. Do not enable Nginx, do not expose public routes, do not start model-service beyond the stub already in use, and do not perform `.pth` file operations.

Orchestration audit persistence is currently limited to the orchestration audit tables and must not automatically write into case trace/evidence tables unless a later stage explicitly says so.

## Global File Safety Constraint

If any later task needs a deep-learning `.pth` model file, no thread may scan, copy, move, or infer paths from other project folders. The thread must report the need to the main controller, and the main controller will ask the user for the exact file location.

## Running Infra

| Service | Status | Binding |
| --- | --- | --- |
| Backend | running | 127.0.0.1:8000 -> 8000/tcp |
| PostgreSQL | healthy | 127.0.0.1:5432 -> 5432/tcp |
| Redis | healthy | 127.0.0.1:6379 -> 6379/tcp |
| MinIO API | healthy | 127.0.0.1:9000 -> 9000/tcp |
| MinIO Console | healthy | 127.0.0.1:9001 -> 9001/tcp |
| Frontend | running | 127.0.0.1:3000 -> 3000/tcp |
| model-service | running | 127.0.0.1:8100 -> 8100/tcp |

## Conversation Status

| Conversation | Status | Current Instruction |
| --- | --- | --- |
| MedOrion-???????? | Active | Maintain source of truth, decisions, and scheduling board. |
| MedOrion-??????? | Active next | Continue UI polish and validation around auth, case, feedback, and quality review flows. |
| MedOrion-???MLOps | Monitor | Keep infra healthy; do not enable Nginx or public exposure. |
| MedOrion-??API???? | Hold | Support contract gaps only; no unnecessary new business logic. |
| MedOrion-????????? | Hold | Wait for future model registry and real model onboarding readiness. |
| MedOrion-??????? | Hold | Optional later verification of trace and quality review behavior. |

## Next Required Return From Frontend Thread

1. Frontend project path and package manager.
2. Chosen stack and dependency versions.
3. Route/page skeleton created.
4. Mock API adapter design and base URL configuration.
5. Backend stub endpoints consumed successfully.
6. Whether local frontend dev server runs and on which localhost port.
7. Confirmation Nginx remains disabled and no public exposure was added.
8. Confirmation no model-service, training, or `.pth` operation occurred.
9. Any backend stub contract gaps discovered.
10. What should be added to SOURCE_OF_TRUTH.md or docs/decisions.
