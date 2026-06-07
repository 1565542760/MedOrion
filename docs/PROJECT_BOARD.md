# PROJECT_BOARD

Last updated: 2026-06-08 Asia/Shanghai

## Current Stage

**Stage 123: CAP/COP clinical MLP shadow usable baseline.**

The project is runnable as a local MVP skeleton. It supports doctor workbench flows, trace/evidence skeletons, model registry, agent/orchestration audit, model input validation, snapshot provenance, access audit, shadow audit viewing, and a usable CAP/COP clinical MLP fold5 shadow baseline.

It is not a real diagnostic system. The clinical MLP path is shadow only, not a formal recommendation, not default/canary, not production deployment, and not externally validated.

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
| Clinical MLP fold5 shadow baseline | Complete - one-shot CPU-only bridge writes shadow audit output and frontend displays it with warnings |
| Snapshot provenance and access audit | Complete baseline - snapshot write/read, privacy hardening, case ownership helper, access audit emit/read skeleton |

## CAP/COP Model Onboarding Board

| Item | Current Status | Notes |
| --- | --- | --- |
| Clinical MLP adapter | Usable shadow baseline | Temporary CPU-only runner bridge, not formal recommendation or diagnosis |
| Clinical MLP fold1 | Historical dry-run passed | Superseded by fold5 shadow baseline work |
| Clinical MLP fold5 | Usable shadow baseline | Metadata/provenance finalized, hash verified, one-shot shadow output available; not default/canary |
| Imaging ResNet18 adapter | Skeleton/disabled | No real loading |
| Multimodal ResNet18 adapter | Skeleton/disabled | No real loading |
| Feature set | `cap_cop_clinical_feature_set_v1` | 36 CAP/COP task-related fields, includes `Striated_shadow.1` |
| Model input schema | Skeleton/API/UI complete | Not a global case table shape |
| Shadow audit | Schema/API/UI complete | Separate from formal recommendation/evidence |

## Current Boundaries

- Real adapters remain disabled for formal live inference.
- Clinical MLP fold5 is usable only as a shadow baseline through a temporary runner bridge.
- Clinical MLP fold5 shadow output is not a diagnosis, not a formal recommendation, not default/canary, not production deployment, and not externally validated.
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

1. Stage 123 clinical MLP shadow usable baseline status/release update.
2. Imaging ResNet18 provenance + runner plan if the goal is three-model CAP/COP shadow.
3. Multimodal ResNet18 provenance + runner plan after imaging or in a separate reviewed lane.
4. Model-service or inference-service migration away from the temporary MRI3D runner bridge.
5. Clinical MLP further validation / external held-out-set plan.
6. Access/shadow audit frontend polish.

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
