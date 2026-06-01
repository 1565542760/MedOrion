# MedOrion Traceability Stage 14 Review

Last updated: 2026-06-01 Asia/Shanghai
Reviewer thread: MedOrion traceability and quality-control
Scope: Focused review of Stage 13 minimal trace/evidence persistence loop.
Boundary: Review only. No schema change, no Alembic execution, no real model integration, no training, no Nginx/public exposure.

## 1. Review Inputs

Reviewed code:
1. /home/sygxdg/MedOrion/app/backend/app/modules/inference/router.py
2. /home/sygxdg/MedOrion/app/backend/app/modules/inference/persistence.py
3. /home/sygxdg/MedOrion/app/backend/app/modules/traces/router.py
4. /home/sygxdg/MedOrion/app/backend/app/modules/traces/schemas.py

Reviewed contracts:
1. /home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md
2. /home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_02_SCHEMA_API_PLAN.md

Reference commit:
1. 614855e feat: add minimal trace evidence persistence loop

## 2. Overall Conclusion

Stage 13 trace/evidence semantics review result: **conditionally pass**.

Interpretation:
1. The current loop is a valid minimal audit chain for stub inference.
2. Core persistence objects and links are present and coherent (`inference_tasks`, `recommendations`, `trace_events`, `evidence_nodes`, `evidence_edges`).
3. The chain is not yet semantically complete for Stage 01 target taxonomy detail; it is acceptable as a minimal transitional baseline.

## 3. Focused Findings Against Requested Checks

### 3.1 trace_events ordering and taxonomy

Current event order:
1. `inference_task_created`
2. `model_invoked`
3. `model_result_received`
4. `recommendation_generated`

Assessment:
1. Order is reasonable for a minimal stub path.
2. All 4 event types are valid Stage 01 taxonomy members.
3. For full contract alignment, `model_selected` is missing; Stage 02 plan also lists it as required emitted event minimum.

Decision:
1. Minimal loop can temporarily omit `model_selected`.
2. Omission should be explicitly documented as a stub simplification and scheduled for next stage.

### 3.2 Are 4 events enough for minimal stub inference?

Assessment:
1. For pure "request -> invoke stub -> get output -> generate recommendation", 4 events are enough to trace the happy path.
2. They are not enough to explain model version selection rationale, routing decision semantics, or fallback policy.

Decision:
1. Acceptable for Stage 13 minimal closure.
2. Not sufficient as medium-term stable audit baseline without `model_selected` payload enrichment.

### 3.3 Should `model_selected` be added now?

Recommendation:
1. Yes, add in next iteration.
2. If no real selector exists yet, emit a deterministic stub event with explicit reason: `selection_reason=stub_default` and chosen `model_version_id`.

Rationale:
1. Keeps event chain compatible with Stage 01/Stage 02 contract and avoids later backfill ambiguity.

### 3.4 `model_invoked` and `model_result_received` payload minimum fields

Current payloads in Stage 13 are too thin:
1. `model_invoked` currently only carries `inference_task_id`.
2. `model_result_received` carries `inference_task_id` and `model_invocation_id` only.

Recommended minimal payload:
1. `model_invoked`:
   - `inference_task_id`
   - `invocation_id`
   - `model_version_id`
   - `input_refs` (or input ref count/hash if large)
   - `runtime_stub=true`
2. `model_result_received`:
   - `inference_task_id`
   - `invocation_id`
   - `model_version_id`
   - `output_ref` (node id or payload ref)
   - `confidence`
   - `uncertainty`
   - `status` (`succeeded`/`failed`)

### 3.5 `recommendation_generated` association fields

Current payload includes:
1. `inference_task_id`
2. `recommendation_id`

Gap:
1. Missing `model_version_id` and `evidence_chain_id` in event payload.

Recommendation:
1. Add `recommendation_version`, `evidence_chain_id`, and `model_version_id` to reduce cross-table reconstruction cost for audit.

### 3.6 evidence node semantics (`model_output` and `recommendation`)

Assessment:
1. Node types are correct and contract-compatible.
2. `model_output` node links to invocation id via `source_record_id` and stores uncertainty/confidence.
3. `recommendation` node links to recommendation record id.

Decision:
1. Semantics are clear enough for minimal lineage.

### 3.7 `supports` vs `derived_from` for edge type

Current edge:
1. `model_output -> recommendation`
2. `edge_type = supports`

Assessment:
1. `supports` is acceptable when recommendation is framed as a decision justified by evidence.
2. `derived_from` would imply transformation lineage.

Recommendation:
1. Keep `supports` as primary semantic for this relation.
2. Optionally add a second `derived_from` edge later only if recommendation content is programmatically transformed from model payload.

### 3.8 `recommendations.evidence_refs_json` consistency with graph

Assessment:
1. `evidence_refs_json` includes model node id and type.
2. Graph has corresponding `model_output` node and `supports` edge to recommendation node.
3. This is internally consistent for minimal case.

Caveat:
1. Prefer adding recommendation node id in refs (or explicit `evidence_chain_id`) in response payload for easier frontend stitching.

### 3.9 Trace query API readiness for frontend lineage page

Current API returns:
1. Trace summary counts (`/traces/{trace_id}`)
2. Ordered events list (`/traces/{trace_id}/events`)
3. Nodes/edges list (`/traces/{trace_id}/evidence-chain`)

Assessment:
1. Sufficient for a minimal lineage page MVP.
2. Missing richer fields for robust UI filtering/explanations: severity in response item, parent_event_id, source_record refs in events, uncertainty/status for nodes in response model typing.

Decision:
1. Adequate for Stage 13 MVP visualization.
2. Needs typed expansion before broader doctor-facing audit UX.

### 3.10 `patients/cases` stub anchor risk and convergence

Risk rating: **Medium**.

Reason:
1. `ensure_stub_case` can create generic anchor records and fallback to first case, which is acceptable only for stub loop enablement.
2. This can blur provenance ownership when multiple test flows run concurrently.

Convergence suggestion:
1. Replace with explicit case creation flow in next backend stage.
2. Block inference endpoint when case identity contract is missing, instead of silent fallback to first row.
3. Keep a temporary feature flag for stub anchor mode and mark records with explicit stub provenance tag.

### 3.11 Possible misleading "real diagnosis" signals

Assessment:
1. No explicit claim of diagnosis authority was found in reviewed trace modules.
2. Potential confusion risk exists if UI surfaces `status='active'` recommendation without clear stub badge/context.

Recommendation:
1. Ensure frontend and API docs label outputs as stub recommendation/demo inference.
2. Keep `runtime_stub=true` style marker in model-related trace payload.

### 3.12 Multi-disease / multi-model extensibility check

Assessment:
1. `disease_agent`, `model_version_policy`, and `model_version_id` plumbing exists in request/response path.
2. Event payload currently under-specifies model selection and invocation metadata, which weakens future multi-model comparisons.

Recommendation:
1. Enrich event payloads as listed above.
2. Add `model_selected` event to lock extension-friendly semantics now.

## 4. Must-Fix vs Should-Fix

Must-fix before treating this as stable audit baseline:
1. Add `model_selected` event (stub-friendly allowed).
2. Enrich `model_invoked` and `model_result_received` payload minimum fields.
3. Enrich `recommendation_generated` payload with `model_version_id` and `evidence_chain_id`.

Should-fix soon:
1. Expand trace event API response schema to include `severity`, `parent_event_id`, `source_record_type`, `source_record_id`.
2. Add explicit stub markers in payload and API response where recommendations are generated.
3. Replace `patients/cases` silent stub anchor fallback with explicit case workflow gate.

## 5. Controller Writeback Summary

1. Stage 13 minimal trace/evidence loop is **conditionally pass** as a transitional baseline.
2. Event ordering is coherent; current 4 events are enough for minimal happy-path stub inference but not yet semantically complete.
3. `model_selected` should be added next stage (stub deterministic selection allowed).
4. `supports` edge for `model_output -> recommendation` is appropriate for current semantics; keep it.
5. `recommendations.evidence_refs_json` is currently consistent with graph in tested flow.
6. Trace query APIs are sufficient for minimal lineage MVP, but event/detail richness should be expanded before broader audit UX.
7. `patients/cases` stub anchor has medium risk and should be converged to formal case creation flow soon.
8. No hard evidence in reviewed files of "real diagnosis" claims, but product/API labeling should keep explicit stub markers to avoid misinterpretation.

## 6. Constraint Confirmation

Confirmed in this Stage 14 review:
1. No database schema changes were made.
2. No Alembic command was executed.
3. No real model integration was performed.
4. No training or auto-training was performed.
5. No Nginx enablement or public exposure actions were performed.
6. No `.pth/.pt/.onnx/.ckpt/.safetensors` file path scanning/copy/move actions were performed.
