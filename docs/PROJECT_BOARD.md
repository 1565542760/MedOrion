# PROJECT_BOARD

Last updated: 2026-06-04 Asia/Shanghai

## Current Stage

**Stage 80: CAP/COP clinical MLP shadow governance baseline fixed.**

The project is runnable as a local MVP skeleton. It supports doctor workbench flows, trace/evidence skeletons, model registry, agent/orchestration audit, model input validation, and shadow audit viewing. CAP/COP clinical MLP fold5 remains a shadow candidate only and is not enabled.

It is not a real diagnostic system and does not run live real-model inference in the doctor-facing path.

## Current Service State

Expected local-only runtime:

| Service | Endpoint | Status Expectation |
| --- | --- | --- |
| Frontend | `127.0.0.1:3000` | Next.js dev server |
| Backend | `127.0.0.1:8000` | FastAPI API |
| Model-service | `127.0.0.1:8100` | FastAPI model-service skeleton |
| PostgreSQL | compose internal/local | running |
| Redis | compose internal/local | running |
| MinIO | compose internal/local | running |
| Nginx | none | disabled/inactive |

Access is through SSH tunnel to port `3000`.

## Completed Milestones

| Area | Status |
| --- | --- |
| Foundation backend/frontend/model-service stub | Complete |
| Git baseline and release checkpoint | Complete |
| Auth/RBAC skeleton | Complete |
| Frontend login/proxy flow | Complete |
| Formal patient/case creation | Complete |
| Inference trace/evidence loop | Complete |
| Missing-value consultation loop | Complete |
| Doctor feedback loop | Complete |
| Quality review loop | Complete |
| Model registry lifecycle skeleton | Complete |
| Model registry frontend UI | Complete |
| Agent Gateway skeleton | Complete |
| Multi-agent orchestration skeleton | Complete |
| Persistent orchestration audit | Complete |
| MVP skeleton acceptance | Complete |
| Real model onboarding contracts | Complete |
| CAP/COP clinical MLP dry-run | Complete for fold1 only |
| CAP/COP clinical MLP offline evaluation | Complete, low-evidence/internal retrospective |
| Model input schema and selection skeleton | Complete |
| Frontend model input preview UI | Complete |
| Shadow audit schema/read API | Complete |
| Controlled shadow audit write skeleton | Complete |
| Frontend shadow audit UI | Complete |

## CAP/COP Model Onboarding Board

| Item | Current Status | Notes |
| --- | --- | --- |
| Clinical MLP adapter | Draft/disabled | Architecture and dry-run helper exist; not live |
| Clinical MLP fold1 | Dry-run passed | Single artifact structure and dummy forward only |
| Clinical MLP fold5 | Shadow candidate | Best retrospective fold; not default |
| Imaging ResNet18 adapter | Skeleton/disabled | No real loading |
| Multimodal ResNet18 adapter | Skeleton/disabled | No real loading |
| Feature set | `cap_cop_clinical_feature_set_v1` | 36 CAP/COP task-related fields, includes `Striated_shadow.1` |
| Model input schema | Skeleton/API/UI complete | Not a global case table shape |
| Shadow audit | Schema/API/UI complete | Separate from formal recommendation/evidence |

## Current Boundaries

- Real adapters are disabled for live inference.
- Fold5 is only a shadow candidate; the allowlist remains empty, so shadow execution is not enabled.
- Shadow audit records are not formal diagnosis and are not formal recommendations.
- Orchestration audit and shadow audit are separate from case evidence chains.
- Missing required model features must result in consultation, explicit default strategy, or `insufficient_data_for_assessment`.
- No silent fallback is allowed.

## Active Risks

| Risk | Current Mitigation |
| --- | --- |
| Confusing shadow candidate with production model | Docs and UI state must keep `shadow`, `not_for_diagnosis`, and disabled/live boundaries visible |
| Historical CAP/COP schema overfitting the whole system | Separate `disease_task_feature_set` from `model_input_schema` |
| Runtime code lagging behind repo | Always verify container/runtime endpoints after sync |
| Model file safety | Only touch explicitly authorized single artifact path and stage |
| Lack of independent clinical validation | Keep evaluation labelled low evidence/internal retrospective |
| Dev-only shadow write endpoint misuse | Keep explicit `runtime_stub=true` and `not_for_diagnosis=true`; consider future env gate |

## Suggested Next Work

Short-term safe options:

1. Stage 69 documentation/release checkpoint.
2. Governance sign-off / no-go maintenance and readiness documentation, still not live/default.
3. Frontend readability pass for model input and shadow audit pages.
4. Admin/RBAC hardening.
5. Deployment hardening plan: HTTPS/Nginx, backup/restore, external DB rehearsal.

Avoid for now:

- Real live diagnosis.
- Default model promotion.
- Automatic training.
- Public deployment.
- Broad model directory scanning.

## Conversation Routing

| Work Type | Preferred Thread |
| --- | --- |
| Stage decision, documentation, Git checkpoint | Main controller |
| Backend APIs, DB, migrations, containers | Backend/deployment |
| Browser pages, warnings, UI routing | Frontend |
| Provenance, audit, trace/evidence review | Traceability/review |
| Model onboarding, adapters, artifact rules | Model/onboarding |

When in doubt, the main controller should decide stage order and produce the exact prompt for the target thread.
