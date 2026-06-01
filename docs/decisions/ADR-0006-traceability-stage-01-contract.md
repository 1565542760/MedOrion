# ADR-0006: Traceability Stage 01 Contract

Date: 2026-05-31
Status: Accepted
Source: Traceability and Quality-Control Stage 01 report

## Context

The traceability and quality-control thread produced /home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md. The document defines trace, evidence, missing-value audit, quality-review, dynamic reassessment provenance, and trace query contracts.

## Decision

The Traceability Stage 01 contract is accepted.

The backend inference-task service is the canonical trace_id generator. One inference_task has exactly one trace_id. One trace_id belongs to exactly one canonical inference_task. MVP reassessment inference runs use one new trace_id.

The Stage 01 trace_events taxonomy is accepted:

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

Evidence chains are represented as directed graphs using evidence_nodes and evidence_edges. Node types include input, clinical_feature, lab_result, image_finding, model_output, rule_result, llm_reasoning_step, recommendation, and doctor_feedback. Edge types include supports, contradicts, derived_from, references, overrides, and missing_value_defaulted.

Missing-value audit states are pending, answered, default_applied, waived_by_doctor, and expired. Defaulted values must be traceable and distinguishable from doctor-provided values.

Quality reviews target recommendation, trace, model_output, missing_value_decision, and reassessment. Status values are open, investigating, resolved, and dismissed. Error attribution categories are data_quality, model_error, orchestration_error, missing_value_policy, human_feedback, and system_error.

## Accepted Trace Query API Drafts

- GET /api/v1/traces/{trace_id}
- GET /api/v1/traces/{trace_id}/events
- GET /api/v1/traces/{trace_id}/evidence-chain
- GET /api/v1/cases/{case_id}/traces
- POST /api/v1/quality-reviews

## Ownership

Traceability owns trace_events, evidence_nodes, evidence_edges, and quality_reviews.

Backend core tables must retain trace references on inference_tasks, recommendations, doctor_feedback, reassessment_jobs, dynamic_state_snapshots, and case_missing_value_queries.

## Consequences

The small-model and agent orchestration thread is now unblocked and should define model-service IO, CAP/COP disease-agent workflow, model selection/fallback, error/retry behavior, and model/orchestrator trace event and evidence graph emission rules.

Backend schema implementation, frontend provenance graph implementation, and model-service deployment should wait until the model/orchestration contract is accepted.
