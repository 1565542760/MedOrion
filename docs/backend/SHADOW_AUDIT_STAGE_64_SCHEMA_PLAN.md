# MedOrion Stage 64: Shadow Audit Schema / Storage Plan

Last updated: 2026-06-04

## 1. Purpose
Stage 64 defines how CAP/COP clinical MLP shadow outputs should be audited and stored in a shadow-specific data path. This stage is a storage design artifact only. It does not create tables, does not change application behavior, and does not affect the doctor-facing recommendation path.

The design goal is to make shadow results observable, replayable, and comparable without allowing them to become the formal diagnostic output.

## 2. Scope and Non-Goals
This plan:
- defines a shadow audit schema draft
- defines storage semantics for shadow inference runs and outputs
- defines query surfaces for later implementation
- defines the boundary between shadow audit and case trace/evidence

This plan does not:
- create database tables
- execute Alembic
- load a model
- train a model
- run real shadow inference
- change frontend behavior
- enable Nginx
- promote any shadow candidate to default or canary
- write to case trace/evidence

## 3. Shadow Audit Data Model Draft

### 3.1 shadow_inference_runs
This table represents one shadow execution attempt for a case/model pair.

Recommended fields:
- shadow_run_id
- trace_id
- case_id
- patient_id
- model_version_id
- artifact_hash
- adapter_code
- model_input_schema_id
- input_snapshot_id
- status
- runtime_env
- runtime_stub
- not_for_diagnosis
- started_at
- completed_at
- duration_ms
- error_code
- error_detail_json

### 3.2 shadow_inference_outputs
This table stores the shadow run outputs and comparison-ready result payloads.

Recommended fields:
- output_id
- shadow_run_id
- trace_id
- case_id
- model_version_id
- prediction_raw_json
- prediction_probability_json
- candidate_label
- confidence_json
- uncertainty_json
- limitations_json
- input_quality_flags_json
- created_at

### 3.3 Optional shadow_inference_errors
Recommended only if the project later wants error rows separated from run rows.

Potential fields:
- shadow_error_id
- shadow_run_id
- trace_id
- case_id
- model_version_id
- error_code
- error_detail_json
- created_at

### 3.4 Optional shadow_model_comparisons
Recommended only if the project later needs side-by-side comparisons between shadow outputs and formal recommendations or other candidate models.

Potential fields:
- comparison_id
- shadow_run_id
- trace_id
- case_id
- baseline_model_version_id
- compare_model_version_id
- comparison_status
- comparison_summary_json
- created_at

## 4. Storage Semantics
Shadow audit storage is explicitly separate from the formal case recommendation path.

### 4.1 What shadow audit records
Shadow audit should record:
- success and failure outcomes
- adapter and runtime timing
- input snapshot linkage
- model version linkage
- confidence, uncertainty, and limitation summaries
- execution environment details
- timeout, disabled, insufficient-input, and model-not-enabled conditions

### 4.2 What shadow audit does not record into the formal case chain by default
Shadow results must not, by default:
- create doctor-facing recommendations
- enter the official case evidence chain
- override the stub path
- change the formal assessment result
- appear as a diagnostic claim

### 4.3 When case trace/evidence may reference shadow results
Only an explicitly approved, clinically meaningful summary may later be surfaced into the case trace/evidence path. Even then, only the summary or clinical implication should be referenced, not the full shadow execution detail.

Normal shadow calls, failures, timing, adapter details, and operational information should remain in shadow audit storage.

## 5. Query API Draft
The following API surfaces are recommended for later implementation:

- GET /api/v1/shadow-inference-runs/{shadow_run_id}
- GET /api/v1/cases/{case_id}/shadow-inference-runs
- GET /api/v1/traces/{trace_id}/shadow-inference-runs
- GET /api/v1/shadow-inference-runs/{shadow_run_id}/outputs

These routes are intended for audit review only. They are not intended to produce or publish formal diagnosis output.

## 6. Indexing Recommendations
Recommended indexes and access paths:
- trace_id
- case_id
- patient_id
- model_version_id
- status
- started_at
- (case_id, started_at)
- (trace_id, model_version_id)

Rationale:
- trace_id is needed for audit correlation.
- case_id and patient_id are needed for case-level review.
- model_version_id is needed to compare shadow candidate behavior across versions.
- status and started_at support operational auditing and timeline review.
- composite indexes support common audit filtering and chronological retrieval.

## 7. Lifecycle States
A shadow run should support the following lifecycle states or equivalent audit outcomes:
- shadow_success
- shadow_failed
- shadow_disabled
- shadow_timeout
- shadow_insufficient_input
- shadow_model_not_enabled

These values are auditing outcomes, not medical outcomes.

## 8. Trace / Evidence Boundary
This stage must keep the case trace/evidence boundary explicit:

### 8.1 Default rule
Shadow results are not entered into the doctor-facing recommendation chain.
Shadow results are not entered into the case evidence chain.

### 8.2 Allowed later use
Only after separate approval may a clinically meaningful shadow summary be referenced in case trace/evidence. If that happens, the reference should be a summary or note, not the full shadow execution payload.

### 8.3 What remains in shadow audit storage
- normal shadow calls
- failed shadow calls
- adapter timing
- runtime details
- retries
- comparisons
- operational metadata
- insufficient input outcomes

## 9. Relationship to Existing Objects
This schema is intended to coexist with the existing MedOrion objects:
- model_versions
- model_input_schemas
- clinical_feature_mappings
- case_model_input_snapshots
- trace_events
- evidence_nodes
- evidence_edges
- recommendations

However, Stage 64 deliberately keeps shadow audit separate from case trace/evidence by default.

## 10. Migration Risk and Downgrade Notes
This is a planning-only stage.

If the project later moves to implementation, risk areas will include:
- deciding whether shadow audit tables should live in the same schema namespace as the rest of the backend audit tables
- deciding whether output rows should be append-only
- deciding whether comparisons need a separate table or a JSON payload column
- deciding how to handle backfill if shadow is enabled before audit storage exists

No migration is created in Stage 64, so there is no apply or downgrade risk yet.

## 11. Stage 65 Recommendation
Stage 65 should produce an Alembic migration review draft only after the shadow storage contract is approved.

Stage 65 should not be used to enable live shadow inference or to change the formal recommendation path.

## 12. Main-Controller Writeback Summary
- Stage 64 defines a shadow audit storage plan only.
- Shadow audit is intentionally separate from the case evidence chain by default.
- The proposed storage shape includes runs, outputs, and optional error and comparison tables.
- The query API draft is audit-first and not diagnostic.
- The next step should be a migration review draft, not a live apply.
