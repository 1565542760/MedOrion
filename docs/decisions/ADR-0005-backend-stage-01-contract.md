# ADR-0005: Backend Stage 01 Contract

Date: 2026-05-31
Status: Accepted
Source: Backend API and Database Stage 01 report

## Context

The backend thread produced /home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_01_CONTRACT.md. The document defines architecture and database contracts only. It intentionally avoids full business implementation and large Alembic rollout.

## Decision

The backend Stage 01 contract is accepted.

Accepted module boundaries:

- patients
- cases
- multimodal_assets
- clinical_tables, labs, and emr
- model_registry
- inference_tasks and reassessment_jobs
- feedback
- trace integration boundary
- agent orchestration adapter boundary

Backend-owned MVP entities:

- patients
- cases
- case_inputs or multimodal_assets
- clinical_observations or clinical_tables baseline
- lab_results
- emr_documents
- model_registry
- model_versions
- inference_tasks
- recommendations
- doctor_feedback
- reassessment_jobs
- dynamic_state_snapshots

Delegated to provenance and quality control:

- trace_events
- evidence_chain
- quality_reviews

## Trace Boundary

Core backend tables must retain trace_id or trace_ref where relevant. inference_tasks, recommendations, doctor_feedback, reassessment_jobs, and missing-value consultation records must carry trace_id.

recommendations.trace_id is required. recommendations.inference_task_id is strongly recommended and should be treated as required for MVP unless a later ADR changes it.

Missing-value handling must be doctor-first, statused, and trace-auditable. Default handling must record strategy and reason.

## Accepted API Groups

- /health
- /api/v1/patients
- /api/v1/cases
- /api/v1/cases/{case_id}/inputs
- /api/v1/cases/{case_id}/missing-values
- /api/v1/cases/{case_id}/recommendations
- /api/v1/cases/{case_id}/inference-tasks
- /api/v1/inference-tasks/{task_id}
- /api/v1/reassessment-jobs
- /api/v1/model-registry
- /api/v1/feedback

## Consequences

The traceability and quality-control thread is now unblocked and should define trace_events, evidence_chain, quality_reviews, and trace query contracts.

Backend implementation, schema migration, model-service schemas, and frontend UI should wait until the trace contract is accepted.
