# MedOrion Project Board

Last updated: 2026-06-01 Asia/Shanghai
Owner: MedOrion general architecture and scheduling thread

## Current Stage

Stage 07 backend API stubs and request logging are complete. The next priority is Frontend Doctor Workbench Stage 01: initialize the frontend project and implement a mock API adapter against the local backend stubs.

## Global Blocker

Frontend project is not initialized yet. Backend API stubs are available locally at 127.0.0.1:8000, but no public Nginx route should be opened.

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

Frontend may initialize under /srv/medorion/app/frontend and use local backend stubs. Do not enable Nginx, do not expose public routes, do not start model-service, and do not perform .pth file operations.

## Global File Safety Constraint

If any later task needs a deep-learning .pth model file, no thread may scan, copy, move, or infer paths from other project folders. The thread must report the need to the main controller, and the main controller will ask the user for the exact file location.

## Running Infra

| Service | Status | Binding |
| --- | --- | --- |
| Backend | running | 127.0.0.1:8000 -> 8000/tcp |
| PostgreSQL | healthy | 127.0.0.1:5432 -> 5432/tcp |
| Redis | healthy | 127.0.0.1:6379 -> 6379/tcp |
| MinIO API | healthy | 127.0.0.1:9000 -> 9000/tcp |
| MinIO Console | healthy | 127.0.0.1:9001 -> 9001/tcp |

## Conversation Status

| Conversation | Status | Current Instruction |
| --- | --- | --- |
| MedOrion-总架构与决策记录 | Active | Maintain source of truth, decisions, and scheduling board. |
| MedOrion-前端医生工作台 | Active next | Initialize frontend under /srv/medorion/app/frontend and implement mock API adapter against backend stubs. |
| MedOrion-部署与MLOps | Monitor | Keep infra healthy; do not enable Nginx or start model-service. |
| MedOrion-后端API与数据库 | Hold | Support frontend if stub contract gaps are found; no new business logic. |
| MedOrion-小模型与智能体编排 | Hold | Wait for frontend/backend adapter feedback. |
| MedOrion-溯源与质控系统 | Hold | Optional later verification of trace API behavior. |

## Next Required Return From Frontend Thread

1. Frontend project path and package manager.
2. Chosen stack and dependency versions.
3. Route/page skeleton created.
4. Mock API adapter design and base URL configuration.
5. Backend stub endpoints consumed successfully.
6. Whether local frontend dev server runs and on which localhost port.
7. Confirmation Nginx remains disabled and no public exposure was added.
8. Confirmation no model-service, training, or .pth operation occurred.
9. Any backend stub contract gaps discovered.
10. What should be added to SOURCE_OF_TRUTH.md or docs/decisions.
