# ADR-0007: Model Orchestration Stage 01 Contract

Date: 2026-05-31
Status: Accepted
Source: Small-Model and Agent Orchestration Stage 01 report

## Decision

The model orchestration Stage 01 contract is accepted.

CAP/COP is the first demonstration disease_agent, not an architectural special case. disease_agent implementations expose disease_agent_code, agent_contract_version, supported_tasks, and supported_modalities.

The MVP model-service API draft includes GET /health, GET /models, GET /models/{model_version_id}, POST /validate-input, POST /infer, and optional POST /warmup.

ModelInferenceRequestV1 and ModelInferenceResponseV1 are accepted as the standard backend/model-service contract names.

Trace-bound requests must carry upstream trace_id. Downstream model-service or disease-agent code must not generate replacement trace IDs.

Supported version policies are approved_only, latest_approved, and pinned_version. Supported fallbacks are fallback_to_cpu and fallback_to_rule_baseline. no_silent_fallback is mandatory.

Accepted error taxonomy includes invalid_input, missing_required_input, unsupported_modality, model_not_found, model_version_not_approved, inference_timeout, resource_exhausted, dependency_unavailable, internal_error, and trace_id_missing.

Stage 01 serving is CPU-first, batch size 1, concurrency 1. GPU serving and NVIDIA Container Toolkit are deferred.
