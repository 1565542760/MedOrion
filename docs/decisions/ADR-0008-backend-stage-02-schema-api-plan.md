# ADR-0008: Backend Stage 02 Schema/API Plan

Date: 2026-05-31
Status: Accepted
Source: Backend API and Database Stage 02 report

## Decision

The backend Stage 02 schema/API plan is accepted. It merges the backend, traceability, and model-orchestration contracts into one MVP table/API/Alembic landing plan.

Build-now MVP tables include patients, cases, multimodal_assets, clinical_observations, lab_results, emr_documents, model_registry, model_versions, inference_tasks, recommendations, doctor_feedback, reassessment_jobs, dynamic_state_snapshots, case_missing_value_queries, trace_events, evidence_nodes, evidence_edges, and quality_reviews.

model_invocations and llm_invocations are deferred unless needed earlier.

Hard constraints are accepted:

- inference_tasks.trace_id required and unique
- recommendations.trace_id required
- recommendations.inference_task_id required for MVP
- recommendations.evidence_chain_id recommended; MVP may use trace_id
- case_missing_value_queries.trace_id required
- model-service must not replace upstream trace_id
- defaulted missing values must be distinguishable from doctor-provided values

The next approved implementation is minimal backend skeleton only: app structure, router stubs, SQLAlchemy models/enums, initial non-destructive Alembic skeleton, /health, config loading, and trace_id-aware logging.

Full business logic, diagnosis logic, model training, service startup, Nginx exposure, and automatic real-time training remain out of scope.
