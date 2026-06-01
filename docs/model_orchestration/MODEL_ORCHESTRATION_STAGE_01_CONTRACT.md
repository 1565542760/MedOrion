# MedOrion Model Orchestration Stage 01 Contract

Last updated: 2026-05-31 Asia/Shanghai
Owner thread: MedOrion small-model and agent orchestration
Scope: Stage 01 defines model-service, disease-agent orchestration, model selection/fallback, error/retry, and trace/evidence emission contracts only. No full inference implementation, no training, and no model-service container startup.

## 0. Scope and Non-Goals

Stage 01 goals:
1. Define CAP/COP disease-agent responsibility boundary and extensible disease-agent interface.
2. Define model-service MVP HTTP API draft.
3. Define standard model inference request/response schemas.
4. Define CAP/COP Stage 01 output contract shape.
5. Define model version selection and fallback policy with mandatory traceability.
6. Define error code, timeout, and retry policy.
7. Define required trace_events and evidence graph emission rules.
8. Define CPU-first serving assumptions for current hardware constraints.
9. Define cross-thread integration requirements for backend, traceability, deployment, and frontend.

Stage 01 non-goals:
1. Do not train CAP/COP models or any other model.
2. Do not implement full inference service logic.
3. Do not start model-service container.
4. Do not introduce automatic real-time training.
5. Do not allow model outputs to replace doctor judgement.

## 1. CAP/COP Disease-Agent Responsibility Boundary

### 1.1 Positioning

1. `cap_cop_agent` is the first demonstration `disease_agent`, not a special-case architecture fork.
2. Future disease agents must reuse the same contract and lifecycle.
3. The large-model orchestrator remains the planner, explainer, and recommendation composer.

### 1.2 Generic Disease-Agent Interface (for multi-disease extension)

Contract identity:
1. `disease_agent_code`: string, for example `cap_cop`.
2. `agent_contract_version`: string, for example `v1`.
3. `supported_tasks`: array, for example `classification`, `risk_scoring`, `rule_baseline_check`.
4. `supported_modalities`: array, for example `ct_image`, `clinical_table`, `emr_text`.

Core operations:
1. `validate_case_inputs(trace_bound_request)`
2. `build_model_invocation_plan(trace_bound_request)`
3. `execute_model_invocations(trace_bound_request, plan)`
4. `merge_model_and_rule_outputs(trace_bound_request, outputs)`
5. `emit_trace_and_evidence(trace_bound_request, outputs, decisions)`
6. `return_structured_agent_result(trace_bound_request)`

### 1.3 Disease-Agent Must Do

1. Enforce disease-specific required-input checks and missing-value policy handoff.
2. Select model-service invocation strategy according to policy and modality availability.
3. Normalize small-model outputs into standard schema.
4. Emit model-related trace events and evidence emissions.
5. Attach limitations, uncertainty, and doctor-review actions.

### 1.4 Disease-Agent Must Not Do

1. Must not generate replacement `trace_id` when request already carries one.
2. Must not bypass doctor-first missing-value workflow.
3. Must not output doctor-final diagnosis statements.
4. Must not perform online or automatic retraining.
5. Must not hide fallback behavior from trace.

### 1.5 Orchestrator vs Disease-Agent Split

Orchestrator:
1. Route to disease agents.
2. Decide data sufficiency and doctor question workflow entry.
3. Compose final explanation and recommendation package for doctor review.
4. Emit `orchestrator_decision` events.

Disease-agent:
1. Execute disease-specific model/rule workflow.
2. Return structured machine judgement package.
3. Emit `model_selected`, `model_invoked`, `model_result_received` events.

Small models:
1. Produce scoped disease/task outputs only.
2. Provide confidence, uncertainty, and limitations metadata.

## 2. model-service MVP HTTP API Draft

Base path suggestion: `/api/v1/model-service`

### 2.1 `GET /health`

Purpose:
1. Liveness/readiness probe for model-service process.

Response highlights:
1. `status`: `ok|degraded|unavailable`
2. `service_version`
3. `cpu_mode`: boolean
4. `registered_model_count`

### 2.2 `GET /models`

Purpose:
1. List registered models visible to this service.

Query parameters:
1. `disease_agent` optional
2. `task_type` optional
3. `approval_state` optional

### 2.3 `GET /models/{model_version_id}`

Purpose:
1. Resolve one model version metadata and contract info.

### 2.4 `POST /validate-input`

Purpose:
1. Validate request structure and modality readiness before inference call.

### 2.5 `POST /infer`

Purpose:
1. Execute one trace-bound inference invocation.

Rules:
1. `trace_id` required.
2. `idempotency_key` required.
3. Must reject missing trace-bound requests.

### 2.6 Optional `POST /warmup`

Purpose:
1. Warm CPU model assets and preprocessors.

Stage 01 status:
1. Optional endpoint, not required to be implemented now.

## 3. Standard Model Inference Request Schema

Schema name: `ModelInferenceRequestV1`

```json
{
  "trace_id": "trc_01J0...",
  "inference_task_id": "inf_01J0...",
  "case_id": "case_...",
  "patient_id": null,
  "disease_agent": "cap_cop",
  "requested_task": "classification",
  "model_version_policy": {
    "mode": "latest_approved",
    "pinned_version": null,
    "allow_fallback_to_cpu": true,
    "allow_fallback_to_rule_baseline": true,
    "no_silent_fallback": true
  },
  "inputs": {
    "image_inputs": [
      {
        "input_id": "img_...",
        "modality": "ct_image",
        "object_ref": {
          "bucket": "medorion-inputs",
          "object_key": "cases/.../ct.nii.gz",
          "checksum": "sha256:..."
        }
      }
    ],
    "tabular_inputs": [
      {
        "input_id": "tab_...",
        "schema_version": "cap_cop_tabular_v1",
        "values_ref": "clinical_table_row_id"
      }
    ],
    "text_inputs": [
      {
        "input_id": "txt_...",
        "modality": "emr_text",
        "document_ref": "emr_document_id"
      }
    ]
  },
  "clinical_context_refs": {
    "clinical_table_ids": ["ctab_..."],
    "lab_result_ids": ["lab_..."],
    "emr_document_ids": ["emr_..."]
  },
  "modality_refs": {
    "available_modalities": ["ct_image", "clinical_table", "emr_text"],
    "required_modalities_for_task": ["ct_image", "clinical_table"]
  },
  "missing_value_context": {
    "missing_fields": [
      {
        "field_path": "clinical_table.crp",
        "status": "pending",
        "doctor_question_id": "mvq_..."
      }
    ],
    "defaulted_fields": []
  },
  "runtime_options": {
    "timeout_ms": 15000,
    "priority": "normal",
    "cpu_only": true,
    "batch_size": 1
  },
  "idempotency_key": "infer-case_...-attempt_1"
}
```

Required fields:
1. `trace_id`
2. `inference_task_id`
3. `case_id`
4. `patient_id` nullable
5. `disease_agent`
6. `requested_task`
7. `model_version_policy`
8. `inputs`
9. `clinical_context_refs`
10. `modality_refs`
11. `missing_value_context`
12. `runtime_options`
13. `idempotency_key`

Trace rule:
1. If `trace_id` missing, return `trace_id_missing` error.

## 4. Standard Model Inference Response Schema

Schema name: `ModelInferenceResponseV1`

```json
{
  "trace_id": "trc_01J0...",
  "inference_task_id": "inf_01J0...",
  "model_invocation_id": "inv_01J0...",
  "model_id": "capcop_multimodal_classifier",
  "model_version_id": "capcop_mm_v2026_05_31",
  "disease_agent": "cap_cop",
  "task_type": "classification",
  "status": "succeeded",
  "outputs": {
    "candidate_label": "CAP",
    "classification": {
      "label_space": ["CAP", "COP"],
      "predicted_label": "CAP",
      "probability": {
        "CAP": 0.74,
        "COP": 0.26
      }
    },
    "risk_score": null
  },
  "confidence": {
    "score": 0.74,
    "calibrated": false,
    "method": "model_native"
  },
  "uncertainty": {
    "level": "moderate",
    "reasons": ["missing_lab_crp", "single_modality_only"],
    "ood_flag": false
  },
  "limitations": [
    "MVP model output is decision support only",
    "Defaulted or missing clinical fields reduce reliability"
  ],
  "evidence_nodes_to_create": [],
  "evidence_edges_to_create": [],
  "trace_events_to_emit": [],
  "error": null
}
```

Required fields:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `model_id`
5. `model_version_id`
6. `disease_agent`
7. `task_type`
8. `status`
9. `outputs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `evidence_nodes_to_create`
14. `evidence_edges_to_create`
15. `trace_events_to_emit`
16. `error` nullable

Status values:
1. `succeeded`
2. `failed`
3. `partial`

## 5. CAP/COP Stage 01 Output Contract

Schema name: `CapCopAgentOutputV1`

Required output fields:
1. `classification`
2. `risk_score` nullable
3. `probability`
4. `candidate_label`
5. `confidence`
6. `uncertainty`
7. `input_quality_flags`
8. `missing_value_impact`
9. `model_limitations`
10. `recommended_next_actions_for_doctor_review`

Example shape:

```json
{
  "classification": {
    "predicted_label": "COP",
    "label_space": ["CAP", "COP"]
  },
  "risk_score": {
    "name": "cop_likelihood",
    "value": 0.81,
    "scale": "0_to_1"
  },
  "probability": {
    "CAP": 0.19,
    "COP": 0.81
  },
  "candidate_label": "COP",
  "confidence": {
    "score": 0.81,
    "level": "high"
  },
  "uncertainty": {
    "level": "low",
    "reasons": []
  },
  "input_quality_flags": [
    "ct_slice_thickness_outside_recommended_range"
  ],
  "missing_value_impact": {
    "has_missing": true,
    "defaulted_fields": ["clinical_table.smoking_status"],
    "impact_level": "moderate"
  },
  "model_limitations": [
    "For physician support only",
    "Not a standalone diagnosis"
  ],
  "recommended_next_actions_for_doctor_review": [
    "Review CT pattern consistency with model output",
    "Confirm smoking_status to reduce uncertainty",
    "Cross-check with latest lab and EMR findings"
  ]
}
```

## 6. Model Version Selection and Fallback Policy

### 6.1 Version policy modes

1. `approved_only`: only versions with approved status allowed.
2. `latest_approved`: resolve latest approved version by disease/task/modality.
3. `pinned_version`: use explicit `model_version_id`.

### 6.2 Fallback controls

1. `fallback_to_cpu`: allowed in Stage 01 by default.
2. `fallback_to_rule_baseline`: allowed only when configured by disease-agent policy.
3. `no_silent_fallback`: mandatory true in Stage 01 recommendation workflows.

### 6.3 Hard rule

1. Any fallback must emit trace events and evidence entries.
2. Silent fallback is prohibited.

## 7. Error Code, Timeout, and Retry Policy

### 7.1 Error taxonomy

Required error codes:
1. `invalid_input`
2. `missing_required_input`
3. `unsupported_modality`
4. `model_not_found`
5. `model_version_not_approved`
6. `inference_timeout`
7. `resource_exhausted`
8. `dependency_unavailable`
9. `internal_error`
10. `trace_id_missing`

Error object shape:

```json
{
  "code": "inference_timeout",
  "message": "Model invocation exceeded timeout",
  "retryable": true,
  "suggested_action": "retry_with_same_trace_and_idempotency_key",
  "details": {
    "timeout_ms": 15000,
    "model_version_id": "capcop_mm_v2026_05_31"
  }
}
```

### 7.2 Timeout policy

1. Default `POST /infer` timeout suggestion: `15000 ms` CPU-first baseline.
2. Per-task override allowed via `runtime_options.timeout_ms` within backend guardrails.

### 7.3 Retry policy

Retryable by default:
1. `inference_timeout`
2. `resource_exhausted`
3. `dependency_unavailable`

Non-retryable by default:
1. `invalid_input`
2. `missing_required_input`
3. `unsupported_modality`
4. `model_not_found`
5. `model_version_not_approved`
6. `trace_id_missing`

Retry limits:
1. Max retries suggestion: `2`.
2. Backoff: exponential (`500ms`, `1500ms`).
3. Same `trace_id` and `idempotency_key` must be preserved for retries of the same task attempt chain.

## 8. Required trace_events Emission

Stage 01 must align to frozen taxonomy in `TRACEABILITY_STAGE_01_CONTRACT.md`.

Required event types:
1. `model_selected`
2. `model_invoked`
3. `model_result_received`
4. `orchestrator_decision`

### 8.1 Required payload fields per event

`model_selected`:
1. `trace_id`
2. `inference_task_id`
3. `disease_agent`
4. `requested_task`
5. `model_id`
6. `model_version_id`
7. `selection_reason`
8. `model_version_policy_mode`

`model_invoked`:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `model_id`
5. `model_version_id`
6. `input_refs`
7. `runtime_options`

`model_result_received`:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `status`
5. `output_ref_or_inline_summary`
6. `confidence_summary`
7. `uncertainty_summary`
8. `error_code` nullable

`orchestrator_decision`:
1. `trace_id`
2. `inference_task_id`
3. `decision_type`
4. `decision_summary`
5. `inputs_considered`
6. `selected_agent_or_action`

### 8.2 Trace propagation rule

1. If request is trace-bound, model-service and disease-agent must use upstream `trace_id`.
2. Replacement `trace_id` generation is forbidden.

## 9. Evidence Nodes and Edges Emission Rules

### 9.1 Node emission

Required node types in this contract:
1. `model_output` node for every successful or partial model invocation.
2. `rule_result` node when fallback rule baseline or deterministic checks are used.
3. `image_finding` node for image-derived intermediate findings when applicable.
4. `clinical_feature` node for table/lab/text derived structured features.
5. `recommendation` node is created by orchestrator/backend recommendation layer, and must reference disease-agent outputs.

### 9.2 Edge usage rules

1. `derived_from`: use from `input` or `clinical_feature` to `model_output`.
2. `supports`: use from `model_output` or `rule_result` to `recommendation` when evidence aligns.
3. `contradicts`: use when evidence conflicts with candidate recommendation.
4. `references`: use for prior trace, policy, template, or external reference linkage.
5. `missing_value_defaulted`: use from missing-value decision node to affected derived/model/recommendation nodes when default strategy affected output.

### 9.3 Emission discipline

1. Emitted nodes/edges must be reference-oriented, not raw heavy payload dumps.
2. Recommendation must retain visible linkage to upstream `model_output` and missing-value effects.

## 10. CPU-First Serving Assumptions

Stage 01 serving assumptions:
1. Current hardware constraint: RTX 3050 Laptop GPU with 4GB VRAM.
2. Default inference runtime: CPU-first.
3. Default batch size: `1`.
4. Default service concurrency: `1`.
5. GPU serving and NVIDIA Container Toolkit integration are deferred.
6. Prefer quantized or lightweight model variants for MVP reliability.
7. Any future GPU enablement must be explicit config change and traceable in deployment records.

## 11. Cross-Thread Interface Requirements

### 11.1 Backend thread must consume

1. `ModelInferenceRequestV1` and `ModelInferenceResponseV1` payload contracts.
2. Disease-agent interface boundary and model version policy fields.
3. Error taxonomy and retryability metadata.
4. Required trace event emission payload minimums.

### 11.2 Traceability and QC thread must validate

1. Event taxonomy compliance for `model_selected`, `model_invoked`, `model_result_received`, `orchestrator_decision`.
2. Evidence node/edge type correctness and linkage completeness.
3. `no_silent_fallback` enforcement through observed events.
4. Missing-value default impact visibility on evidence graph.

### 11.3 Deployment and MLOps thread must prepare (later stage)

1. `model-service` Dockerfile skeleton and runtime env contract.
2. Env keys for `MODEL_SERVICE_CPU_ONLY`, `MODEL_SERVICE_MAX_CONCURRENCY`, `MODEL_SERVICE_TIMEOUT_MS`.
3. Healthcheck contract compatibility with `GET /health`.
4. Versioned model mount convention and approval metadata sync path.

### 11.4 Frontend doctor workstation must display

1. `candidate_label`, `probability`, `confidence`, `uncertainty`.
2. `input_quality_flags` and `missing_value_impact`.
3. `model_limitations` and doctor-review next actions.
4. `trace_id` and evidence references for audit drill-down.
5. Explicit assistive disclaimer that output does not replace doctor diagnosis.

## 12. Explicit Stage 01 Do-Not-Do List

1. Do not train models.
2. Do not implement full inference logic.
3. Do not start model-service container.
4. Do not add automatic real-time training.
5. Do not allow model output to replace doctor clinical judgement.

## 13. Main-Controller Writeback Summary

1. Stage 01 model orchestration contract is now defined for disease-agent boundary, model-service API draft, request/response schema, fallback policy, error taxonomy, trace emission, and evidence emission.
2. CAP/COP is explicitly constrained as the first disease-agent only; contract is reusable for future disease agents.
3. Trace-bound propagation is strict: downstream services must reuse upstream `trace_id` and must reject missing trace requests.
4. No-silent-fallback policy is frozen for recommendation workflows; all fallback behavior must emit trace events and evidence links.
5. CPU-first assumptions are frozen for current 4GB GPU environment; GPU inference enablement is deferred and not part of Stage 01.
