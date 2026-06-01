# MedOrion Traceability Stage 01 Contract

Last updated: 2026-05-31 Asia/Shanghai
Owner thread: MedOrion traceability and quality-control system
Scope: Stage 01 defines trace, evidence, and quality-control contracts only. No full backend implementation, no large Alembic rollout, no frontend provenance graph implementation, and no model training.

## 0. Scope and Non-Goals

This document freezes the Stage 01 contract for MedOrion traceability and quality-control. It complements the backend Stage 01 contract at `/home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_01_CONTRACT.md`.

Stage 01 goals:
1. Define the `trace_id` lifecycle and propagation rules.
2. Define the `trace_events` taxonomy and required fields.
3. Define the `evidence_chain` graph contract with node and edge schemas.
4. Define missing-value consultation audit states and trace behavior.
5. Define `quality_reviews` workflow, attribution categories, and links to doctor feedback.
6. Define dynamic state snapshot trace relationships for reassessment.
7. Define trace query API drafts for backend and frontend integration.
8. Define table ownership boundaries between traceability and backend core modules.

Stage 01 non-goals:
1. Do not implement full backend code.
2. Do not execute large-scale Alembic migrations.
3. Do not train small models or large models.
4. Do not implement the frontend provenance graph.
5. Do not implement automatic real-time training.
6. Do not create provider-specific LLM integration logic.

## 1. Core Principles

1. Every recommendation must be reproducible at the evidence-contract level.
2. Every model-facing or doctor-facing recommendation must carry a `trace_id`.
3. No clinically relevant missing value may be silently imputed for recommendations.
4. Missing values must be handled in this order: detect, ask doctor, record answer or waiver, apply auditable default only when unresolved by workflow policy.
5. Traceability records explain what happened. They do not replace backend-owned clinical records.
6. Evidence nodes and trace events must reference source records rather than duplicating large clinical payloads.
7. Dynamic patient updates trigger reassessment and comparison. They do not trigger automatic real-time training.
8. Doctor feedback is part of the evidence and quality loop, but it is not an automatic model update.

## 2. `trace_id` Lifecycle

### 2.1 Who Generates `trace_id`

The backend inference-task service is the canonical generator of `trace_id` for recommendation-producing workflows.

Generation rule:
1. When a new `inference_task` is accepted, backend creates a globally unique `trace_id` before orchestration starts.
2. The generated `trace_id` is stored on `inference_tasks.trace_id` and propagated to all downstream services.
3. Model services, orchestrators, disease agents, missing-value consultation services, recommendation services, feedback services, and quality-control services must not create replacement trace IDs for the same inference task.
4. If a downstream service receives a request without `trace_id`, it must reject the request or return a typed contract error. It must not create an implicit trace.

Recommended format:
1. Opaque string, sortable UUIDv7 or ULID preferred.
2. The value must not encode patient-identifiable information.
3. Public API responses may expose `trace_id` to authenticated clinical users for audit navigation.

### 2.2 When `trace_id` Is Generated

`trace_id` is generated at the first durable boundary where MedOrion commits to producing an inference or reassessment audit trail.

Required generation points:
1. `POST /api/v1/cases/{case_id}/inference-tasks`
2. `POST /api/v1/reassessment-jobs` when the reassessment creates or schedules a new inference run
3. Any internal backend workflow that creates an inference task from dynamic patient updates

Events before inference-task creation, such as case creation or raw input upload, may be recorded under an existing active trace only when they are part of an already started inference workflow. Otherwise they remain backend audit records until an inference task references them.

### 2.3 One `inference_task` and One `trace_id`

Stage 01 rule:
1. One `inference_task` has exactly one required `trace_id`.
2. One `trace_id` belongs to exactly one canonical `inference_task`.
3. One inference task may produce multiple recommendation revisions or multiple recommendation records, but they must share the same `trace_id` and use recommendation version fields.
4. A retry of the same failed infrastructure step keeps the same `trace_id` and records retry events.
5. A new clinical interpretation run after changed inputs must create a new `inference_task` and new `trace_id`.

### 2.4 Reassessment and `trace_id`

A reassessment is a new clinical evaluation after new or changed patient data. It is not real-time training.

Reassessment rule:
1. `reassessment_jobs.trace_id` is required.
2. If a reassessment creates an inference task, `reassessment_jobs.trace_id` and `inference_tasks.trace_id` should be the same for MVP.
3. Later versions may allow a parent reassessment trace with child inference traces, but Stage 01 should use one trace per reassessment inference run.
4. The reassessment trace must record the prior state snapshot, new state snapshot, changed inputs, comparison result, and new recommendation if generated.
5. The reassessment trace may reference earlier trace IDs through `payload_json.related_trace_ids` and evidence edges of type `references`.

### 2.5 Relation to `case_id`, `patient_id`, and `recommendation_id`

Association rules:
1. `trace_id` must always bind to `case_id`.
2. `patient_id` is nullable in trace events to support de-identified or pre-patient ingestion flows, but should be present when the case has a patient reference.
3. `recommendations.trace_id` is required.
4. `recommendations.inference_task_id` is required for MVP.
5. `doctor_feedback.trace_id` is required and should reference `recommendation_id` when feedback is about a recommendation.
6. `quality_reviews.trace_id` is required when the review concerns one trace. It may additionally reference `recommendation_id`, `model_output` evidence node, or missing-value decision.
7. `case_id` can have many traces over time, especially after reassessments.
8. `patient_id` can have many cases and many traces through those cases.

## 3. `trace_events` Taxonomy

`trace_events` is the append-only event log for trace-level provenance. Events describe steps, decisions, inputs, outputs, and audit-relevant state transitions.

### 3.1 Required Event Types

| event_type | Required trigger | Typical actor_type | Required payload highlights |
| --- | --- | --- | --- |
| `case_created` | Case is created and included in a trace-bound workflow | `doctor` or `system` | `case_id`, `case_status` |
| `input_uploaded` | CT, MRI, table, lab, EMR, or other asset is attached | `doctor` or `system` | `input_id`, `modality`, `object_ref`, `checksum` |
| `input_validated` | Input validation finishes | `system` | `input_id`, `validation_status`, `issues` |
| `missing_value_detected` | Required or recommended field is missing or invalid | `system` | `field_path`, `clinical_importance`, `blocking_level` |
| `doctor_question_asked` | Doctor is asked to provide, confirm, waive, or explain a missing value | `system` | `question_id`, `field_path`, `question_text`, `expires_at` |
| `doctor_answer_received` | Doctor answers missing-value question | `doctor` | `question_id`, `answer_value`, `answer_source`, `answered_at` |
| `default_strategy_applied` | System applies configured default after unresolved missing value | `system` | `field_path`, `strategy_code`, `default_value`, `reason`, `policy_version` |
| `inference_task_created` | Durable inference task is created | `system` | `inference_task_id`, `task_type`, `requested_modalities` |
| `model_selected` | Orchestrator or disease agent selects a model version | `orchestrator` or `system` | `model_id`, `model_version_id`, `selection_reason`, `applicability` |
| `model_invoked` | Small model, rule engine, or LLM call starts | `system` | `invocation_id`, `model_version_id`, `input_refs`, `prompt_template_version` |
| `model_result_received` | Model or rule result is returned | `system` | `invocation_id`, `output_ref`, `confidence`, `uncertainty`, `status` |
| `orchestrator_decision` | LLM or orchestration layer chooses routing, reconciliation, or next action | `orchestrator` | `decision_type`, `inputs_considered`, `rationale_ref`, `selected_agent` |
| `recommendation_generated` | Recommendation is generated or revised | `orchestrator` or `system` | `recommendation_id`, `recommendation_version`, `evidence_chain_id` |
| `recommendation_viewed` | Doctor opens or views recommendation | `doctor` | `recommendation_id`, `view_context`, `viewed_at` |
| `doctor_feedback_recorded` | Doctor accepts, rejects, edits, or comments | `doctor` | `feedback_id`, `recommendation_id`, `feedback_type`, `clinical_rationale` |
| `reassessment_requested` | New data or doctor action requests reassessment | `doctor` or `system` | `reassessment_job_id`, `trigger_type`, `changed_input_refs` |
| `reassessment_completed` | Reassessment finishes | `system` | `reassessment_job_id`, `new_snapshot_id`, `comparison_summary`, `recommendation_id` |
| `quality_review_created` | QC review is opened | `qc_agent`, `doctor`, or `system` | `quality_review_id`, `review_target_type`, `reason` |
| `quality_issue_detected` | QC identifies a potential issue | `qc_agent` or `system` | `quality_review_id`, `issue_type`, `attribution_candidate`, `severity` |

### 3.2 Optional Extension Event Types

The taxonomy may later add event types without breaking Stage 01 if consumers ignore unknown event types and rely on the common event fields. Candidate future types include `model_retry_scheduled`, `model_timeout`, `knowledge_reference_selected`, `evidence_conflict_detected`, `trace_exported`, and `quality_review_resolved`.

## 4. `trace_events` Required Fields

Trace event table owned by traceability:

| Field | Type draft | Required | Notes |
| --- | --- | --- | --- |
| `id` | UUID or ULID | yes | Event primary key. |
| `trace_id` | string | yes | Required trace reference. |
| `case_id` | UUID or string | yes | Backend case reference. |
| `patient_id` | UUID or string | nullable | Present when known. |
| `event_type` | string enum | yes | Must use taxonomy or approved extension. |
| `actor_type` | string enum | yes | `doctor`, `system`, `orchestrator`, `disease_agent`, `small_model`, `large_model`, `qc_agent`, `admin`. |
| `actor_id` | string | nullable | User ID, service ID, agent ID, or model invocation actor. |
| `source_module` | string | yes | Example: `cases`, `clinical_tables`, `inference_tasks`, `orchestrator`, `traceability`, `quality_control`. |
| `event_time` | timestamptz | yes | When the event occurred. |
| `payload_json` | JSONB | yes | Event-specific structured details. |
| `parent_event_id` | UUID or ULID | nullable | Links causally related events. |
| `severity` | string enum | yes | `info`, `warning`, `error`, `critical`. |
| `created_at` | timestamptz | yes | Persistence timestamp. |

Recommended additional fields for future migration planning: `correlation_id`, `idempotency_key`, `schema_version`, `source_record_type`, and `source_record_id`.

Payload conventions:
1. `payload_json` must avoid large binary blobs and full PHI-heavy documents.
2. Large objects must be referenced by MinIO object references or backend record IDs.
3. Model inputs and outputs should be referenced as evidence nodes or object refs when they are large.
4. Payloads must include version references for policies, models, prompts, and templates when used.
5. Payloads must be stable enough for audit export, but not treated as the primary clinical record.

## 5. `evidence_chain` Graph Contract

The evidence chain is a directed graph under one trace. It explains how raw inputs, derived features, model outputs, rules, LLM reasoning steps, recommendations, and doctor feedback relate to each other.

Stage 01 storage recommendation:
1. `evidence_nodes` table for graph nodes.
2. `evidence_edges` table for graph edges.
3. `evidence_chain_id` may be represented as `trace_id` for MVP, or as a separate ID if multiple evidence graphs per trace are needed later.

### 5.1 Evidence Node Schema

| Field | Type draft | Required | Notes |
| --- | --- | --- | --- |
| `id` | UUID or ULID | yes | Node primary key. |
| `trace_id` | string | yes | Owning trace. |
| `case_id` | UUID or string | yes | Case reference. |
| `patient_id` | UUID or string | nullable | Patient reference when known. |
| `node_type` | string enum | yes | See node types below. |
| `source_module` | string | yes | Producing module. |
| `source_record_type` | string | nullable | Backend table or service object type. |
| `source_record_id` | string | nullable | Backend record ID. |
| `label` | string | yes | Human-readable short label. |
| `summary` | text | nullable | Doctor-facing concise summary. |
| `payload_json` | JSONB | yes | Structured node details. |
| `confidence` | numeric | nullable | 0 to 1 when applicable. |
| `uncertainty` | JSONB | nullable | Calibration, interval, caveat, or unknown reason. |
| `status` | string | yes | `active`, `superseded`, `retracted`, `conflicted`, `defaulted`. |
| `created_at` | timestamptz | yes | Persistence timestamp. |

Required `node_type` values:
1. `input`: uploaded or entered source data such as CT, MRI, lab file, table row, EMR note, wearable batch.
2. `clinical_feature`: normalized or derived clinical feature.
3. `lab_result`: structured lab measurement or extracted lab fact.
4. `image_finding`: image preprocessing output, radiology finding, or model-derived visual feature.
5. `model_output`: small model, rule engine, or LLM structured output.
6. `rule_result`: deterministic rule or guideline check result.
7. `llm_reasoning_step`: bounded reasoning summary, orchestration decision rationale, or explanation step. It must reference prompt/template version where applicable.
8. `recommendation`: final or revised recommendation record.
9. `doctor_feedback`: doctor confirmation, edit, rejection, waiver, or comment.

### 5.2 Evidence Edge Schema

| Field | Type draft | Required | Notes |
| --- | --- | --- | --- |
| `id` | UUID or ULID | yes | Edge primary key. |
| `trace_id` | string | yes | Owning trace. |
| `case_id` | UUID or string | yes | Case reference. |
| `source_node_id` | UUID or ULID | yes | From node. |
| `target_node_id` | UUID or ULID | yes | To node. |
| `edge_type` | string enum | yes | See edge types below. |
| `weight` | numeric | nullable | Strength of relationship, 0 to 1 when applicable. |
| `rationale` | text | nullable | Brief explanation for the link. |
| `payload_json` | JSONB | yes | Structured edge details. |
| `created_at` | timestamptz | yes | Persistence timestamp. |

Required `edge_type` values:
1. `supports`: source evidence supports target conclusion or recommendation.
2. `contradicts`: source evidence conflicts with target conclusion or recommendation.
3. `derived_from`: target is derived from source through preprocessing, extraction, model inference, or calculation.
4. `references`: source references target metadata, guideline, prior trace, object, or source record.
5. `overrides`: doctor feedback, policy, or higher-priority evidence overrides a previous node.
6. `missing_value_defaulted`: target uses a defaulted missing-value decision derived from unresolved source field.

### 5.3 Confidence, Uncertainty, and Conflict Handling

Confidence rules:
1. `confidence` is optional but should be present for model outputs and rule results when the producer provides it.
2. Confidence must not be invented by downstream components if the upstream model does not provide it.
3. Use `uncertainty` to capture calibration status, confidence interval, missing-input impact, out-of-distribution warnings, and caveats.
4. `weight` on edges describes evidence-link strength, not clinical truth.

Conflict rules:
1. Contradictory evidence must be represented with `contradicts` edges instead of being hidden.
2. A recommendation that depends on conflicting evidence must include a visible uncertainty or caveat node/field.
3. If doctor feedback rejects or modifies a recommendation, create a `doctor_feedback` node and an `overrides` edge to the affected recommendation node.
4. If QC detects a likely error source, create or update a `quality_review` and link the relevant evidence node or event.

### 5.4 External References

MinIO object references:
1. Store in `payload_json.object_ref` or `payload_json.input_refs`.
2. Required fields: `bucket`, `object_key`, `etag` or `checksum`, `content_type`, `size_bytes` when known.
3. Do not store raw binary payloads in evidence nodes.

Model references:
1. Use backend-owned `model_registry` and `model_versions` IDs.
2. Evidence node payloads should include `model_id`, `model_version_id`, `model_name`, `version_label`, and `model_contract_version` when applicable.
3. Model invocation event payloads should include `invocation_id`, `input_node_ids`, `output_node_id`, `runtime_env`, and `service_version` when available.

Prompt and template references:
1. LLM-related nodes and events must include `prompt_template_id` and `prompt_template_version` when prompts/templates are used.
2. If a prompt is dynamically assembled, store a template/version reference plus hashed or redacted prompt material as allowed by privacy policy.
3. Prompt references are audit metadata, not a license to expose PHI in logs.

Knowledge-base references:
1. Use `payload_json.knowledge_refs` with `kb_id`, `kb_version`, `document_id`, `chunk_id`, `retrieval_score`, and `citation_label` where available.
2. Knowledge references should become evidence nodes or be referenced by `references` edges when they materially affect the recommendation.

## 6. Missing-Value Consultation Audit Model

Backend core may own the consultation record table, but traceability defines the audit states and required trace/evidence behavior.

Required statuses:
1. `pending`: missing value detected and doctor question is open.
2. `answered`: doctor provided a value, correction, or explanation.
3. `default_applied`: system applied configured default because the issue remained unresolved by workflow policy.
4. `waived_by_doctor`: doctor explicitly allowed proceeding without the value or marked it clinically unavailable.
5. `expired`: question exceeded configured response window without answer, before or alongside default application depending on policy.

Recommended consultation fields:
1. `id`
2. `case_id`
3. `patient_id` nullable
4. `inference_task_id`
5. `trace_id`
6. `field_path`
7. `field_label`
8. `clinical_importance`: `required`, `recommended`, `optional`
9. `blocking_level`: `blocking`, `degrades_confidence`, `informational`
10. `question_text`
11. `status`
12. `doctor_id` nullable
13. `doctor_response_json` nullable
14. `default_strategy_code` nullable
15. `default_value_json` nullable
16. `default_reason` nullable
17. `policy_version`
18. `expires_at` nullable
19. `created_at`, `updated_at`

### 6.1 Status to Trace Event Mapping

| Status transition | Required trace event | Evidence-chain behavior |
| --- | --- | --- |
| new missing field found | `missing_value_detected` | Create `clinical_feature` or `input` node with `status=active` and uncertainty describing missingness. |
| question opened | `doctor_question_asked` | Create or update missing-value decision node, usually `clinical_feature`, and link from affected input with `derived_from`. |
| doctor answered | `doctor_answer_received` | Create `doctor_feedback` node or clinical feature node from answer; link with `overrides` or `derived_from`. |
| default applied | `default_strategy_applied` | Create defaulted `clinical_feature` node with `status=defaulted`; add `missing_value_defaulted` edge from missing field node. |
| doctor waived | `doctor_answer_received` with waiver payload, optional extension event later | Create `doctor_feedback` node; link with `overrides`; downstream recommendation must show caveat if clinically relevant. |
| expired | `default_strategy_applied` if default follows, or `missing_value_detected` update event if it only expires | Mark uncertainty and policy reason in node payload; if default follows, add `missing_value_defaulted` edge. |

Rules:
1. `default_applied` must always be preceded in the same trace by `missing_value_detected` and `doctor_question_asked` unless the field is explicitly configured as non-askable. Non-askable fields require policy justification in payload.
2. A defaulted value must never be indistinguishable from a doctor-entered value.
3. Doctor answer should override default only through a new event and evidence edge. Historical default events remain immutable.
4. Recommendations that rely on defaulted fields must reference the defaulted node and include the impact in uncertainty or caveat fields.

## 7. `quality_reviews` Quality-Control Loop

`quality_reviews` records review and closure of potential trace, evidence, model, data, or workflow issues.

### 7.1 Review Targets

Required `review_target_type` values:
1. `recommendation`
2. `trace`
3. `model_output`
4. `missing_value_decision`
5. `reassessment`

A review may target one primary object and include secondary references in `related_refs_json`.

### 7.2 Review Statuses

Required `status` values:
1. `open`: issue or review request has been created.
2. `investigating`: human or QC agent is examining evidence.
3. `resolved`: review concluded with an action, correction, or accepted finding.
4. `dismissed`: review concluded no issue or insufficient support.

### 7.3 Error Attribution Categories

Required `error_attribution` values:
1. `data_quality`: raw input, asset quality, inconsistent clinical data, invalid lab value, corrupted document, or bad source metadata.
2. `model_error`: specialized model, rule model, calibration, confidence, out-of-scope input, or version behavior issue.
3. `orchestration_error`: wrong disease agent, wrong routing, bad reconciliation, LLM misinterpretation, prompt/template issue, or failure to surface uncertainty.
4. `missing_value_policy`: missing-value detection, doctor consultation, waiver, default strategy, default reason, or default impact issue.
5. `human_feedback`: incorrect, conflicting, delayed, or ambiguous doctor feedback or labels.
6. `system_error`: service failure, timeout, stale dynamic data, delayed event, bad object reference, duplicated event, or integration issue.

### 7.4 Quality Review Schema

| Field | Type draft | Required | Notes |
| --- | --- | --- | --- |
| `id` | UUID or ULID | yes | Review primary key. |
| `trace_id` | string | yes | Owning trace when review concerns a trace-bound object. |
| `case_id` | UUID or string | yes | Case reference. |
| `patient_id` | UUID or string | nullable | Patient reference when known. |
| `review_target_type` | string enum | yes | Required values above. |
| `review_target_id` | string | yes | Recommendation ID, evidence node ID, event ID, missing decision ID, or reassessment ID. |
| `status` | string enum | yes | `open`, `investigating`, `resolved`, `dismissed`. |
| `severity` | string enum | yes | `low`, `medium`, `high`, `critical`. |
| `opened_by_type` | string enum | yes | `doctor`, `qc_agent`, `system`, `admin`. |
| `opened_by_id` | string | nullable | Actor reference. |
| `reason` | text | yes | Why review exists. |
| `error_attribution` | string enum | nullable | Required by resolution unless dismissed as no issue. |
| `attribution_confidence` | numeric | nullable | 0 to 1. |
| `findings_json` | JSONB | yes | Findings, evidence refs, and uncertainty. |
| `related_refs_json` | JSONB | yes | Related event IDs, node IDs, model versions, doctor feedback IDs, prior trace IDs. |
| `resolution_summary` | text | nullable | Required when resolved or dismissed. |
| `resolved_by_type` | string enum | nullable | `doctor`, `qc_agent`, `system`, `admin`. |
| `resolved_by_id` | string | nullable | Actor reference. |
| `created_at` | timestamptz | yes | Persistence timestamp. |
| `updated_at` | timestamptz | yes | Last update timestamp. |
| `resolved_at` | timestamptz | nullable | Closure timestamp. |

### 7.5 Relationship to Doctor Feedback

1. Doctor feedback can create or update a quality review when it rejects, edits, or flags a recommendation.
2. A `doctor_feedback_recorded` event must be written for feedback itself.
3. If feedback indicates possible system error, model issue, data issue, or missing-value issue, create `quality_review_created`.
4. Quality review resolution may reference doctor feedback, but must not overwrite the original feedback record.
5. Doctor feedback may become an evidence node and may use an `overrides` edge to a recommendation node.
6. Resolved quality reviews may feed offline evaluation datasets, but must not trigger automatic real-time training.

## 8. Dynamic State Snapshots and Reassessment Trace Relationship

Backend owns `dynamic_state_snapshots`. Traceability defines how snapshots participate in trace and evidence chains.

### 8.1 New Data and New Trace

When new CT, MRI, lab, EMR, wearable, or doctor observation data is added:
1. Backend records the new input in the appropriate core table.
2. Backend creates or updates a `dynamic_state_snapshot` summarizing case state after the new data.
3. If reassessment is requested or policy-triggered, backend creates `reassessment_job` with required `trace_id`.
4. The reassessment trace records `reassessment_requested` with changed input refs and prior snapshot ref.
5. Reassessment creates evidence nodes for new inputs, prior snapshot summary, new snapshot summary, model outputs, and recommendation if generated.
6. Reassessment completes with `reassessment_completed` and a comparison summary.

### 8.2 Reassessment, Not Real-Time Training

Reassessment means rerunning validation, orchestration, disease-agent judgement, model inference, and recommendation generation against updated patient state.

It does not mean:
1. Training models on the new patient data immediately.
2. Changing model weights or prompt behavior silently.
3. Replacing model versions outside the model registry approval process.

Required trace payloads must include the model versions and prompt/template versions used during reassessment, even when unchanged from the prior trace.

### 8.3 Comparing Previous and Current State

Recommended snapshot comparison payload:
1. `previous_snapshot_id`
2. `current_snapshot_id`
3. `changed_input_refs`
4. `added_modalities`
5. `removed_or_superseded_inputs`
6. `changed_clinical_features`
7. `changed_lab_results`
8. `changed_image_findings`
9. `changed_emr_facts`
10. `risk_or_recommendation_delta`
11. `uncertainty_delta`
12. `comparison_summary`

Evidence-chain rule:
1. Create `input`, `clinical_feature`, `lab_result`, or `image_finding` nodes for new material data.
2. Use `references` edges to prior trace nodes or prior snapshots when explaining change.
3. Use `derived_from` edges for new derived findings.
4. Use `contradicts` edges when new data conflicts with prior evidence.
5. Use `supports` edges when new data strengthens a prior recommendation or a new recommendation.

## 9. Trace Query API Contract Draft

These endpoints are contract suggestions for backend and frontend. They do not imply implementation in this stage.

### 9.1 `GET /api/v1/traces/{trace_id}`

Purpose: fetch trace summary.

Response draft:
1. `trace_id`
2. `case_id`
3. `patient_id` nullable
4. `inference_task_id` nullable
5. `reassessment_job_id` nullable
6. `recommendation_ids`
7. `status`: `running`, `completed`, `failed`, `partially_completed`, `superseded`
8. `started_at`
9. `completed_at` nullable
10. `event_counts_by_type`
11. `has_missing_value_defaults`
12. `has_quality_issues`
13. `latest_quality_review_status` nullable
14. `related_trace_ids`

### 9.2 `GET /api/v1/traces/{trace_id}/events`

Purpose: fetch ordered trace timeline.

Query parameters:
1. `event_type` optional repeated filter
2. `severity` optional
3. `source_module` optional
4. `after` optional timestamp
5. `before` optional timestamp
6. `limit` and `cursor`

Response draft:
1. `trace_id`
2. `events`: ordered by `event_time`, then `created_at`
3. `next_cursor` nullable

### 9.3 `GET /api/v1/traces/{trace_id}/evidence-chain`

Purpose: fetch graph data for audit and frontend provenance visualization.

Response draft:
1. `trace_id`
2. `case_id`
3. `patient_id` nullable
4. `evidence_chain_id`
5. `nodes`
6. `edges`
7. `conflicts`
8. `defaulted_missing_values`
9. `model_versions_used`
10. `knowledge_refs_used`
11. `quality_review_refs`

Frontend graph should receive enough fields to render source type, label, status, confidence, uncertainty, conflict state, and links to detail panels. It should not receive raw binary objects or unrestricted PHI-heavy payloads.

### 9.4 `GET /api/v1/cases/{case_id}/traces`

Purpose: list all traces for a case, including reassessments and superseded recommendations.

Query parameters:
1. `patient_id` optional if backend requires additional scoping
2. `trace_status` optional
3. `has_quality_issues` optional
4. `limit` and `cursor`

Response draft:
1. `case_id`
2. `traces`: summary records with `trace_id`, `inference_task_id`, `recommendation_ids`, `started_at`, `completed_at`, `status`, `trigger_type`, `related_trace_ids`
3. `next_cursor` nullable

### 9.5 `POST /api/v1/quality-reviews`

Purpose: create a quality review from doctor feedback, QC agent, system check, or admin review.

Request draft:
1. `trace_id`
2. `case_id`
3. `patient_id` nullable
4. `review_target_type`
5. `review_target_id`
6. `severity`
7. `reason`
8. `opened_by_type`
9. `opened_by_id` nullable
10. `related_refs_json`

Response draft:
1. `quality_review_id`
2. `trace_id`
3. `status`
4. `created_at`

Recommended future endpoints:
1. `GET /api/v1/quality-reviews/{quality_review_id}`
2. `PATCH /api/v1/quality-reviews/{quality_review_id}` for status, attribution, findings, and resolution updates
3. `GET /api/v1/traces/{trace_id}/quality-reviews`

## 10. Table Ownership Recommendations

### 10.1 Defined by Traceability Thread

Traceability owns detailed contracts for:
1. `trace_events`
2. `evidence_nodes`
3. `evidence_edges`
4. `quality_reviews`

Traceability also defines status and event behavior for missing-value consultation records, but backend core may own the physical table because it belongs to clinical table workflow.

### 10.2 Backend Core Tables Requiring Trace References

Backend core tables should retain:
1. `inference_tasks.trace_id`: required, unique for the task.
2. `recommendations.trace_id`: required.
3. `recommendations.inference_task_id`: required for MVP.
4. `recommendations.evidence_chain_id`: recommended. For MVP this may equal `trace_id`.
5. `doctor_feedback.trace_id`: required.
6. `doctor_feedback.recommendation_id`: required when feedback targets a recommendation.
7. `reassessment_jobs.trace_id`: required.
8. `dynamic_state_snapshots.trace_ref` or `trace_id`: nullable for snapshots not tied to inference, required for reassessment-produced snapshots.
9. `case_missing_value_queries.trace_id`: required.
10. `case_missing_value_queries.inference_task_id`: required when tied to inference.
11. `case_inputs` or `multimodal_assets.trace_ref`: optional, only when uploaded inside a trace-bound workflow.

### 10.3 Contract Boundary

Backend core modules own clinical records, task state, recommendation records, and feedback records.

Traceability owns event history, evidence graph, and quality review closure. Traceability should reference backend records by ID and source type instead of duplicating ownership.

## 11. Frontend Provenance Data Fields

The frontend provenance graph and audit panels should receive at least:
1. `trace_id`
2. `case_id`
3. `patient_id` nullable or de-identified display reference
4. timeline events with `event_type`, `event_time`, `actor_type`, `source_module`, `severity`, and safe payload summary
5. evidence nodes with `node_type`, `label`, `summary`, `confidence`, `uncertainty`, `status`, and source refs
6. evidence edges with `edge_type`, `source_node_id`, `target_node_id`, `weight`, and rationale
7. missing-value decisions including status, field path, question, doctor answer or waiver, default strategy, default reason, and policy version
8. model references including model name, model version, applicability, confidence, and output summary
9. knowledge references including KB version and citation labels
10. recommendation ID, version, final suggestion summary, uncertainty, and caveats
11. doctor feedback status and summary
12. quality review status, severity, attribution, and resolution summary
13. related trace IDs for reassessment comparison

No frontend contract should require raw MinIO object content in trace query responses. The backend may provide authorized download/view URLs through separate asset APIs.

## 12. Stage 01 Acceptance Criteria

This contract is satisfied when:
1. Backend can add required trace references to core table plans.
2. Frontend can design a provenance timeline and graph against stable fields.
3. Model/orchestration threads know what events and evidence nodes they must emit.
4. Missing-value handling is doctor-first and auditable.
5. Quality-control reviews can attribute likely error source without rewriting original evidence.
6. Reassessment can be represented as a new trace with comparison to prior state.

## 13. Main-Controller Writeback Summary

1. Traceability Stage 01 contract defines one canonical `trace_id` per `inference_task` and one trace per MVP reassessment inference run.
2. Required trace event taxonomy is frozen for Stage 01, including missing-value, model, orchestration, recommendation, feedback, reassessment, and quality-review events.
3. Evidence graph is represented by `evidence_nodes` and `evidence_edges`; MVP may use `trace_id` as `evidence_chain_id`.
4. Missing-value handling must emit trace events for detection, doctor question, doctor answer or waiver, expiration/default, and evidence links for defaulted values.
5. Quality reviews target recommendation, trace, model output, missing-value decision, or reassessment and use status `open`, `investigating`, `resolved`, `dismissed`.
6. Error attribution categories are `data_quality`, `model_error`, `orchestration_error`, `missing_value_policy`, `human_feedback`, and `system_error`.
7. Dynamic state updates create reassessment traces and snapshot comparisons. They do not imply automatic real-time training.
8. Trace query API drafts are defined for trace summary, events, evidence chain, case trace list, and quality-review creation.
9. Traceability owns `trace_events`, `evidence_nodes`, `evidence_edges`, and `quality_reviews`; backend core keeps required trace references on task, recommendation, feedback, reassessment, snapshot, and missing-value records.
