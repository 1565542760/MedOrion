# MedOrion Traceability Stage 23 Missing Value Review

Last updated: 2026-06-02 Asia/Shanghai
Reviewer thread: MedOrion traceability and quality-control
Scope: Fast re-review of Stage 22 missing-value consultation minimal closure.
Boundary: Review only. No schema change, no Alembic execution, no business expansion, no real model integration, no training, no Nginx/public exposure.

## 1. Review Inputs

Reviewed code:
1. `/home/sygxdg/MedOrion/app/backend/app/modules/clinical/router.py`
2. `/home/sygxdg/MedOrion/app/backend/app/modules/clinical/schemas.py`

Reviewed contracts:
1. `/home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md`
2. `/home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_02_SCHEMA_API_PLAN.md`

## 2. Overall Conclusion

Stage 23 review result: **pass**.

Interpretation:
1. Stage 22 implements the required doctor-first missing-value loop.
2. The create, answer, and default paths are trace-bound and audit-readable.
3. The default path is explicitly distinguishable from doctor-provided input.
4. The flow is still stub-only and not a real diagnostic or real recommendation system.

## 3. Focused Findings

### 3.1 Create query ordering

Assessment:
1. Query creation persists the record first.
2. Trace events are then written in the required order:
   - `missing_value_detected`
   - `doctor_question_asked`
3. Both events share the same `trace_id`, `case_id`, and `patient_id`.

Decision:
1. Ordering is correct and matches the contract intent.
2. The create path is sufficient for the minimal doctor-first audit chain.

### 3.2 Doctor answer path

Assessment:
1. Answer path updates the query to `answered`.
2. It sets `value_source = doctor_provided`.
3. It writes `doctor_answer_received` on the same trace.
4. Returned query payload exposes the resolved `value_source` and doctor answer content.

Decision:
1. The answer path clearly expresses doctor-provided resolution.
2. This is sufficient for audit and downstream consumers.

### 3.3 Default path

Assessment:
1. Default path updates the query to `default_applied`.
2. It sets `value_source = default_applied`.
3. It writes `default_strategy_applied` on the same trace.
4. It persists `default_strategy_code`, `default_reason`, and `default_value_json`.

Decision:
1. The default path clearly expresses defaulted resolution.
2. The query state and payload are enough to distinguish it from doctor input.

### 3.4 Default evidence semantics

Assessment:
1. The default path writes two evidence nodes: the missing-value question node and the defaulted node.
2. The nodes carry `runtime_stub: true` and `value_source` metadata.
3. The edge type is `missing_value_defaulted`, which matches the contract.
4. This is sufficient to show that the value came from policy/default processing rather than a doctor answer.

Decision:
1. Evidence semantics are acceptable for the minimal closure.
2. The graph is explicit enough for audit and lineage display.

### 3.5 Trace binding

Assessment:
1. All create/answer/default events use one shared `trace_id` per query flow.
2. `case_id` and `patient_id` are carried into query storage and events.
3. `query_id` and `field_name` are preserved in query rows and event payloads.
4. `status`, `policy_version`, and `runtime_stub` are present in the user-facing and audit payloads.

Decision:
1. Trace binding is coherent and sufficient.

### 3.6 Error semantics

Assessment:
1. `case_not_found` is returned as `404 case_not_found`.
2. `query_not_found` is returned as `404 query_not_found`.
3. These error codes are clear and appropriate for client handling.

Decision:
1. Error semantics are good and do not block the next stage.

### 3.7 Misleading diagnosis / untrue fill risk

Assessment:
1. No direct claim of real diagnosis or real unassisted clinical correction was found.
2. `runtime_stub: true` is propagated in trace/event payloads and default evidence payloads.
3. The remaining risk is primarily UI wording, not backend semantics.

Decision:
1. No blocking wording issue found in the reviewed backend flow.

## 4. Must-Fix vs Suggestion

Must-fix:
1. None identified from trace/evidence audit semantics.

Suggestion:
1. If the frontend later needs stronger explanation of provenance, surface `value_source` and `default_strategy_code` prominently in the consultation detail panel.

## 5. Next Stage Recommendation

Recommended next stage: **doctor feedback minimal closure or dynamic reassessment groundwork**.

Reason:
1. The missing-value loop is now stable enough to support downstream feedback and reassessment.
2. `case_id` / `patient_id` / `trace_id` anchoring is already in place.
3. The next useful contract is either doctor feedback or reassessment tracking, depending on main-controller priority.

## 6. Controller Writeback Summary

1. Stage 23 review result: **pass**.
2. No must-fix item remains for the missing-value audit loop.
3. Answer path clearly expresses `doctor_provided`.
4. Default path clearly expresses `default_applied` and is distinguishable from doctor input.
5. `missing_value_defaulted` edge is appropriate and adequately proves the value came from policy/default processing.
6. No hidden `case-001`-style fallback was introduced.
7. Recommend entering Git checkpoint discussion if the main controller wants to checkpoint Stage 22/23 together.
8. No schema change, Alembic execution, Nginx enablement, real-model integration, training, or `.pth/.pt/.onnx/.ckpt/.safetensors` operation was performed in this review.
