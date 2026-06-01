# MedOrion Architecture Source of Truth

Last updated: 2026-05-31 Asia/Shanghai
Owner thread: MedOrion general architecture collaboration Codex
Remote workspace: /home/sygxdg/MedOrion

## 1. Project Positioning

MedOrion is a multimodal medical intelligent-agent assisted diagnosis platform for doctors. It supports clinical decision support, explanation, evidence aggregation, and follow-up reassessment. It does not replace doctors' diagnosis.

CAP/COP is the first-stage demonstration disease task only. It must not constrain MedOrion into a single-disease system.

## 2. Non-Negotiable Principles

1. Multi-disease extensibility is a first-class architectural requirement.
2. Multimodal input must be supported: CT, MRI, clinical tables, electronic medical records, laboratory indicators, and future dynamic wearable-device data.
3. The system uses disease-specific agents on top of a shared general capability foundation.
4. Small/specialized models handle disease-specific prediction and judgement; large models handle orchestration, explanation, doctor-facing Q&A, and recommendation generation.
5. Every generated suggestion must carry a trace_id and evidence chain.
6. Missing table values must first trigger an active question to the doctor. If the doctor does not resolve them, the system applies a configured default strategy and records that decision in the trace.
7. Continuous learning must not mean automatic real-time training.
8. Dynamic disease feedback means newly added patient data can trigger state reassessment; it does not mean real-time model training.

## 3. Target Architecture Layers

### 3.1 Interaction Layer

Doctor-facing interfaces, patient case workspace, upload/review flows, evidence visualization, Q&A, and recommendation review. Frontend implementation details belong to frontend-specific threads.

### 3.2 Orchestration Layer

The large-model agent layer is responsible for:

- routing tasks to disease agents and shared services;
- deciding which modalities are required or missing;
- asking doctors for missing critical information;
- generating explanations, summaries, Q&A answers, and recommendations;
- enforcing trace_id creation and evidence-chain completeness.

### 3.3 Disease-Agent Layer

Each disease agent owns disease-specific workflow logic, required inputs, specialized models, rules, thresholds, evaluation metrics, and explanation templates.

Initial agent: CAP/COP demonstration agent.

Future agents must follow the same contract rather than forking the platform architecture.

### 3.4 Shared Capability Foundation

Shared services include:

- multimodal data ingestion;
- data normalization and validation;
- image preprocessing adapters;
- clinical table schema management;
- EMR/lab text parsing and retrieval;
- evidence-chain and trace registry;
- model registry and model versioning;
- prompt/template registry;
- audit logging;
- evaluation and feedback datasets;
- doctor feedback collection;
- controlled retraining workflow.

### 3.5 Model Layer

Small/specialized models provide disease-specific outputs, such as classification, risk score, segmentation, abnormality detection, or calibrated probability.

Large models do not silently override specialized model results. They may explain, reconcile, ask for more data, and present uncertainty.

## 4. Core Data Flow

1. Case is created or updated.
2. Inputs are ingested by modality adapters.
3. Validation checks required fields, modality completeness, and quality issues.
4. Missing table values trigger doctor-facing questions.
5. If unresolved, default missing-value strategy is applied and recorded.
6. Orchestrator selects relevant disease agent(s).
7. Disease agent calls specialized model(s) and disease rules.
8. Evidence chain is assembled under a trace_id.
9. Large model generates explanation and recommendation using evidence-bound context.
10. Doctor reviews, accepts, rejects, edits, or requests clarification.
11. Feedback is stored for later evaluation and controlled learning, not automatic real-time training.

## 5. Trace and Evidence Requirements

Every recommendation must include:

- trace_id;
- patient/case identifier reference;
- timestamp;
- data modality references used;
- model names and versions;
- prompt/template version where applicable;
- missing-value handling record;
- intermediate disease-agent outputs;
- generated recommendation;
- uncertainty and caveats;
- doctor feedback status.

## 6. Missing-Value Policy

Default order:

1. identify missing or invalid fields;
2. classify clinical importance;
3. ask the doctor to provide or confirm values;
4. wait according to product workflow policy;
5. if unresolved, apply disease-agent-specific default strategy;
6. record strategy, affected fields, and impact in the trace.

No silent imputation is allowed for doctor-facing recommendations.

## 7. Continuous Learning Policy

Allowed:

- collect doctor feedback;
- collect later outcome labels;
- build versioned evaluation datasets;
- schedule offline retraining or fine-tuning;
- run validation and approval before deployment;
- release new model versions through a registry.

Not allowed:

- automatic real-time training from live doctor edits;
- unversioned model replacement;
- changing recommendation behavior without traceable version records.

## 8. Dynamic Condition Feedback

When new CT/MRI, labs, EMR notes, vitals, wearable data, or doctor observations are added, MedOrion may rerun validation, orchestration, disease-agent judgement, and recommendation generation.

This is patient-state reassessment. It is not model training.

## 9. MVP Scope

MVP should prove the platform pattern with CAP/COP while preserving multi-disease extensibility.

Recommended MVP boundaries:

- one CAP/COP disease agent;
- multimodal case container;
- CT/image input adapter placeholder or initial pipeline;
- clinical table/lab input schema with missing-value workflow;
- EMR text ingestion placeholder or lightweight parsing;
- trace_id evidence chain for every recommendation;
- large-model orchestration and explanation interface contract;
- doctor feedback capture;
- model registry metadata, even if the first model is simple or mocked.

Out of MVP:

- real-time wearable ingestion at production scale;
- automatic online learning;
- full hospital information-system integration;
- broad disease library;
- regulatory-grade clinical deployment claims.

## 10. Naming Conventions

Project name: MedOrion

Recommended module vocabulary:

- disease_agent: disease-specific agent implementation;
- orchestrator: large-model routing and reasoning coordinator;
- modality_adapter: CT, MRI, table, EMR, lab, wearable ingestion adapters;
- evidence_chain: traceable evidence package;
- trace_id: unique recommendation trace identifier;
- model_registry: versioned model metadata;
- feedback_store: doctor and outcome feedback records;
- reassessment: rerun after new patient data;
- continuous_learning: offline, governed learning workflow only.

Avoid naming that implies replacement of doctors, automatic diagnosis authority, or real-time self-training.

## 11. Current Remote Environment Snapshot

Checked on 2026-05-31:

- OS: Ubuntu 24.04.4 LTS
- Kernel: 6.17.0-20-generic
- CPU: AMD Ryzen 7 5800H, 16 logical CPUs
- Memory: 15 GiB RAM, 4 GiB swap
- Root disk: 457 GiB total, 397 GiB available
- Home disk: 469 GiB total, 79 GiB available
- Python: /usr/bin/python3, Python 3.12.3
- pip: 24.0
- python3-venv: available
- Conda: /home/sygxdg/miniconda3, conda 26.1.1
- Existing conda envs: base, DL, MRI3D, hert, intelipress
- Git: 2.43.0
- Docker: 29.1.3, service active and enabled
- Docker Compose: 2.40.3
- Nginx: 1.24.0, installed but inactive and disabled
- Node.js: v22.22.2
- npm: 10.9.7
- ripgrep: 14.1.0
- GPU: NVIDIA GeForce RTX 3050 Laptop GPU, 4 GiB VRAM
- NVIDIA driver: 535.309.01
- CUDA runtime shown by nvidia-smi: 12.2
- Still not installed or not found in PATH: pnpm, uv, nvcc
- Nginx is intentionally stopped; ports 80 and 443 are not listening after foundation install.
- Infra services are running healthy: PostgreSQL on 127.0.0.1:5432, Redis on 127.0.0.1:6379, MinIO API on 127.0.0.1:9000, and MinIO Console on 127.0.0.1:9001.
- sudo channel was resolved for the foundation install. The password was not written to project files or reports.
- /srv/medorion directory structure exists and deployment drafts were copied to /srv/medorion/deploy.


Global model artifact handling constraint:

- If any later task needs a deep-learning .pth model file, no thread may scan, copy, move, or infer paths from other project folders.
- The thread must report the need to the main-controller conversation, and the main controller will ask the user for the exact file location.

## 12. MVP Deployment Direction

Deployment-specific implementation belongs to the deployment thread, but the following architecture constraints are accepted globally:

- Use Docker Compose as the MVP deployment foundation.
- Prefer /srv/medorion as the deployment application root because the root partition has substantially more available space than /home.
- Keep code, persistent data, model artifacts, object storage, logs, and backups in separate directory layers.
- Backend should run as a containerized FastAPI service.
- Backend should connect through Compose-managed PostgreSQL, Redis, and MinIO services.
- Model inference services should be separate containers rather than embedded directly in the FastAPI backend.
- Reserve /models-style mounted storage with explicit model version directories.
- Frontend production assets may be served by an Nginx container or host Nginx, behind an HTTPS reverse proxy.
- Keep a development Compose profile separate from production behavior.
- Reserve MLflow or an equivalent model/experiment tracking service, but do not make it a blocker for the earliest vertical MVP.
- GPU serving requires a later NVIDIA Container Toolkit setup.
- Because the RTX 3050 Laptop GPU has only 4 GiB VRAM, model-serving plans must prefer lightweight models, quantization, batching discipline, and CPU fallback.
- Until sudo access is available, deployment drafts may live under /home/sygxdg/MedOrion/deploy and later be migrated to /srv/medorion/deploy.
- Compose service ports should bind to 127.0.0.1 by default; public exposure should go through Nginx on 80/443.
- MinIO API and console should remain local-only unless a later security review approves exposure.
- Backend-to-model-service communication may start with HTTP at model-service:8100 for MVP; gRPC or queue-based inference remains an open architecture option.


## 13. Backend MVP Contract

The backend Stage 01 contract is documented at /home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_01_CONTRACT.md.

Accepted backend module boundaries:

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

Delegated to the provenance and quality-control thread:

- trace_events taxonomy and payload schema
- evidence_chain graph structure
- quality_reviews and audit closure workflow

Backend trace integration rules:

- inference_tasks, recommendations, doctor_feedback, reassessment_jobs, and missing-value consultation records must carry trace_id.
- recommendations.trace_id is required.
- recommendations.inference_task_id is strongly recommended and should be treated as required unless a later ADR says otherwise.
- Missing-value consultation must be doctor-first, statused, and trace-auditable; default handling must record strategy and reason.

Accepted MVP API path groups:

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


## 14. Traceability and Quality-Control Contract

The traceability Stage 01 contract is documented at /home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md.

Accepted trace_id lifecycle:

- The backend inference-task service is the canonical trace_id generator.
- One inference_task has exactly one required trace_id.
- One trace_id belongs to exactly one canonical inference_task.
- MVP reassessment inference runs create a new trace_id; reassessment_jobs.trace_id and inference_tasks.trace_id should be the same for MVP when a reassessment creates an inference task.
- trace_id must bind to case_id; patient_id may be nullable for de-identified or pre-patient workflows.
- Downstream model, agent, orchestration, feedback, and quality services must reject trace-bound requests that omit trace_id rather than silently creating one.

Accepted trace_events taxonomy for Stage 01:

- case_created
- input_uploaded
- input_validated
- missing_value_detected
- doctor_question_asked
- doctor_answer_received
- default_strategy_applied
- inference_task_created
- model_selected
- model_invoked
- model_result_received
- orchestrator_decision
- recommendation_generated
- recommendation_viewed
- doctor_feedback_recorded
- reassessment_requested
- reassessment_completed
- quality_review_created
- quality_issue_detected

Accepted trace_events required baseline fields:

- id
- trace_id
- case_id
- patient_id nullable
- event_type
- actor_type
- actor_id nullable
- source_module
- event_time
- payload_json
- parent_event_id nullable
- severity
- created_at

Accepted evidence_chain structure:

- Evidence graph is represented by evidence_nodes and evidence_edges.
- MVP may use trace_id as evidence_chain_id unless a later implementation ADR introduces a separate chain identifier.
- Node types include input, clinical_feature, lab_result, image_finding, model_output, rule_result, llm_reasoning_step, recommendation, and doctor_feedback.
- Edge types include supports, contradicts, derived_from, references, overrides, and missing_value_defaulted.
- Evidence nodes and edges must support confidence, uncertainty, conflict handling, source references, model version references, prompt/template version references, MinIO object references where appropriate, and knowledge references.

Accepted missing-value audit states:

- pending
- answered
- default_applied
- waived_by_doctor
- expired

Missing-value handling must emit trace events for detection, doctor question, doctor answer or waiver, expiration/default, and evidence links for defaulted values. Defaulted values must not be confused with doctor-provided values.

Accepted quality review contract:

- quality review targets: recommendation, trace, model_output, missing_value_decision, reassessment.
- quality review statuses: open, investigating, resolved, dismissed.
- error attribution categories: data_quality, model_error, orchestration_error, missing_value_policy, human_feedback, system_error.
- doctor feedback may trigger a quality review, but must not overwrite the original feedback record.

Accepted trace query API drafts:

- GET /api/v1/traces/{trace_id}
- GET /api/v1/traces/{trace_id}/events
- GET /api/v1/traces/{trace_id}/evidence-chain
- GET /api/v1/cases/{case_id}/traces
- POST /api/v1/quality-reviews

Traceability-owned tables:

- trace_events
- evidence_nodes
- evidence_edges
- quality_reviews

Backend core tables must retain trace references including inference_tasks.trace_id, recommendations.trace_id, recommendations.inference_task_id, recommendations.evidence_chain_id, doctor_feedback.trace_id, reassessment_jobs.trace_id, dynamic_state_snapshots.trace_ref or trace_id, and case_missing_value_queries.trace_id.


## 15. Model Orchestration Contract

The model orchestration Stage 01 contract is documented at /home/sygxdg/MedOrion/docs/model_orchestration/MODEL_ORCHESTRATION_STAGE_01_CONTRACT.md.

Accepted disease_agent interface:

- CAP/COP is the first demonstration disease_agent, not an architectural special case.
- disease_agent implementations expose disease_agent_code, agent_contract_version, supported_tasks, and supported_modalities.
- Standard operation chain: validate_case_inputs, build_model_invocation_plan, execute_model_invocations, merge_model_and_rule_outputs, emit_trace_and_evidence, and return_structured_agent_result.
- Disease agents provide disease-specific judgement, while the orchestrator handles routing, reconciliation, explanation, Q&A, and doctor-facing recommendation generation.

Accepted model-service API draft:

- GET /health
- GET /models
- GET /models/{model_version_id}
- POST /validate-input
- POST /infer
- optional POST /warmup

Accepted schemas:

- ModelInferenceRequestV1 includes trace_id, inference_task_id, case_id, patient_id nullable, disease_agent, requested_task, model_version_policy, inputs, clinical_context_refs, modality_refs, missing_value_context, runtime_options, and idempotency_key.
- ModelInferenceResponseV1 includes trace_id, inference_task_id, model_invocation_id, model_id, model_version_id, disease_agent, task_type, status, outputs, confidence, uncertainty, limitations, evidence_nodes_to_create, evidence_edges_to_create, trace_events_to_emit, and nullable error.

Accepted CAP/COP output contract:

- classification or risk_score or probability
- candidate_label
- confidence
- uncertainty
- input_quality_flags
- missing_value_impact
- model_limitations
- recommended_next_actions_for_doctor_review

Accepted model policy:

- supported version policies: approved_only, latest_approved, pinned_version.
- supported fallbacks: fallback_to_cpu and fallback_to_rule_baseline.
- no_silent_fallback is mandatory; any fallback must emit trace_event and evidence.
- trace-bound model-service and disease-agent requests must carry upstream trace_id and must not generate replacement trace IDs.

Accepted error taxonomy:

- invalid_input
- missing_required_input
- unsupported_modality
- model_not_found
- model_version_not_approved
- inference_timeout
- resource_exhausted
- dependency_unavailable
- internal_error
- trace_id_missing

Accepted serving assumption:

- Stage 01 is CPU-first with batch size 1 and concurrency 1.
- GPU serving and NVIDIA Container Toolkit are deferred.
- Lightweight or quantized models are preferred because the available RTX 3050 Laptop GPU has 4 GiB VRAM.


## 16. Backend Stage 02 Schema/API Plan

The backend Stage 02 schema/API plan is documented at /home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_02_SCHEMA_API_PLAN.md.

Accepted MVP table ownership:

- backend-owned: patients, cases, multimodal_assets, clinical_observations, lab_results, emr_documents, inference_tasks, recommendations, doctor_feedback, reassessment_jobs, dynamic_state_snapshots, case_missing_value_queries.
- traceability-owned: trace_events, evidence_nodes, evidence_edges, quality_reviews.
- model/orchestration-related: model_registry, model_versions. model_invocations and llm_invocations are deferred to a later phase unless needed earlier.

Accepted hard constraints:

- inference_tasks.trace_id is required and unique.
- recommendations.trace_id is required.
- recommendations.inference_task_id is required for MVP.
- recommendations.evidence_chain_id is recommended; MVP may use trace_id as evidence_chain_id.
- case_missing_value_queries.trace_id is required.
- model-service must not replace upstream trace_id.
- defaulted missing values must be distinguishable from doctor-provided values, including through value_source_type or equivalent fields.

Accepted implementation plan:

- Alembic migration order is planned as non-destructive 0001 through 0007.
- Enums and A-priority indexes should be defined before feature implementation.
- Next backend action may be minimal skeleton implementation only: app structure, router stubs, SQLAlchemy models/enums, initial Alembic skeleton, /health, config loading, and structured trace_id-aware logging.
- Full business logic, real diagnosis logic, model training, backend/model-service container startup, Nginx exposure, and automatic real-time training remain out of scope for the next backend skeleton stage.

Accepted FastAPI structure:

- app/api/v1
- app/modules/patients
- app/modules/cases
- app/modules/assets
- app/modules/clinical
- app/modules/model_registry
- app/modules/inference
- app/modules/recommendations
- app/modules/feedback
- app/modules/traces
- app/modules/quality
- app/core
- app/db


## 17. Backend Stage 03 Minimal Skeleton

The backend Stage 03 minimal skeleton is implemented under /srv/medorion/app/backend.

Accepted implementation status:

- Dependency approach: Python venv plus requirements.txt.
- Local FastAPI health check is verified: GET http://127.0.0.1:8000/health returns status ok, service backend, env development.
- Backend Docker container has not been started.
- Nginx remains disabled.
- No diagnosis logic, model training, model-service startup, or automatic real-time training was introduced.

Created backend structure:

- app/api/v1
- app/core
- app/db
- app/modules/patients
- app/modules/cases
- app/modules/assets
- app/modules/clinical
- app/modules/model_registry
- app/modules/inference
- app/modules/recommendations
- app/modules/feedback
- app/modules/traces
- app/modules/quality
- alembic/versions

Accepted Stage 03 model coverage:

- Implemented core skeleton models: Patient, Case, MultimodalAsset, InferenceTask, Recommendation, CaseMissingValueQuery, DoctorFeedback.
- Deferred field refinement while preserving ID-level skeletons: ClinicalObservation, LabResult, EmrDocument, ModelRegistry, ModelVersion, ReassessmentJob, DynamicStateSnapshot, TraceEvent, EvidenceNode, EvidenceEdge, QualityReview.
- Implemented key enums: ValueSourceType, InferenceTaskStatus, RecommendationStatus, MissingValueQueryStatus.

Accepted Stage 03 trace constraints:

- inference_tasks.trace_id is required and unique.
- recommendations.trace_id is required.
- recommendations.inference_task_id is required.
- case_missing_value_queries.trace_id is required.
- case_missing_value_queries.value_source distinguishes doctor_provided, default_applied, and related value origins.

Alembic status:

- Alembic skeleton exists under /srv/medorion/app/backend/alembic.
- Initial revision exists: 0e36c2285187_stage03_initial_skeleton.py.
- The revision has not been applied to PostgreSQL.
- No destructive migration has been performed.

Next backend implementation scope:

- Fill deferred model fields and enums according to BACKEND_STAGE_02_SCHEMA_API_PLAN.md.
- Regenerate or refine non-destructive migration for review.
- Add trace_id middleware and structured request logging.
- Add readiness and liveness split.
- Draft backend Dockerfile and Compose profile only after model/migration review.


## 18. Backend Stage 04 Skeleton Refinement Status

Backend Stage 04 is mostly implemented under /srv/medorion/app/backend, but migration refinement is blocked by database credential mismatch.

Accepted completed items:

- app/db/enums.py now includes expanded enums for case status, modality, inference status, feedback, reassessment, missing value, trace/evidence, and quality review.
- app/db/models.py now includes deferred model field skeletons for ClinicalObservation, LabResult, EmrDocument, ModelRegistry, ModelVersion, ReassessmentJob, DynamicStateSnapshot, TraceEvent, EvidenceNode, EvidenceEdge, and QualityReview.
- app/core/trace.py provides request/trace context.
- app/core/middleware.py provides request_id and trace_id middleware.
- app/core/logging.py injects request_id and trace_id into logs.
- app/db/session.py includes readiness database check support.
- app/main.py exposes /health/live, /health/ready, and compatibility /health.

Accepted Stage 04 behavior:

- x-request-id is read from headers or generated with req_*.
- x-trace-id is read from headers when present, otherwise represented as '-'.
- Response headers include x-request-id and include x-trace-id only when a trace was supplied.
- Logging includes request_id and trace_id fields.
- Middleware does not replace canonical business trace_id generation; canonical trace_id generation remains owned by inference_task service.

Health check status:

- /health/live verified locally through venv + uvicorn and returns 200 alive.
- /health verified locally and returns 200 compatibility status.
- /health/ready now returns 200 ready after backend local .env was aligned with the running PostgreSQL credentials.

Alembic status:

- Revision exists: a9d28e4978dd_stage04_schema_baseline_non_destructive.py.
- The revision remains skeleton-style and has not been applied.
- Alembic can connect to PostgreSQL.
- alembic check reports that the target database is not up to date, which is expected because migrations have not been applied.
- No destructive migration has been performed.

Current blocker:

- Alembic migration DDL needs to be generated/refined and reviewed.
- Do not apply Alembic migrations until the generated DDL is reviewed and approved by the main controller.


## 19. Backend Stage 04 Migration Review Draft

Backend produced a non-applied Alembic DDL review draft at /srv/medorion/app/backend/alembic/versions/a9d28e4978dd_stage04_schema_baseline_non_destructive.py.

Accepted status:

- The migration draft covers 18 MVP tables, enums, foreign keys, indexes, and key trace constraints.
- alembic upgrade was not executed.
- The database remains intentionally not up to date.
- This migration is a review draft only, not an approved database state.

Key trace constraints present in the draft:

- inference_tasks.trace_id is required and unique.
- recommendations.trace_id is required.
- recommendations.inference_task_id is required.
- case_missing_value_queries.trace_id is required.
- value_source distinguishes doctor_provided and default_applied values.

Known review notes:

- Enum type names use compact names such as valuesourcetype rather than the snake_case style used in planning docs. Semantics appear aligned, but naming should be reviewed before apply.
- The current versions directory reportedly has a single effective baseline revision; since no migration has been applied yet, this may be acceptable, but revision lineage should be confirmed before apply.

Current gate:

- Do not apply this migration until traceability/quality-control reviews trace_events, evidence_nodes, evidence_edges, quality_reviews, missing-value audit fields, and dynamic snapshot trace links.
- After traceability review, the backend thread may make corrections and then request main-controller approval to apply.


## 20. Frontend Workbench Proposal Status

A frontend-specialized thread proposed the doctor workbench stack and page map, but frontend implementation remains on hold until schema/API review stabilizes.

Corrected environment facts:

- Node.js v22.22.2 and npm 10.9.7 are installed on the remote server.
- corepack is available.
- pnpm is not currently installed or enabled.
- /home/sygxdg/MedOrion is not empty; it contains docs and deployment drafts.
- /srv/medorion/app/frontend does not yet exist.

Accepted as proposal, not implementation approval:

- Next.js plus TypeScript for the frontend application.
- Ant Design / ProComponents for dense clinical-workbench UI.
- React Flow for trace/evidence lineage and error provenance graphs.
- ECharts for trends, risk curves, and model-output visualization.
- Cornerstone.js / Cornerstone3D reserved for medical image viewing.
- First frontend stage may use mock data and an API adapter layer, but should not start until backend API and trace query contracts are stable enough for UI scaffolding.

Proposed page map:

- /dashboard
- /cases
- /cases/[caseId]/multimodal
- /cases/[caseId]/missing-consultation
- /cases/[caseId]/small-models
- /cases/[caseId]/llm-explanation
- /cases/[caseId]/lineage
- /cases/[caseId]/feedback
- /models
- /learning-library
- /cases/[caseId]/dynamic-monitoring


## 21. Backend Stage 04 Revised Migration Candidate

Backend revised the Stage 04 migration candidate after traceability review. The candidate is still not applied.

Modified files:

- /srv/medorion/app/backend/app/db/models.py
- /srv/medorion/app/backend/alembic/versions/a9d28e4978dd_stage04_schema_baseline_non_destructive.py

Accepted revisions in the candidate:

- reassessment_jobs now includes previous_snapshot_id and current_snapshot_id.
- previous_snapshot_id and current_snapshot_id reference dynamic_state_snapshots.id.
- ORM and migration Priority A compound indexes are aligned for trace_events, evidence_nodes, evidence_edges, quality_reviews, dynamic_state_snapshots, case_missing_value_queries, and recommendations.
- trace_events.parent_event_id now has a self-reference to trace_events.id.
- trace_events includes source_record_type and source_record_id.

Preserved key constraints:

- inference_tasks.trace_id is required and unique.
- recommendations.trace_id is required.
- recommendations.inference_task_id is required.
- case_missing_value_queries.trace_id is required.
- value_source distinguishes doctor_provided, default_applied, and related origins.

Accepted candidate decisions pending final review:

- recommendations.evidence_chain_id remains nullable for MVP, with service-layer fallback to trace_id plus evidence_refs_json.
- PostgreSQL enum type names remain compact for this candidate; snake_case normalization is a main-controller decision before apply.
- Single down_revision=None baseline is acceptable only under an empty-schema baseline initialization assumption. A non-empty target requires a different migration strategy.

Current gate:

- Do not apply the migration yet.
- Send the revised candidate to traceability/quality-control for a focused re-review.
- If traceability passes, the main controller must decide whether enum naming normalization is required before apply approval.


## 22. Focused Traceability Re-Review Result

Traceability and quality-control completed focused re-review of the revised Stage 04 migration candidate.

Re-review result:

- Passed from the trace/evidence/quality contract perspective.
- No mandatory traceability corrections remain.
- Migration apply is no longer blocked by trace/evidence/quality contract concerns.
- Apply still requires main-controller approval and final backend preflight checks.

Accepted reviewed items:

- reassessment_jobs.previous_snapshot_id and reassessment_jobs.current_snapshot_id satisfy reassessment lineage for MVP.
- Priority A compound indexes are aligned between ORM and migration.
- trace_events.parent_event_id self-reference is reasonable.
- trace_events.source_record_type and source_record_id are sufficient for future source-record queries.
- recommendations.evidence_chain_id may remain nullable for MVP if service-layer fallback to trace_id plus evidence_refs_json is enforced.
- Compact PostgreSQL enum type names are not a traceability blocker.
- Single down_revision=None baseline is acceptable only for an empty schema or an explicit baseline process.

Recommended non-blocking follow-ups:

- Add trace_events(source_record_type, source_record_id) index later if source-record lookup becomes frequent.
- Add an application or database check that previous_snapshot_id and current_snapshot_id are not equal.
- Document the evidence_chain_id fallback invariant in service/API behavior.

## 23. Project Coordination Board

Current phase: Stage 04 migration candidate passed focused traceability re-review; apply approval can proceed with strict preflight.

Active blocker:

- No traceability blocker remains. The remaining gate is operational: backend must run final preflight checks against the current development database before alembic upgrade head is allowed.

Conversation priorities:

1. MedOrion-Small Models and Agent Orchestration: define model-service IO schema, CAP/COP disease-agent contract, model selection/fallback, error taxonomy, and required trace/evidence emissions.
2. MedOrion-Backend API and Database: hold full implementation; later reconcile backend and trace contracts with model-service contracts into schema/Alembic plan.
3. MedOrion-Frontend Doctor Workbench: wait for model output and trace query contracts before UI implementation.
4. MedOrion-Deployment and MLOps: monitor running infra and prepare, but do not start model-service until contract and source scaffold are approved.
5. MedOrion-Traceability and Quality Control: hold implementation; later review model/agent event emission compatibility.

Latest accepted deployment scaffold:

- Draft files are under /home/sygxdg/MedOrion/deploy and /home/sygxdg/MedOrion/docs/deployment.
- Deployment drafts have also been copied to /srv/medorion/deploy.
- PostgreSQL, Redis, and MinIO are base services and are currently running healthy under /srv/medorion/deploy.
- backend, frontend, model-service, and mlflow use Compose profiles.
- All service ports bind to 127.0.0.1 by default.
- Nginx is the only intended public HTTP/HTTPS entry point.
- model-service is CPU-first, batch size 1, concurrency 1, with /srv/medorion/models mounted read-only.

## 24. Open Architecture Questions

1. Which Python dependency manager should be standardized for backend implementation if not using system pip/venv.
2. Whether the initial Alembic skeleton should be generated immediately after backend model files are scaffolded.
3. Which model-serving protocol should be used after MVP if HTTP becomes insufficient: gRPC or task queue.
4. Whether CAP/COP labels and datasets are already available on the server, and where they should live.
5. Which LLM provider/runtime will be used for orchestration and explanation.
6. What clinical table schema is authoritative for the CAP/COP first task.
7. Whether host Nginx or containerized Nginx should own production TLS termination in MVP.
8. Whether backend-to-model-service HTTP remains sufficient past MVP or should be replaced by gRPC/task queue for heavier inference.

## 25. Decision Log

- 2026-05-31: MedOrion established as a multi-disease multimodal doctor-assistance platform, not a CAP/COP-only system.
- 2026-05-31: CAP/COP is first-stage demonstration disease task.
- 2026-05-31: Specialized small models handle disease judgement; large model handles orchestration, explanation, Q&A, and recommendation generation.
- 2026-05-31: Every recommendation requires trace_id and evidence chain.
- 2026-05-31: Missing table values require active doctor questioning before fallback strategy.
- 2026-05-31: Continuous learning is offline and governed, not automatic real-time training.
- 2026-05-31: Dynamic feedback triggers reassessment, not real-time training.
- 2026-05-31: MVP deployment direction accepts Docker Compose, FastAPI backend, PostgreSQL, Redis, MinIO, separated small-model service containers, and separated persistent data/model/log/backup layers.
- 2026-05-31: /srv/medorion is the recommended deployment root; /home/sygxdg/MedOrion remains the current architecture/documentation workspace unless migrated deliberately.
- 2026-05-31: GPU deployment must be conservative because the available RTX 3050 Laptop GPU has 4 GiB VRAM; lightweight or quantized models and CPU fallback are required planning assumptions.

- 2026-05-31: Deployment Stage 02 scaffold is accepted as a draft: base services are PostgreSQL, Redis, and MinIO; backend, frontend, model-service, and MLflow remain profile-gated until source and Dockerfiles exist.

- 2026-05-31: MVP public exposure policy is local-only Compose ports plus Nginx as the single public 80/443 entry point; MinIO console and API remain local-only by default.

- 2026-05-31: Docker Hub pull timeout was resolved by configuring Docker daemon to use the existing local proxy at 127.0.0.1:7897; no registry mirror was configured.

- 2026-05-31: Foundation tooling installed: Docker 29.1.3, Compose 2.40.3, Nginx 1.24.0, Node v22.22.2, npm 10.9.7, pip 24.0, python3-venv, and ripgrep 14.1.0.

- 2026-05-31: Docker service is active and enabled; user sygxdg is in the docker group and can run docker directly.

- 2026-05-31: Nginx is installed but intentionally inactive and disabled until public routing is explicitly configured.

- 2026-05-31: Infra-only PostgreSQL, Redis, and MinIO are running healthy with local-only port bindings: 127.0.0.1:5432, 127.0.0.1:6379, 127.0.0.1:9000, and 127.0.0.1:9001.

- 2026-05-31: Docker daemon proxy is configured via /etc/systemd/system/docker.service.d/http-proxy.conf and depends on the local proxy at 127.0.0.1:7897 for outbound image pulls.

- 2026-05-31: /srv/medorion/data now contains persistent PostgreSQL, Redis, and MinIO data; destructive cleanup requires explicit confirmation.

- 2026-05-31: Backend Stage 01 contract accepted: module boundaries, backend-owned MVP entities, API path groups, and trace integration boundaries are documented.

- 2026-05-31: Backend owns core entities including patients, cases, multimodal assets, clinical observations, labs, EMR documents, model registry, inference tasks, recommendations, feedback, reassessment jobs, and dynamic state snapshots.

- 2026-05-31: trace_events, evidence_chain, and quality_reviews are delegated to the provenance and quality-control thread for detailed schema and taxonomy.

- 2026-05-31: recommendations must bind trace_id and should bind inference_task_id; missing-value consultation records must be doctor-first, statused, and trace-auditable.

- 2026-05-31: Traceability Stage 01 contract accepted: backend inference-task service is canonical trace_id generator, with one trace_id per inference_task and one trace per MVP reassessment inference run.

- 2026-05-31: Stage 01 trace_events taxonomy is frozen, covering case/input validation, missing-value handling, model invocation/result, orchestration, recommendation, feedback, reassessment, and quality-review events.

- 2026-05-31: Evidence chain is an evidence_nodes/evidence_edges directed graph; MVP may use trace_id as evidence_chain_id.

- 2026-05-31: Missing-value audit states are pending, answered, default_applied, waived_by_doctor, and expired; defaulted values must be distinguishable from doctor-provided values.

- 2026-05-31: quality_reviews target recommendation, trace, model_output, missing_value_decision, and reassessment with statuses open, investigating, resolved, and dismissed.

- 2026-05-31: Model orchestration Stage 01 contract accepted: disease_agent interface, model-service API, request/response schemas, CAP/COP output structure, fallback policy, error taxonomy, and CPU-first serving assumptions are documented.

- 2026-05-31: trace-bound model-service and disease-agent requests must carry upstream trace_id and must not generate replacement trace IDs.

- 2026-05-31: Backend Stage 02 schema/API plan accepted: backend, traceability, and model-orchestration contracts are merged into a unified MVP table/API/Alembic plan.

- 2026-05-31: MVP hard constraints accepted: inference_tasks.trace_id is required and unique; recommendations.trace_id and recommendations.inference_task_id are required; case_missing_value_queries.trace_id is required; defaulted values must be distinguishable from doctor-provided values.

- 2026-05-31: Next approved implementation scope is minimal backend skeleton only: app structure, router stubs, SQLAlchemy models/enums, initial Alembic skeleton, /health, config loading, and trace_id-aware logging.

- 2026-05-31: Backend Stage 03 minimal skeleton implemented under /srv/medorion/app/backend using Python venv and requirements.txt.

- 2026-05-31: Backend /health verified locally with uvicorn; backend Docker container was not started and Nginx remains disabled.

- 2026-05-31: SQLAlchemy skeleton includes core models and key trace constraints; several lower-priority tables remain ID-level skeletons pending Stage 04 field completion.

- 2026-05-31: Alembic skeleton and revision 0e36c2285187_stage03_initial_skeleton.py exist but have not been applied to PostgreSQL.

- 2026-05-31: Backend Stage 04 mostly completed: deferred models/enums, trace_id middleware/logging, and /health/live plus /health/ready are implemented.

- 2026-05-31: /health/ready is degraded because backend DATABASE_URL credentials do not match running PostgreSQL credentials; this is a configuration mismatch, not a backend process crash.

- 2026-05-31: Alembic revision a9d28e4978dd_stage04_schema_baseline_non_destructive.py exists but remains unapplied; autogenerate is blocked until DB credentials are aligned.

- 2026-05-31: Any need for .pth deep-learning model files must be routed through the main controller to ask the user for an exact path; no thread may scan, copy, move, or guess files from other project folders.

- 2026-05-31: Backend local .env was created on the server and aligned with running PostgreSQL, Redis, MinIO, and local model-service placeholder settings; secret values are not recorded in docs.

- 2026-05-31: Backend /health/live, /health/ready, and /health all return 200 through local venv/uvicorn verification; /health/ready is now ready.

- 2026-05-31: Alembic can connect to PostgreSQL; alembic check reports target database is not up to date because migrations remain intentionally unapplied.

- 2026-05-31: Main-controller review gate added before database migration finalization: traceability must review core table boundaries and trace/evidence fields before any Alembic apply is considered.

- 2026-05-31: Project direction remains accepted, but migration apply is explicitly blocked to avoid prematurely freezing unstable table structures, enums, or trace/evidence fields.

- 2026-05-31: Backend produced a non-applied Stage 04 Alembic DDL review draft covering 18 MVP tables, enums, FKs, indexes, and key trace constraints.

- 2026-05-31: Alembic upgrade remains blocked; the migration draft must be reviewed by traceability/quality-control before apply approval is considered.

- 2026-05-31: Review note: enum type names currently use compact naming such as valuesourcetype; naming style should be reviewed before migration apply.

- 2026-05-31: Frontend workbench proposal received: Next.js, TypeScript, Ant Design/ProComponents, React Flow, ECharts, and Cornerstone.js are accepted as a proposal, but frontend implementation remains on hold until schema/API review stabilizes.

- 2026-05-31: Corrected frontend environment facts: Node.js and npm are installed; pnpm is not installed; /srv/medorion/app/frontend does not exist yet.

- 2026-05-31: Traceability review conditionally passed the Stage 04 migration draft for trace_events, evidence graph, quality_reviews, and missing-value audit main contract, but migration apply remains blocked.

- 2026-05-31: Required migration corrections before apply consideration: add explicit reassessment previous/current snapshot lineage and align ORM model indexes with migration Priority A compound indexes.

- 2026-05-31: Recommended migration review decisions: choose evidence_chain_id nullability policy, consider trace_events parent/source references, decide enum type naming style, and confirm single baseline revision policy for empty-schema apply only.

- 2026-06-01: Backend revised the Stage 04 migration candidate: added reassessment previous/current snapshot lineage, aligned ORM and migration Priority A compound indexes, added trace_events parent self-reference, and added trace_events source_record_type/source_record_id.

- 2026-06-01: recommendations.evidence_chain_id remains nullable by decision, with MVP service-layer fallback through trace_id plus evidence_refs_json.

- 2026-06-01: Enum DB type names remain compact in the revised candidate; main controller must decide whether snake_case normalization is required before apply.

- 2026-06-01: Single baseline revision remains acceptable only for an empty-schema baseline initialization; apply remains blocked pending focused traceability re-review.

- 2026-06-01: Focused traceability re-review passed the revised Stage 04 migration candidate; no mandatory trace/evidence/quality corrections remain.

- 2026-06-01: reassessment snapshot lineage, Priority A compound indexes, trace_events parent/source references, nullable evidence_chain_id fallback, compact enum type names, and empty-schema baseline assumption are accepted from traceability perspective.

- 2026-06-01: Migration apply may enter approval execution only after backend preflight confirms target database state and no unexpected schema objects; Nginx/backend containers remain disabled.

- 2026-06-01: Restricted alembic upgrade head was executed against the local development database after preflight confirmed an empty public schema baseline assumption.

- 2026-06-01: First migration apply attempt failed due to duplicate enum creation; backend removed manual enum create/drop blocks and reran upgrade head successfully.

- 2026-06-01: Database is now at Alembic revision a9d28e4978dd with 18 MVP tables and key trace constraints applied.

- 2026-06-01: alembic check still reports ORM/database drift, mainly created_at/updated_at nullability/default mismatch and ORM field-level indexes not reflected in migration; Stage 05 drift convergence is required before deployment.

- 2026-06-01: Backend Stage 05 drift convergence completed; alembic current reports 9fd992e59a0c (head) and alembic check is clean.

- 2026-06-01: TimestampMixin was aligned to the applied baseline with nullable=True and server_default=func.now(); unnecessary ORM field-level indexes were reduced to prevent drift.

- 2026-06-01: Stage 05 head includes a drift probe revision 9fd992e59a0c_stage05_drift_probe.py with no business DDL expansion.

- 2026-06-01: Backend local health endpoints remain healthy; backend Docker, Nginx, model-service, diagnosis logic, training, and .pth operations remain untouched.

- 2026-06-01: Backend Stage 06 containerization completed: Dockerfile and .dockerignore created, medorion/backend:local built, backend container started on 127.0.0.1:8000, and container health checks pass.

- 2026-06-01: Nginx remains disabled; frontend, model-service, and MLflow remain stopped; no Alembic command or schema change occurred during containerization.

- 2026-06-01: Follow-up required: backend API stub stage should add or verify application-layer request logging with request_id and trace_id because container logs currently show mainly uvicorn access logs.

- 2026-06-01: Backend Stage 07 completed: domain API stubs and Pydantic schema stubs were added for patients, cases, assets, clinical, recommendations, inference, model registry, feedback, traces, and quality.

- 2026-06-01: Backend application request logging now records method, path, status, duration_ms, request_id, and trace_id; container logs verified request_id and trace_id propagation.

- 2026-06-01: Backend stubs return safe placeholder responses only; no diagnosis logic, model calls, training, automatic real-time training, schema changes, or .pth operations occurred.

- 2026-06-01: Frontend doctor workbench may begin Stage 01 project initialization and mock API adapter against local backend stubs under /srv/medorion/app/frontend.
