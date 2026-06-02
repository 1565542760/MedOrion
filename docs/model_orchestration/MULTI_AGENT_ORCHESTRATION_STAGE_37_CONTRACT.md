# MedOrion Multi-Agent Orchestration Stage 37 Contract

Last updated: 2026-06-02 Asia/Shanghai
Owner thread: MedOrion multi-agent orchestration and decision routing
Scope: Stage 37 defines multi-agent orchestration contracts, scheduler boundaries, conflict handling, trace/evidence requirements, and interoperability profiles only. No business code, no database changes, no Alembic, no Nginx, no real model loading, no training, and no `.pth` artifact discovery.

## 0. Scope and Non-Goals

Stage 37 goals:
1. Define the unified multi-agent orchestration entry contract for single-agent, parallel-agent, serial-agent, triage-then-specialist, conditional, conflict-aware, and dynamic re-evaluation flows.
2. Define LLM scheduler responsibilities and limits.
3. Define agent selection rules using registry metadata and endpoint health.
4. Define conflict handling and doctor-confirmation requirements.
5. Define trace and evidence requirements for every orchestration run and step.
6. Define data structure contracts for later backend implementation without creating tables now.
7. Define a public interoperability profile based on common standards, while preserving MedOrion-specific governance rules.
8. Define how dynamic condition feedback triggers re-evaluation instead of real-time training.
9. Define Stage 38 backend orchestration skeleton as the next implementation step.

Stage 37 non-goals:
1. Do not implement business code.
2. Do not change database schema.
3. Do not execute Alembic.
4. Do not enable Nginx.
5. Do not expose public network services.
6. Do not load real `.pth`, `.pt`, `.onnx`, `.ckpt`, or `.safetensors` artifacts.
7. Do not train or automatically retrain models.
8. Do not implement production inference or production orchestration logic.
9. Do not let LLM replace doctor decision-making.

## 1. Goals

MedOrion needs multi-agent orchestration because a single disease task may require more than one specialist agent, a triage agent, a summarizer, or a conflict-aware aggregator.

This stage solves the following:
1. One orchestration run may coordinate multiple agents without hardcoding per-agent flow in the main backend.
2. The scheduler can select agents from registries rather than filesystem discovery.
3. The system can support parallel, serial, conditional, and triage-to-specialist patterns.
4. The system can rerun only the affected agents when patient state changes.
5. The system can explain how the final recommendation was assembled, including disagreements and uncertainty.

The orchestration layer is a coordinator, not a hidden decision authority.

## 2. Non Goals

1. No real model execution beyond stub/interoperability contract design.
2. No `.pth` artifact discovery by scanning or guessing.
3. No training.
4. No automatic real-time training.
5. No GPU enablement.
6. No public deployment.
7. No production database changes.
8. No hardcoded agent location in main backend business logic.
9. No silent fallback.
10. No bypass of model or agent approval gates.

## 3. Core Concepts

### 3.1 `orchestration_run`
A top-level orchestration session tied to one `trace_id`, one case, and one clinical reasoning episode.

### 3.2 `orchestration_step`
A single step within an orchestration run, such as triage, specialist invocation, conflict resolution, or LLM summarization.

### 3.3 `agent_invocation`
One trace-bound call to one agent endpoint or one selected agent version.

### 3.4 `llm_scheduler`
The component that reads registry metadata, selects eligible agents, decides call order, and builds the orchestration plan.

### 3.5 `conflict_aware_aggregation`
A synthesis mode that preserves agreements, disagreements, uncertainty, and doctor-confirmation needs.

### 3.6 `dynamic_reassessment`
A new orchestration run or partial re-run triggered by new patient data, changed clinical context, or new doctor input.

### 3.7 `public_interoperability_profile`
A compatibility layer using common external standards to describe API, capability, and healthcare references while keeping MedOrion-specific governance intact.

## 4. Unified Multi-Agent Orchestration Entry API Draft

Stage 37 proposes a unified orchestration entry surface, typically behind the gateway.

Suggested draft APIs:
1. `POST /api/v1/orchestration-runs`
2. `GET /api/v1/orchestration-runs/{orchestration_run_id}`
3. `GET /api/v1/orchestration-runs/{orchestration_run_id}/steps`
4. `POST /api/v1/orchestration-runs/{orchestration_run_id}/reassess`
5. `POST /api/v1/agent-gateway/infer`
6. `POST /api/v1/agent-gateway/validate-input`
7. `GET /api/v1/agent-registry`
8. `GET /api/v1/agent-registry/{agent_code}`

### 4.1 Supported orchestration modes

1. `single_agent`
2. `parallel_agents`
3. `serial_agents`
4. `triage_then_specialist`
5. `conditional_trigger`
6. `conflict_aware_summary`
7. `dynamic_re_evaluation`

### 4.2 Entry contract rule

1. The backend/orchestrator creates `trace_id`.
2. The orchestration run references that trace and never replaces it.
3. The entry contract may select one agent or many agents.
4. The entry contract must preserve every selection and invocation decision in trace.

## 5. LLM Scheduler Boundary

The LLM scheduler may do the following:
1. Read `agent_registry`, `agent_version`, `agent_endpoint`, `agent_capability`, and `model_registry` metadata.
2. Read approved capability summaries and contract versions.
3. Build a routing plan using disease, task, modality, approval, and endpoint health.
4. Decide orchestration order such as parallel, serial, triage, or conditional steps.
5. Produce a bounded explanation of why the selected agents were chosen.
6. Identify when more than one specialist is needed.
7. Decide when to ask the doctor for clarification instead of pretending certainty.

The LLM scheduler must not do the following:
1. It must not discover `.pth` or endpoint files by scanning folders.
2. It must not bypass approval or default-selection policy.
3. It must not silently choose an unapproved model or agent.
4. It must not replace doctor decision-making.
5. It must not generate or replace `trace_id`.
6. It must not auto-train or self-update.
7. It must not hardcode endpoint paths or model artifact paths.

Scheduler rule:
1. LLM can propose a plan.
2. Backend policy decides whether the plan is allowed.
3. Gateway and registry decide whether the planned endpoint and model are eligible.
4. Doctor remains final decision maker for clinical interpretation.

## 6. Agent Selection Rules

Agent selection must use explicit metadata, not implicit assumptions.

Required selection inputs:
1. `disease_agent_code`
2. `supported_diseases`
3. `supported_tasks`
4. `supported_modalities`
5. `contract_version`
6. endpoint health
7. approval state
8. default model version
9. requested task
10. runtime policy

### 6.1 Selection order

Recommended selection sequence:
1. Filter by disease scope.
2. Filter by task compatibility.
3. Filter by modality compatibility.
4. Filter by contract version compatibility.
5. Filter by endpoint status and health.
6. Filter by approval status and rollout state.
7. Resolve default or pinned model version according to policy.
8. Select endpoint(s) using weight and priority.
9. Emit `agent_selected` trace event.

### 6.2 Selection constraints

1. `supported_diseases` must match the clinical problem or disease family.
2. `supported_tasks` must match the requested task.
3. `supported_modalities` must cover the available inputs or requested inference mode.
4. `contract_version` must be compatible with the gateway contract.
5. Unhealthy, disabled, or incompatible endpoints must not be selected.
6. Approved/default/shadow/canary policy must be respected.

### 6.3 Default and approval linkage

1. Agent selection may reference `default_model_id` and `default_model_version_id` from the agent registry.
2. Model version selection is still governed by model registry policy.
3. If no eligible default exists, the system must surface the issue explicitly rather than silently choosing another version.

## 7. Multi-Agent Conflict Handling

Multi-agent results may agree, disagree, or remain uncertain.

Required conflict outcomes:
1. `supports`
2. `contradicts`
3. `uncertain`
4. `needs_doctor_confirmation`

### 7.1 Conflict modes

1. **Supportive consensus**: multiple agents align.
2. **Direct contradiction**: agents produce opposite conclusions or materially conflicting risk signals.
3. **Uncertain overlap**: agents do not have enough evidence to confidently agree or disagree.
4. **Doctor confirmation required**: uncertainty or conflict is clinically important enough that the system must ask the doctor.

### 7.2 Conflict resolution rule

1. The orchestrator must not hide disagreements.
2. Conflict must be stored in trace and evidence.
3. If conflict changes the recommendation, the recommendation node must reference the conflict record.
4. If conflict remains unresolved, the output must show uncertainty and doctor-action next steps.
5. The LLM summary may explain conflict, but it cannot erase conflict.

### 7.3 Conflict-aware aggregation behavior

1. Preserve each specialist result.
2. Mark the dominant reasoning path.
3. Mark contradictory agent outputs explicitly.
4. Convert unresolved conflict into doctor-facing confirmation or review items.
5. Never silently collapse multiple viewpoints into a single hidden score.

## 8. Dynamic Re-Evaluation

Dynamic patient feedback means new information can trigger a new orchestration run or a partial re-run.

Trigger sources:
1. New CT, MRI, lab, or EMR data.
2. Doctor correction or new observation.
3. Quality review finding.
4. Missing-value resolution.
5. Case state change.

Re-evaluation rule:
1. Re-evaluation is a new reasoning event, not training.
2. Only affected agents should be re-invoked when possible.
3. Unaffected agents may be reused from prior trace if policy allows and the evidence remains valid.
4. The run must record what changed, what was reused, and what was recomputed.
5. No automatic model retraining is allowed.

## 9. Failure, Timeout, Retry, and Fallback

Failure types:
1. agent unavailable
2. endpoint unavailable
3. validation failure
4. timeout
5. contract mismatch
6. capability mismatch
7. approval failure
8. partial orchestration failure
9. conflict resolution failure

### 9.1 Retry policy

1. Retryable errors may be retried with the same `trace_id` and the same orchestration run context.
2. Retries must preserve idempotency.
3. Retry reason must be recorded.
4. Retry limit should be bounded by policy.

### 9.2 Fallback policy

1. Fallback is allowed only if policy explicitly permits it.
2. Fallback may be to another endpoint, another approved agent version, or another allowed orchestration path.
3. Fallback must never be silent.
4. Fallback reason must be emitted to trace and evidence.
5. If fallback is not possible, the failure must be surfaced to the doctor-facing workflow.

### 9.3 `no_silent_fallback`

Mandatory rule:
1. Any fallback, endpoint swap, version swap, or agent swap must be visible in trace.
2. Hidden substitution is prohibited.

## 10. Trace / Evidence Requirements

Every orchestration run must be trace-bound.

Required fields:
1. `trace_id`
2. `orchestration_run_id`
3. `orchestration_step_id`
4. `agent_code`
5. `agent_version`
6. `endpoint_id`
7. `endpoint_url`
8. `model_version_id`
9. `agent_invocation_id`
10. `fallback_reason` nullable
11. `runtime_stub_or_real_model` flag
12. `selection_reason`
13. `approval_status`

Required trace events:
1. `agent_selected`
2. `agent_invoked`
3. `agent_result_received`
4. `agent_unavailable`
5. `fallback_used`
6. `orchestration_run_started`
7. `orchestration_step_started`
8. `orchestration_step_completed`
9. `orchestration_run_completed`

Trace rule:
1. The orchestration run must be traceable end-to-end.
2. Every step must be attributable to an agent or the scheduler.
3. Evidence must reference the exact version and endpoint used.
4. Stub mode and real mode must never be ambiguous.

## 11. Suggested Data Structures

This stage only defines the contract intent. No tables are created now.

Suggested future entities:
1. `orchestration_runs`
2. `orchestration_steps`
3. `agent_invocations`
4. `orchestration_conflicts`
5. `llm_summaries`

### 11.1 Suggested payload intent

`orchestration_runs`:
1. `trace_id`
2. `case_id`
3. `patient_id` nullable
4. `run_mode`
5. `status`
6. `created_at`
7. `completed_at`

`orchestration_steps`:
1. `orchestration_run_id`
2. `step_type`
3. `step_order`
4. `selected_agent_code`
5. `step_status`
6. `input_ref`
7. `output_ref`

`agent_invocations`:
1. `orchestration_run_id`
2. `orchestration_step_id`
3. `agent_code`
4. `agent_version`
5. `endpoint_id`
6. `model_version_id`
7. `agent_invocation_id`
8. `status`
9. `latency_ms`

`orchestration_conflicts`:
1. `orchestration_run_id`
2. `conflict_type`
3. `conflicting_agent_codes`
4. `resolution_status`
5. `doctor_confirmation_required`

`llm_summaries`:
1. `orchestration_run_id`
2. `summary_type`
3. `prompt_template_version`
4. `summary_ref`
5. `uncertainty_summary`

## 12. Boundary With Other Threads

### 12.1 Model registry boundary

1. Model registry defines version lifecycle and artifact governance.
2. Multi-agent orchestration reads model registry, but does not own model artifact registration.
3. Model registry controls approved/default/shadow/canary state.

### 12.2 Agent registry boundary

1. Agent registry defines agents, endpoints, capabilities, and routing eligibility.
2. Multi-agent orchestration reads agent registry and endpoint health.
3. Agent registry controls addressability and capability matching.

### 12.3 Traceability boundary

1. Traceability owns trace IDs, event taxonomy, and evidence graph rules.
2. Multi-agent orchestration must emit trace-compatible records.
3. Orchestration must not invent a parallel trace system.

### 12.4 Quality review boundary

1. Quality review evaluates problematic outputs, conflicts, or failures.
2. Multi-agent orchestration links to quality review records but does not decide governance closure alone.

### 12.5 Doctor feedback boundary

1. Doctor feedback is a signal for refinement and reassessment.
2. It is not automatic training.
3. It may influence future approval, rollback, or promotion decisions.

## 13. Public Interoperability Profile

MedOrion may use standard interoperability protocols as an adapter layer.

### 13.1 Supported public descriptions

1. `OpenAPI 3.1` for HTTP API and request/response schema description.
2. `JSON Schema` for payload contracts and validation.
3. `Agent Card` or `A2A-like` capability description for agent metadata, endpoint description, and task lifecycle.
4. `FHIR` reference fields for medical record and clinical data references.
5. `DICOMweb` reference fields for imaging asset references.
6. `Model Card` or `MLflow-like metadata` for model metadata and evaluation summaries.

### 13.2 Interoperability boundary rule

These standards are only adapter and interoperability layers.

They must not overwrite MedOrion rules for:
1. `trace_id`
2. evidence chain
3. model approval
4. doctor-assistance positioning
5. safety audit logging
6. `no_silent_fallback`
7. registry-based capability resolution

### 13.3 Implementation meaning

1. Public APIs can be described using OpenAPI 3.1.
2. Agent capability metadata can be expressed in an Agent Card-like document.
3. Medical data references can use FHIR or DICOMweb reference URIs where appropriate.
4. Model metadata can be stored in a Model Card-like or MLflow-like shape.
5. MedOrion-specific governance remains authoritative.

## 14. Future Standard Entry Points Not Implemented Yet

The following endpoints or files may be exposed later, but are not implemented in Stage 37:
1. `/openapi.json`
2. `/.well-known/agent-card.json`
3. `/health`

Rule:
1. They are future interoperability surfaces only.
2. They must not replace MedOrion trace, evidence, approval, or fallback rules.

## 15. Stage 38 Recommendation

Stage 38 should implement the backend orchestration skeleton.

What Stage 38 should focus on:
1. orchestration run creation
2. orchestration step recording
3. agent selection adapter
4. conflict object recording
5. LLM summary placeholder
6. trace-bound orchestration response shapes

What Stage 38 should not do:
1. no real model loading
2. no training
3. no production deployment
4. no silent fallback
5. no public exposure

## 16. Main-Controller Writeback Summary

1. Stage 37 multi-agent orchestration contract is created.
2. The unified orchestration entry supports single agent, parallel, serial, triage-then-specialist, conditional, conflict-aware summary, and dynamic re-evaluation.
3. LLM scheduler is limited to reading registry/capability metadata and planning orchestration; it cannot discover files, bypass approvals, or replace doctors.
4. Agent selection must use disease scope, tasks, modalities, contract version, endpoint health, approval, and default model version.
5. Multi-agent conflicts must be preserved as support/contradiction/uncertainty/doctor-confirmation-needed, not hidden.
6. Trace and evidence must bind every orchestration run and step with agent and endpoint identifiers, model version, invocation ID, and run/step IDs.
7. Public interoperability standards such as OpenAPI 3.1, JSON Schema, Agent Card-like metadata, FHIR, DICOMweb, and Model Card/MLflow-like metadata are allowed only as adapters, not as replacements for MedOrion governance.
8. Stage 38 backend orchestration skeleton is the recommended next step.
