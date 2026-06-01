# MedOrion Backend Stage 01 Contract

Last updated: 2026-05-31 Asia/Shanghai
Owner thread: MedOrion backend API and database
Scope: Stage 01 defines architecture and database contracts only. No full business implementation and no large Alembic rollout.

## 0. Scope and Non-Goals

MedOrion backend is a doctor-assistance platform backend, not an autonomous diagnosis system.

Stage 01 goals:
1. Define FastAPI module boundaries.
2. Define MVP database entity contract and ownership boundaries.
3. Define backend trace/evidence integration boundary.
4. Define API grouping and naming draft.
5. Define cross-thread interface requirements.

Stage 01 non-goals:
1. Full business implementation.
2. Real diagnosis logic implementation.
3. Model training or online training.
4. Frontend implementation.
5. Large migration execution.

## 1. Recommended FastAPI Module Boundaries

Suggested package layout: `app/modules/*` with `router/service/repository/schemas`, mounted by `app/api/v1`.

### 1.1 patients
Responsibilities:
1. Patient identity and de-identified external mapping.
2. Consent status and patient-level indexing for case listing.

Boundary:
1. No diagnosis conclusion logic.
2. Only patient master data and links to cases.

### 1.2 cases
Responsibilities:
1. Case master record and clinical context.
2. Case lifecycle status management.

Boundary:
1. No direct model inference execution.
2. Owns case-level validation before task creation.

### 1.3 multimodal_assets
Responsibilities:
1. Metadata and object references for CT, MRI, and related files.
2. MinIO refs: bucket/key/checksum/content_type/size.

Boundary:
1. Metadata and references only.
2. No in-module image algorithm processing.

### 1.4 clinical_tables / labs / emr
Responsibilities:
1. Structured clinical observations.
2. Lab result records.
3. EMR document metadata and extraction placeholders.
4. Missing-value detection and active doctor-question records.

Boundary:
1. No medical reasoning engine implementation.
2. No final LLM explanation generation.

### 1.5 model_registry
Responsibilities:
1. Specialized model registration and version metadata.
2. Input/output contract and approval state.

Boundary:
1. No training pipeline ownership.

### 1.6 inference_tasks / reassessment_jobs
Responsibilities:
1. Inference task creation and status transitions.
2. One task must produce one trace_id.
3. Reassessment jobs after new patient data.

Boundary:
1. Task orchestration status only.
2. No autonomous medical final decision.

### 1.7 feedback
Responsibilities:
1. Doctor accept/reject/edit feedback.
2. Push eligible items to governed continuous-learning pool.

Boundary:
1. No automatic online training trigger.
2. Record only auditable feedback and candidate state.

### 1.8 trace integration boundary
Responsibilities:
1. Keep trace_id references in core backend entities.
2. Provide minimal trace event adapter boundary.

Boundary:
1. Do not hardcode trace_events/evidence_chain detailed schema here.
2. Delegate detailed spec to provenance and quality-control thread.

### 1.9 agent orchestration adapter boundary
Responsibilities:
1. Standard adapter contract for LLM orchestration and model services.
2. Standardized IO including task_id, trace_id, context summary, and output refs.

Boundary:
1. No provider-specific lock-in in core backend module.
2. LLM cannot replace doctor judgement.

## 2. MVP Database Entities and Ownership

### 2.1 Backend-owned core entities (Stage 01 contract owner)
1. patients
2. cases
3. case_inputs or multimodal_assets
4. clinical_observations (or clinical_tables baseline)
5. lab_results
6. emr_documents
7. model_registry
8. model_versions
9. inference_tasks
10. recommendations
11. doctor_feedback
12. reassessment_jobs
13. dynamic_state_snapshots

Backend ownership means:
1. Define PK/FK, core status fields, and audit baseline fields.
2. Define CRUD/API contract and lifecycle ownership.

### 2.2 Entities delegated to provenance and quality-control thread
1. trace_events (event taxonomy and granularity).
2. evidence_chain (nodes/edges/confidence/conflict handling).
3. quality_reviews (audit closure and governance records).

Boundary rule:
1. Core backend tables must keep trace_id or trace_ref.
2. Detailed trace and evidence schema is defined in provenance thread.

## 3. Trace and Evidence Integration Boundary

### 3.1 Mandatory trace_id references in backend
Must carry trace_id in:
1. inference_tasks
2. recommendations
3. doctor_feedback
4. reassessment_jobs
5. missing-value consultation records

### 3.2 Delegated detailed design
1. trace_events and evidence_chain detailed schema is not frozen here.
2. Provenance thread owns taxonomy, graph schema, and QC scoring.
3. Backend adapter submits minimum fields: trace_id, event_type, event_time, source_ref.

### 3.3 recommendation to trace linkage
Recommended constraints:
1. recommendations.trace_id is required.
2. recommendations.inference_task_id is required (recommended strongly).
3. Support one-task multi-recommendation with revision/version field.

### 3.4 Missing-value consultation to trace linkage
Recommended record: case_missing_value_queries.
Key fields:
1. case_id
2. inference_task_id
3. trace_id
4. field_path
5. question_text
6. status (pending/answered/default_applied)
7. doctor_response
8. default_strategy_applied
9. default_reason

Rule:
1. Ask doctor first.
2. Apply default only after unanswered state.
3. Default action must be trace-auditable.

## 4. API Grouping and Path Naming Draft

Required groups:
1. /health
2. /api/v1/patients
3. /api/v1/cases
4. /api/v1/cases/{case_id}/inputs
5. /api/v1/cases/{case_id}/missing-values
6. /api/v1/cases/{case_id}/recommendations
7. /api/v1/reassessment-jobs
8. /api/v1/model-registry
9. /api/v1/feedback

Additional task-oriented endpoints (recommended):
1. POST /api/v1/cases/{case_id}/inference-tasks
2. GET /api/v1/inference-tasks/{task_id}
3. POST /api/v1/reassessment-jobs
4. GET /api/v1/reassessment-jobs/{job_id}

Naming rules:
1. Use plural resources.
2. Use case as aggregate root for case-owned subresources.
3. Use PATCH for status transitions.
4. Use async task endpoints for long-running inference.

## 5. Cross-Thread Interface Requirements

### 5.1 Requirements for provenance and quality-control thread
Need to define:
1. trace_events standard taxonomy and payload schema.
2. evidence_chain node/edge schema and confidence fields.
3. Trace query contract by trace_id.
4. Quality review closure fields and workflow.

### 5.2 Requirements for small-model and orchestration thread
Need to define:
1. Specialized model IO JSON schema.
2. Model version selection and fallback strategy.
3. Orchestration adapter request/response contract.
4. Error code, retry class, timeout behavior.

### 5.3 Requirements for frontend doctor workstation thread
Backend should expose:
1. Case workspace aggregate read API.
2. Missing-value consultation workflow endpoints.
3. Recommendation fields with trace_id and evidence refs.
4. Reassessment status tracking endpoints.

### 5.4 Requirements for deployment and MLOps thread
Backend should provide:
1. Backend Dockerfile.
2. .env.example for db/redis/minio/model-service/llm adapter.
3. Healthcheck split: liveness and readiness.
4. Startup, migration command, structured logging, trace_id propagation.

## 6. Explicitly Out of Scope for Stage 01

1. Full frontend implementation.
2. Model training.
3. Real diagnosis logic implementation.
4. LLM replacing doctor judgement.
5. Automatic online real-time training.

Additional note:
Large-scale Alembic migration rollout is deferred; only migration planning input is in scope.

## 7. Main-Controller Writeback Summary

1. Stage 01 backend output is now frozen at contract level: module boundaries, DB entities, trace boundary, and API naming.
2. Backend-owned MVP entities are defined; trace_events/evidence_chain detailed schema is delegated to provenance thread.
3. Missing-value workflow must be statused, doctor-first, and trace-bound.
4. recommendations must bind trace_id and preferably inference_task_id.
5. Stage 01 intentionally excludes full implementation and large migration execution.
