# MedOrion Agent Registry Stage 35 Contract

Last updated: 2026-06-02 Asia/Shanghai
Owner thread: MedOrion agent registry and gateway architecture
Scope: Stage 35 defines agent registry, agent version lifecycle, endpoint metadata, capability model, and unified agent gateway contracts only. No source code changes, no database migrations, no real `.pth` loading, no training, and no public deployment.

## 0. Scope and Non-Goals

Stage 35 goals:
1. Support multi-disease, multi-agent, multi-endpoint topology.
2. Support distributed deployment and endpoint mobility.
3. Support endpoint URL and health URL changes without hardcoding agent addresses in the main backend.
4. Support capability and contract version changes over time.
5. Support one unified entry point for one or many agent calls.
6. Support future model upgrade integration through registry metadata rather than filesystem discovery.
7. Keep trace/evidence consistent with the existing MedOrion traceability contract.

Stage 35 non-goals:
1. Do not load real `.pth` artifacts.
2. Do not train models.
3. Do not automatically retrain in real time.
4. Do not enable GPU serving.
5. Do not implement real multi-agent reasoning.
6. Do not open public network exposure.
7. Do not hardcode agent addresses in core backend business logic.
8. Do not execute database migrations.
9. Do not modify source code in this stage.

## 1. Goals

MedOrion now needs an Agent Registry because the platform has moved beyond a single stub endpoint.

The registry and gateway layer solve these problems:
1. Many disease-specific intelligent agents must be registered and discovered in a consistent way.
2. Intelligent agents may be deployed in distributed form, with separate endpoints and health probes.
3. Agent location, endpoint URL, and capability may change without forcing the main backend to hardcode addresses.
4. The system must support a unified invocation interface whether one agent or multiple agents are involved.
5. The system must keep the relationship between agent calls, model versions, trace, evidence, and doctor feedback visible.

This registry is a control plane for discovery, routing, capability, and lifecycle, not a file browser and not a model executor.

## 2. Non Goals

1. No real `.pth` loading.
2. No training.
3. No automatic real-time training.
4. No GPU enablement.
5. No real multi-agent inference.
6. No production deployment.
7. No public exposure.
8. No database migration execution.
9. No source code changes in this stage.
10. No silent endpoint discovery from filesystem scanning.

## 3. Core Concepts

### 3.1 `agent_registry`
Catalog of agents that MedOrion can route to. It answers: which agents exist, what they do, what disease scope they cover, and which version is considered current or default.

### 3.2 `agent_version`
A versioned definition of an agent contract. It captures contract version, input/output schema version, supported capability set, and compatibility expectations.

### 3.3 `agent_endpoint`
A concrete runtime instance for an agent version or agent family. It has endpoint URL, health URL, region, resource profile, and rollout status.

### 3.4 `agent_capability`
A structured description of what a given agent can do: disease, task, modality, input schema, output schema, constraints, and limitations.

### 3.5 `agent_gateway`
The unified entry point used by backend/orchestrator to invoke one or many agents without hardcoding each agent endpoint.

### 3.6 `agent_invocation`
A trace-bound call to one selected agent endpoint or one routed agent version.

### 3.7 `orchestration_run`
One top-level orchestration session that may include one or many agent invocations.

### 3.8 `orchestration_step`
A single step inside an orchestration run, for example triage, specialist agent call, conflict resolution, or LLM summary.

### 3.9 `disease_agent_code`
Stable code for a disease-specific agent family, for example `cap_cop`.

### 3.10 `contract_version`
Version of the agent contract or gateway contract that defines request/response compatibility.

### 3.11 `supported_diseases`
Disease labels or disease scopes that an agent can support.

### 3.12 `supported_tasks`
Task labels that the agent can perform, such as classification, detection, segmentation, risk scoring, triage, or explanation helper.

### 3.13 `supported_modalities`
Input modalities that the agent can consume, such as CT, MRI, clinical table, EMR text, lab features, or future wearable data.

## 4. Agent Registry Metadata

Every agent registration record must include the following fields:

1. `agent_code`
2. `agent_name`
3. `agent_type`
4. `disease_scope`
5. `supported_tasks`
6. `supported_modalities`
7. `contract_version`
8. `input_schema_version`
9. `output_schema_version`
10. `status`
11. `owner_team`
12. `default_model_id`
13. `default_model_version_id`
14. `created_at`
15. `updated_at`

### 4.1 Field notes

`agent_code`:
1. Immutable logical identifier.
2. Used by orchestrator and backend policy.

`agent_name`:
1. Human-readable name.
2. Used for admin UI and audit readability.

`agent_type`:
1. For example `single_agent`, `triage_agent`, `specialist_agent`, `aggregator_agent`.
2. Useful for routing and UI classification.

`disease_scope`:
1. The disease area or disease family covered by the agent.
2. Must not be inferred from the name alone.

`supported_tasks`:
1. Must be explicit.
2. Must align with contract and model registry capabilities.

`supported_modalities`:
1. Must be explicit.
2. Must align with what the agent and its downstream models can consume.

`contract_version`:
1. Defines compatibility with the unified agent gateway and model registry integration.

`input_schema_version` and `output_schema_version`:
1. Bind agent behavior to concrete schema versions.
2. Required for backward compatibility.

`status`:
1. Registry lifecycle state for the agent itself.
2. Used to decide whether the agent can receive routing traffic.

`owner_team`:
1. Accountability metadata.

`default_model_id` and `default_model_version_id`:
1. Reference the default model selection used by the agent when policy allows.
2. These are registry references, not filesystem paths.

`created_at` and `updated_at`:
1. Audit timestamps for governance.

## 5. Agent Endpoint Metadata

Every endpoint registration record must include the following fields:

1. `endpoint_id`
2. `agent_code`
3. `endpoint_url`
4. `health_url`
5. `region`
6. `runtime`
7. `resource_type`
8. `status`
9. `weight`
10. `priority`
11. `last_health_check_at`
12. `failure_count`
13. `timeout_ms`

### 5.1 Endpoint rules

`endpoint_id`:
1. Immutable record ID.
2. Used in trace and orchestration logs.

`agent_code`:
1. Links endpoint to agent registry record.

`endpoint_url`:
1. Runtime invocation target.
2. Must not be hardcoded into main backend business logic.

`health_url`:
1. Used for readiness and health checks.
2. Can differ from invocation URL if needed.

`region`:
1. Useful for distributed deployment and failover planning.

`runtime`:
1. For example `python-fastapi`, `onnxruntime`, `grpc-service`, `stub-fastapi`, `container`.

`resource_type`:
1. Declares compute shape such as `cpu-small`, `cpu-medium`, `gpu-small`, or future types.

`status`:
1. For example `active`, `standby`, `degraded`, `disabled`, `deprecated`.

`weight`:
1. Used for routing preference or canary distribution.
2. Should be explicit, not implicit.

`priority`:
1. Used for ordering when multiple endpoints are eligible.

`last_health_check_at`:
1. Useful for routing freshness.

`failure_count`:
1. Used for circuit-breaking and failover decisions.

`timeout_ms`:
1. Endpoint-specific timeout budget.

## 6. Capability Model

An agent capability record must express:
1. disease
2. task
3. modality
4. input schema
5. output schema
6. constraints
7. limitations
8. required model versions
9. optional modalities

### 6.1 Capability representation

A capability should answer:
1. Which disease or disease family this capability serves.
2. Which task the capability performs.
3. Which modalities are required.
4. Which input schema version is expected.
5. Which output schema version is produced.
6. Which model version(s) are required or preferred.
7. Which optional modalities can improve the result.
8. What limitations apply.

### 6.2 Capability contract rule

1. The orchestrator must reason in terms of capability, not file paths.
2. The LLM must only see a capability summary and not local artifact path details.
3. A capability that is not contract-compatible must be treated as unavailable even if the endpoint exists.

## 7. Unified Agent Gateway

The gateway is the only standard call surface that the backend should use for agent invocation in Stage 35 design.

Suggested draft APIs:
1. `POST /api/v1/agent-gateway/infer`
2. `POST /api/v1/agent-gateway/validate-input`
3. `GET /api/v1/agent-registry`
4. `GET /api/v1/agent-registry/{agent_code}`
5. `POST /api/v1/orchestration-runs`

### 7.1 Gateway rule

1. Backend calls gateway only.
2. Backend must not hardcode agent endpoint addresses in business logic.
3. Gateway chooses active endpoint according to registry metadata and policy.
4. Gateway may route to one or many agents.
5. Gateway remains the policy boundary between backend and agent endpoints.

### 7.2 Gateway responsibilities

1. Validate input compatibility.
2. Load agent registry metadata.
3. Select eligible endpoint(s).
4. Invoke one or many agents.
5. Record `agent_invocation` and `orchestration_run`.
6. Emit trace/evidence-related events.
7. Surface fallback or unavailability explicitly.

## 8. Single-Agent Invocation Flow

Single-agent flow:
1. Backend creates `trace_id`.
2. Gateway looks up agent registry.
3. Gateway selects active endpoint.
4. Gateway invokes agent endpoint.
5. Gateway records `agent_invocation`.
6. Gateway forwards result to backend/orchestrator.
7. Trace and evidence are emitted.

Required properties:
1. `trace_id` must be preserved.
2. Selected `agent_code` and `agent_version` must be recorded.
3. `endpoint_id` and `endpoint_url` must be recorded.
4. Result must be trace-bound and audit-visible.

## 9. Multi-Agent Invocation Flow

A single orchestration run may invoke multiple agents.

Supported patterns:
1. `parallel`
2. `serial`
3. `conditional`
4. `triage_then_specialist`
5. `conflict_aware_aggregation`
6. `llm_summary_explanation`

Flow rule:
1. The doctor remains the final decision maker.
2. LLM may summarize and reconcile, but not silently override specialist output.
3. Multi-agent orchestration must preserve every agent invocation in trace.
4. Conflict between agents must be visible, not hidden.

## 10. Endpoint Migration

Endpoint location changes must not require main backend code changes.

Migration rule:
1. Update `endpoint_url` and/or `health_url` in registry.
2. Keep `agent_code` and contract intact unless capability truly changed.
3. Gateway reads the new endpoint on next selection.
4. Old endpoint can be marked `deprecated` or `disabled`.
5. All invocation records must retain the actual endpoint used.

Migration requirements:
1. No hardcoded addresses in core business logic.
2. No silent switchover.
3. No trace loss during endpoint movement.

## 11. Capability Change

Capability changes may require contract version upgrade.

Change rule:
1. If input schema changes, bump `contract_version` and relevant schema versions.
2. If supported task changes, update capability metadata explicitly.
3. If modality support changes, re-evaluate compatibility.
4. If capability is no longer compatible, the gateway must not silently call it.
5. Compatibility check must happen before call selection.

Compatibility considerations:
1. `contract_version` compatibility.
2. `input_schema_version` compatibility.
3. `output_schema_version` compatibility.
4. `supported_tasks` compatibility.
5. `supported_modalities` compatibility.

## 12. Model Upgrade Integration

Agents do not directly decide their default model in an uncontrolled way.

Integration rule:
1. Gateway or backend strategy layer reads `model_registry` and `model_versions`.
2. `latest_approved`, `default`, `shadow`, and `canary` policy states are resolved by registry policy.
3. `trace` must record `model_version_id` for every call.
4. Silent fallback is prohibited.
5. Agent registry references model registry only by ID and policy, not by file path.

## 13. Failure and Fallback

Failure types:
1. health check failure
2. endpoint unavailable
3. timeout
4. compatibility failure
5. selected endpoint failure
6. selected model version failure
7. fallback endpoint
8. fallback model version

Failure rule:
1. Every fallback must emit a trace event.
2. `no_silent_fallback` applies to both agent and model selection.
3. If an endpoint is unavailable, the gateway may select another eligible endpoint only if policy allows and the choice is visible in trace.
4. If no eligible endpoint exists, the failure must be surfaced explicitly.

Recommended trace event types:
1. `agent_selected`
2. `agent_invoked`
3. `agent_result_received`
4. `agent_unavailable`
5. `fallback_used`

## 14. Trace / Evidence Requirements

Every agent call must preserve trace and evidence.

Required fields in emitted records:
1. `trace_id`
2. `orchestration_run_id`
3. `orchestration_step_id`
4. `agent_code`
5. `agent_version`
6. `endpoint_id`
7. `endpoint_url`
8. `model_version_id`
9. `agent_invocation_id`
10. `runtime_stub_or_real_model`
11. `fallback_reason` nullable
12. `approval_status` when available

Rules:
1. Backend-generated `trace_id` must be preserved end to end.
2. Gateway must not generate replacement trace IDs.
3. Agent invocation and result must be linked to the selected endpoint.
4. If stub is used, the trace must clearly mark it as stub.
5. Evidence must point to registry IDs, not guessed filesystem locations.

## 15. Database Draft

This stage only defines contract intent. No migration execution is allowed.

Suggested tables for later implementation:
1. `agent_registry`
2. `agent_versions`
3. `agent_endpoints`
4. `agent_capabilities`
5. `agent_invocations`
6. `orchestration_runs`
7. `orchestration_steps`

### 15.1 What is needed now vs later

Needed in the near term:
1. Agent registry base records.
2. Endpoint metadata.
3. Capability records.
4. Invocation and orchestration run records.

Can be deferred slightly:
1. Detailed endpoint rollout history.
2. Rich multi-step orchestration analytics.
3. Expanded endpoint health history.

## 16. Security and Governance

1. Agent endpoints should not be publicly exposed by default.
2. Agent calls should use service-to-service authentication or an internal trust policy.
3. Secrets must not be printed in logs.
4. Agent cannot generate or replace `trace_id` on its own.
5. Agent cannot silently swap model versions.
6. Agent cannot automatically train.
7. Endpoint selection must follow policy and registry state.
8. Failure handling must be auditable.

## 17. `.pth / Artifact Rule`

1. Do not scan, copy, move, or guess `.pth`, `.pt`, `.onnx`, `.ckpt`, or `.safetensors` files.
2. Real model artifact paths must come from the user through the main controller only.
3. Artifact registration must happen through model registry, not through agent registry.
4. Agent registry should reference `model_version_id` only and must not manage model files directly.
5. Model files must not be committed to Git.

## 18. Stage Plan

Recommended next stages:
1. Stage 36: Agent Gateway skeleton.
2. Stage 37: Multi-Agent Orchestration contract.
3. Stage 38: Multi-Agent Orchestration backend skeleton.
4. Stage 39: Frontend multi-agent result display.
5. Stage 40+: Real model integration preparation after user provides exact artifact paths.

## 19. Main-Controller Writeback Summary

1. Stage 35 Agent Registry contract is now drafted.
2. Registry now covers agents, agent versions, endpoints, capabilities, orchestration runs, and invocations.
3. Unified Agent Gateway is the intended single backend entry surface for agent calls.
4. Endpoint migration, capability change, and model upgrade integration are defined without hardcoding agent addresses.
5. `no_silent_fallback` applies to agent routing and endpoint selection.
6. Trace and evidence must retain `agent_code`, `agent_version`, `endpoint_id`, `endpoint_url`, `model_version_id`, and `agent_invocation_id`.
7. `.pth` artifact discovery remains prohibited; registry must rely on user-provided artifact metadata through model registry, not filesystem scanning.
