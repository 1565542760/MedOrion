# MedOrion Backend Stage 02 Schema/API Plan

Last updated: 2026-05-31 Asia/Shanghai
Owner thread: MedOrion backend API and database
Inputs merged:
1. docs/backend/BACKEND_STAGE_01_CONTRACT.md
2. docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md
3. docs/model_orchestration/MODEL_ORCHESTRATION_STAGE_01_CONTRACT.md
4. docs/architecture/SOURCE_OF_TRUTH.md

Scope of this stage:
1. Integrate contracts into one backend schema and API landing plan.
2. Freeze MVP-level table ownership and constraints.
3. Define migration order and index priorities.
4. Keep implementation minimal: no full business logic, no real diagnosis logic, no container startup.

## 1. Final MVP Table List and Ownership

### 1.1 Backend-owned tables
1. patients
2. cases
3. multimodal_assets (or case_inputs as alias layer)
4. clinical_observations
5. lab_results
6. emr_documents
7. inference_tasks
8. recommendations
9. doctor_feedback
10. reassessment_jobs
11. dynamic_state_snapshots
12. case_missing_value_queries

### 1.2 Traceability-owned tables
1. trace_events
2. evidence_nodes
3. evidence_edges
4. quality_reviews

### 1.3 Model/orchestration-related tables
1. model_registry
2. model_versions
3. (optional for phase 2b) model_invocations
4. (optional for phase 2b) llm_invocations

### 1.4 Build-now vs defer
Build in Stage 02 MVP migration set:
1. patients
2. cases
3. multimodal_assets
4. clinical_observations
5. lab_results
6. emr_documents
7. model_registry
8. model_versions
9. inference_tasks
10. recommendations
11. doctor_feedback
12. reassessment_jobs
13. dynamic_state_snapshots
14. case_missing_value_queries
15. trace_events
16. evidence_nodes
17. evidence_edges
18. quality_reviews

Defer to Stage 02b or Stage 03:
1. model_invocations (can start as JSON payload inside inference_tasks/recommendations if needed)
2. llm_invocations (if orchestrator is not launched yet)
3. heavy denormalized analytics tables or materialized views

## 2. Table Field Draft (MVP)

Conventions for all tables:
1. id: UUID primary key (or ULID by global decision later)
2. created_at: timestamptz not null default now()
3. updated_at: timestamptz not null default now()
4. optional deleted_at for soft delete (defer unless needed)

### 2.1 patients
1. id
2. external_patient_id varchar(128) unique nullable
3. patient_display_id varchar(128) nullable
4. sex varchar(32) nullable
5. birth_date date nullable
6. demographics_json jsonb not null default '{}'
7. consent_status patient_consent_status not null default 'unknown'
8. created_at
9. updated_at

### 2.2 cases
1. id
2. patient_id uuid not null fk -> patients.id
3. case_no varchar(128) unique nullable
4. disease_domain_code varchar(64) nullable
5. title varchar(256) nullable
6. status case_status not null default 'open'
7. chief_complaint text nullable
8. context_json jsonb not null default '{}'
9. opened_at timestamptz nullable
10. closed_at timestamptz nullable
11. created_at
12. updated_at

### 2.3 multimodal_assets (case_inputs)
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid nullable fk -> patients.id
4. modality_type modality_type not null
5. source_type varchar(64) nullable
6. bucket varchar(128) nullable
7. object_key varchar(512) nullable
8. checksum_sha256 varchar(128) nullable
9. content_type varchar(128) nullable
10. size_bytes bigint nullable
11. clinical_time timestamptz nullable
12. trace_ref varchar(96) nullable
13. quality_flags_json jsonb not null default '[]'
14. normalized_payload jsonb not null default '{}'
15. created_at
16. updated_at

### 2.4 clinical_observations
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid not null fk -> patients.id
4. observation_code varchar(128) not null
5. observation_name varchar(256) nullable
6. value_numeric double precision nullable
7. value_text text nullable
8. value_json jsonb nullable
9. unit varchar(64) nullable
10. observed_at timestamptz not null
11. source_asset_id uuid nullable fk -> multimodal_assets.id
12. source_type varchar(64) nullable
13. provenance_level varchar(32) nullable
14. created_at
15. updated_at

### 2.5 lab_results
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid not null fk -> patients.id
4. lab_panel_code varchar(128) nullable
5. test_code varchar(128) not null
6. test_name varchar(256) nullable
7. value_numeric double precision nullable
8. value_text text nullable
9. unit varchar(64) nullable
10. reference_range_json jsonb nullable
11. abnormal_flag varchar(32) nullable
12. sampled_at timestamptz nullable
13. reported_at timestamptz nullable
14. source_asset_id uuid nullable fk -> multimodal_assets.id
15. created_at
16. updated_at

### 2.6 emr_documents
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid not null fk -> patients.id
4. document_type varchar(64) not null
5. title varchar(256) nullable
6. language varchar(16) nullable
7. bucket varchar(128) nullable
8. object_key varchar(512) nullable
9. checksum_sha256 varchar(128) nullable
10. extracted_structured_json jsonb not null default '{}'
11. authored_at timestamptz nullable
12. created_at
13. updated_at

### 2.7 model_registry
1. id
2. model_name varchar(128) not null
3. disease_agent varchar(64) not null
4. task_type varchar(64) not null
5. modality_scope_json jsonb not null default '[]'
6. owner_team varchar(128) nullable
7. description text nullable
8. is_active boolean not null default true
9. created_at
10. updated_at

### 2.8 model_versions
1. id
2. model_id uuid not null fk -> model_registry.id
3. version_label varchar(128) not null
4. approval_state model_approval_state not null
5. contract_version varchar(64) not null
6. artifact_ref_json jsonb not null default '{}'
7. input_schema_json jsonb not null default '{}'
8. output_schema_json jsonb not null default '{}'
9. metrics_json jsonb not null default '{}'
10. runtime_constraints_json jsonb not null default '{}'
11. published_at timestamptz nullable
12. created_at
13. updated_at

### 2.9 inference_tasks
1. id
2. trace_id varchar(96) not null unique
3. case_id uuid not null fk -> cases.id
4. patient_id uuid nullable fk -> patients.id
5. disease_agent varchar(64) not null
6. task_type varchar(64) not null
7. status inference_task_status not null
8. requested_modalities_json jsonb not null default '[]'
9. model_version_policy_json jsonb not null default '{}'
10. input_refs_json jsonb not null default '[]'
11. missing_value_summary_json jsonb not null default '{}'
12. idempotency_key varchar(160) nullable
13. started_at timestamptz nullable
14. completed_at timestamptz nullable
15. error_code varchar(64) nullable
16. error_message text nullable
17. created_at
18. updated_at

### 2.10 recommendations
1. id
2. case_id uuid not null fk -> cases.id
3. inference_task_id uuid not null fk -> inference_tasks.id
4. trace_id varchar(96) not null
5. evidence_chain_id varchar(96) nullable
6. recommendation_version integer not null default 1
7. recommendation_type varchar(64) not null
8. status recommendation_status not null
9. candidate_label varchar(64) nullable
10. confidence_score double precision nullable
11. uncertainty_json jsonb not null default '{}'
12. limitations_json jsonb not null default '[]'
13. evidence_refs_json jsonb not null default '[]'
14. content_json jsonb not null default '{}'
15. created_by_type varchar(32) not null default 'system'
16. created_at
17. updated_at

### 2.11 doctor_feedback
1. id
2. case_id uuid not null fk -> cases.id
3. recommendation_id uuid nullable fk -> recommendations.id
4. inference_task_id uuid nullable fk -> inference_tasks.id
5. trace_id varchar(96) not null
6. doctor_id varchar(128) nullable
7. feedback_type feedback_type not null
8. decision varchar(64) nullable
9. rating smallint nullable
10. clinical_rationale text nullable
11. correction_payload_json jsonb not null default '{}'
12. learning_eligible boolean not null default true
13. created_at
14. updated_at

### 2.12 reassessment_jobs
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid not null fk -> patients.id
4. trace_id varchar(96) not null
5. previous_trace_id varchar(96) nullable
6. trigger_type reassessment_trigger_type not null
7. trigger_ref varchar(256) nullable
8. status reassessment_status not null
9. changed_input_refs_json jsonb not null default '[]'
10. comparison_summary_json jsonb not null default '{}'
11. started_at timestamptz nullable
12. completed_at timestamptz nullable
13. created_at
14. updated_at

### 2.13 dynamic_state_snapshots
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid not null fk -> patients.id
4. snapshot_time timestamptz not null
5. trace_id varchar(96) nullable
6. source_reassessment_job_id uuid nullable fk -> reassessment_jobs.id
7. state_summary_json jsonb not null default '{}'
8. modality_presence_json jsonb not null default '{}'
9. risk_summary_json jsonb not null default '{}'
10. uncertainty_summary_json jsonb not null default '{}'
11. created_at
12. updated_at

### 2.14 case_missing_value_queries
1. id
2. case_id uuid not null fk -> cases.id
3. patient_id uuid nullable fk -> patients.id
4. inference_task_id uuid nullable fk -> inference_tasks.id
5. trace_id varchar(96) not null
6. field_path varchar(256) not null
7. field_label varchar(256) nullable
8. clinical_importance clinical_importance not null
9. blocking_level blocking_level not null
10. question_text text not null
11. status missing_value_query_status not null
12. doctor_id varchar(128) nullable
13. doctor_response_json jsonb nullable
14. value_source value_source_type not null
15. default_strategy_code varchar(128) nullable
16. default_value_json jsonb nullable
17. default_reason text nullable
18. policy_version varchar(64) not null
19. expires_at timestamptz nullable
20. created_at
21. updated_at

### 2.15 trace_events (traceability-owned)
1. id
2. trace_id varchar(96) not null
3. case_id uuid not null
4. patient_id uuid nullable
5. event_type trace_event_type not null
6. actor_type trace_actor_type not null
7. actor_id varchar(128) nullable
8. source_module varchar(64) not null
9. event_time timestamptz not null
10. payload_json jsonb not null default '{}'
11. parent_event_id uuid nullable
12. severity trace_severity not null default 'info'
13. created_at

### 2.16 evidence_nodes (traceability-owned)
1. id
2. trace_id varchar(96) not null
3. case_id uuid not null
4. patient_id uuid nullable
5. evidence_chain_id varchar(96) not null
6. node_type evidence_node_type not null
7. source_module varchar(64) not null
8. source_record_type varchar(64) nullable
9. source_record_id varchar(128) nullable
10. label varchar(256) not null
11. summary text nullable
12. payload_json jsonb not null default '{}'
13. confidence double precision nullable
14. uncertainty_json jsonb nullable
15. status evidence_node_status not null
16. created_at

### 2.17 evidence_edges (traceability-owned)
1. id
2. trace_id varchar(96) not null
3. case_id uuid not null
4. evidence_chain_id varchar(96) not null
5. source_node_id uuid not null fk -> evidence_nodes.id
6. target_node_id uuid not null fk -> evidence_nodes.id
7. edge_type evidence_edge_type not null
8. weight double precision nullable
9. rationale text nullable
10. payload_json jsonb not null default '{}'
11. created_at

### 2.18 quality_reviews (traceability-owned)
1. id
2. trace_id varchar(96) not null
3. case_id uuid not null
4. patient_id uuid nullable
5. review_target_type quality_target_type not null
6. review_target_id varchar(128) not null
7. status quality_review_status not null
8. severity quality_severity not null
9. opened_by_type trace_actor_type not null
10. opened_by_id varchar(128) nullable
11. reason text not null
12. error_attribution quality_error_attribution nullable
13. attribution_confidence double precision nullable
14. findings_json jsonb not null default '{}'
15. related_refs_json jsonb not null default '{}'
16. resolution_summary text nullable
17. resolved_by_type trace_actor_type nullable
18. resolved_by_id varchar(128) nullable
19. resolved_at timestamptz nullable
20. created_at
21. updated_at

## 3. Key Constraints (MVP hard requirements)

1. inference_tasks.trace_id required and unique.
2. recommendations.trace_id required.
3. recommendations.inference_task_id required for MVP.
4. recommendations.evidence_chain_id recommended; in MVP it may equal trace_id.
5. case_missing_value_queries.trace_id required.
6. Downstream model-service must not generate replacement trace_id.
7. defaulted missing values must be distinguishable from doctor-provided values.

Implementation rules:
1. In case_missing_value_queries, use value_source enum: doctor_provided/default_applied/waived/unknown.
2. default_applied rows must include default_strategy_code and default_reason.
3. doctor_provided rows must include doctor_response_json and should not silently overwrite prior defaults.
4. retries of one inference attempt keep same trace_id and idempotency_key.

## 4. API Schema Draft

### 4.1 Pydantic naming convention
Request/response naming:
1. XxxCreateRequestV1
2. XxxUpdateRequestV1
3. XxxResponseV1
4. XxxListResponseV1
5. XxxFilterParamsV1

Core schemas:
1. PatientCreateRequestV1 / PatientResponseV1
2. CaseCreateRequestV1 / CaseResponseV1
3. CaseInputCreateRequestV1 / MultimodalAssetResponseV1
4. ClinicalObservationCreateRequestV1 / ClinicalObservationResponseV1
5. LabResultCreateRequestV1 / LabResultResponseV1
6. EmrDocumentCreateRequestV1 / EmrDocumentResponseV1
7. InferenceTaskCreateRequestV1 / InferenceTaskResponseV1
8. RecommendationCreateRequestV1 / RecommendationResponseV1
9. DoctorFeedbackCreateRequestV1 / DoctorFeedbackResponseV1
10. ReassessmentJobCreateRequestV1 / ReassessmentJobResponseV1
11. MissingValueQueryCreateRequestV1 / MissingValueQueryResponseV1
12. TraceSummaryResponseV1 / TraceEventsListResponseV1 / EvidenceChainResponseV1

### 4.2 ModelInferenceRequestV1 and ModelInferenceResponseV1 backend adapter
Inbound to adapter from backend service:
1. Build request from inference_tasks + case inputs + clinical/lab/emr refs.
2. Enforce required: trace_id, inference_task_id, case_id, disease_agent, requested_task, idempotency_key.
3. Include missing_value_context with statuses and query IDs.

Adapter response handling:
1. Validate response trace_id equals request trace_id.
2. Persist model outcome into recommendation draft payload fields.
3. Append required trace events: model_selected/model_invoked/model_result_received/orchestrator_decision.
4. Persist evidence node/edge proposals or references.

### 4.3 Trace query API in backend router
1. GET /api/v1/traces/{trace_id}
2. GET /api/v1/traces/{trace_id}/events
3. GET /api/v1/traces/{trace_id}/evidence-chain
4. GET /api/v1/cases/{case_id}/traces
5. POST /api/v1/quality-reviews

### 4.4 Recommendation API response minimum contract
RecommendationResponseV1 must include:
1. recommendation_id
2. case_id
3. inference_task_id
4. trace_id
5. evidence_chain_id
6. candidate_label
7. confidence (score and optional level)
8. uncertainty (structured)
9. limitations (list)
10. evidence_refs (node IDs, event IDs, asset refs)
11. status
12. created_at

## 5. Alembic Migration Plan (planning only)

No destructive migration execution in this stage.
No production data rewrite in this stage.

### 5.1 Migration sequence
1. 0001_base_entities: patients, cases
2. 0002_inputs_and_clinical: multimodal_assets, clinical_observations, lab_results, emr_documents
3. 0003_model_registry: model_registry, model_versions
4. 0004_inference_and_recommendation: inference_tasks, recommendations, case_missing_value_queries
5. 0005_feedback_and_reassessment: doctor_feedback, reassessment_jobs, dynamic_state_snapshots
6. 0006_traceability_core: trace_events, evidence_nodes, evidence_edges, quality_reviews
7. 0007_indexes_and_constraints: add advanced indexes/check constraints concurrently where needed

### 5.2 Enum definitions to prepare
1. patient_consent_status: unknown/granted/withdrawn
2. case_status: draft/open/in_review/closed/archived
3. modality_type: ct_image/mri_image/clinical_table/lab_result/emr_text/wearable/other
4. inference_task_status: pending/running/succeeded/failed/partial/cancelled
5. recommendation_status: draft/active/superseded/retracted
6. feedback_type: accept/reject/edit/comment/flag
7. reassessment_trigger_type: new_input/manual_request/scheduled/qc_request
8. reassessment_status: pending/running/completed/failed/cancelled
9. clinical_importance: required/recommended/optional
10. blocking_level: blocking/degrades_confidence/informational
11. missing_value_query_status: pending/answered/default_applied/waived_by_doctor/expired
12. value_source_type: doctor_provided/default_applied/waived/unknown
13. trace_event_type, trace_actor_type, trace_severity
14. evidence_node_type, evidence_node_status, evidence_edge_type
15. quality_target_type, quality_review_status, quality_severity, quality_error_attribution
16. model_approval_state: draft/approved/deprecated/revoked

### 5.3 Priority indexes
Priority A (must for MVP):
1. inference_tasks(trace_id) unique
2. recommendations(trace_id)
3. recommendations(inference_task_id)
4. case_missing_value_queries(trace_id)
5. case_missing_value_queries(case_id, status)
6. trace_events(trace_id, event_time)
7. evidence_nodes(trace_id, node_type)
8. evidence_edges(trace_id, source_node_id, target_node_id)
9. quality_reviews(trace_id, status)
10. dynamic_state_snapshots(case_id, snapshot_time)

Priority B (next wave):
1. multimodal_assets(case_id, modality_type)
2. clinical_observations(case_id, observation_code, observed_at)
3. lab_results(case_id, test_code, reported_at)
4. emr_documents(case_id, document_type, authored_at)
5. inference_tasks(case_id, status, created_at)

### 5.4 Safety rules
1. Do not drop columns/tables in Stage 02.
2. Do not rename critical columns without compatibility view/dual-write plan.
3. Add nullable first for uncertain fields, tighten later after validation.
4. For existing data migration, use backfill scripts after approval.

### 5.5 Current action in this stage
1. Generate migration plan only.
2. If main controller requests next, create minimal empty Alembic revision skeletons by sequence.

## 6. FastAPI Project Structure Suggestion

Suggested structure:
1. app/api/v1
2. app/modules/patients
3. app/modules/cases
4. app/modules/assets
5. app/modules/clinical
6. app/modules/model_registry
7. app/modules/inference
8. app/modules/recommendations
9. app/modules/feedback
10. app/modules/traces
11. app/modules/quality
12. app/core
13. app/db

Per module minimum files:
1. router.py
2. schemas.py
3. service.py
4. repository.py
5. models.py (or centralized model package with module mapping)

Shared layers:
1. app/core/config.py
2. app/core/errors.py
3. app/core/logging.py (trace_id propagation)
4. app/db/session.py
5. app/db/base.py
6. app/api/v1/router.py

## 7. Cross-Thread Integration Requirements

### 7.1 Requirements from small-model and orchestration thread
Must provide:
1. Stable ModelInferenceRequestV1 and ModelInferenceResponseV1 schema.
2. model_version_policy behavior and fallback flags.
3. error code taxonomy with retryable boolean.
4. required emitted events payload minimum.

### 7.2 Requirements from traceability and quality thread
Must validate:
1. event taxonomy compliance.
2. evidence node/edge type correctness.
3. no_silent_fallback observability.
4. missing-value default impact visibility.
5. quality review attribution closure fields.

### 7.3 APIs frontend can rely on
1. /api/v1/patients
2. /api/v1/cases
3. /api/v1/cases/{case_id}/inputs
4. /api/v1/cases/{case_id}/missing-values
5. /api/v1/cases/{case_id}/recommendations
6. /api/v1/reassessment-jobs
7. /api/v1/model-registry
8. /api/v1/feedback
9. /api/v1/traces/{trace_id}
10. /api/v1/traces/{trace_id}/events
11. /api/v1/traces/{trace_id}/evidence-chain

### 7.4 Requirements for deployment and MLOps
Need to provide in next implementation stage:
1. backend Dockerfile
2. .env.example with postgres/redis/minio/model-service keys
3. liveness/readiness healthcheck endpoints
4. structured logs with trace_id propagation
5. migration command and startup command contract

## 8. Explicit Stage-02 Do-Not-Do

1. Do not implement full business logic.
2. Do not train models.
3. Do not start backend container.
4. Do not start model-service container.
5. Do not expose Nginx 80/443.
6. Do not enable automatic real-time training.
7. Do not let model output replace doctor judgement.

## 9. Suggested Next Step

Recommendation: proceed to minimal backend skeleton implementation in the next stage.

Minimal means:
1. create app structure and routers with stub handlers
2. define SQLAlchemy models and enums from this document
3. create non-destructive initial Alembic skeleton by planned sequence
4. add health endpoint and config loading
5. no diagnosis logic and no container startup

## 10. Main-Controller Writeback Summary

1. Stage 02 merged backend, traceability, and model-orchestration contracts into one schema/API landing plan.
2. MVP ownership is now explicit across backend-owned, traceability-owned, and model-related tables.
3. Hard constraints for trace_id and missing-value distinguishability are frozen.
4. API schema naming and adapter integration path for ModelInferenceRequestV1/ResponseV1 are defined.
5. Alembic migration order, enums, and priority indexes are planned with non-destructive policy.
6. Next recommended action is minimal skeleton implementation only, pending controller approval.
