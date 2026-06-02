# MedOrion Traceability Stage 21 Case Binding Review

Last updated: 2026-06-02 Asia/Shanghai
Reviewer thread: MedOrion traceability and quality-control
Scope: Review of Stage 20 formal patient/case creation flow and trace/evidence binding semantics.
Boundary: Review only. No schema change, no Alembic execution, no business expansion, no real model integration, no training, no Nginx/public exposure.

## 1. Review Inputs

Reviewed code:
1. `/home/sygxdg/MedOrion/app/backend/app/modules/patients/router.py`
2. `/home/sygxdg/MedOrion/app/backend/app/modules/patients/schemas.py`
3. `/home/sygxdg/MedOrion/app/backend/app/modules/cases/router.py`
4. `/home/sygxdg/MedOrion/app/backend/app/modules/cases/schemas.py`
5. `/home/sygxdg/MedOrion/app/backend/app/modules/inference/router.py`
6. `/home/sygxdg/MedOrion/app/backend/app/modules/inference/persistence.py`
7. `/home/sygxdg/MedOrion/app/backend/app/db/models.py`

Reviewed contracts:
1. `/home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md`
2. `/home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_02_SCHEMA_API_PLAN.md`

Reference commit:
1. `ad881bd` `feat: add formal patient case creation flow`

## 2. Overall Conclusion

Stage 21 review result: **pass**.

Interpretation:
1. Stage 20 has moved MedOrion from implicit stub anchoring to a formal patient/case binding flow.
2. `case_id` and `patient_id` now provide a stable anchor for trace/evidence persistence.
3. The trace/evidence graph can now be tied to real database case records without silent fallback behavior.
4. The current flow is still stub-only and must not be interpreted as real diagnosis.

## 3. Focused Findings

### 3.1 Patient/case creation as stable trace/evidence anchor

Assessment:
1. `POST /api/v1/patients` creates persisted patient records.
2. `POST /api/v1/cases` requires a real `patient_id`.
3. `POST /api/v1/cases/{case_id}/inference-tasks` resolves case context from the database and binds `case_id` / `patient_id` into inference persistence.

Evidence:
1. `patients/router.py` creates patient rows and returns persisted items.
2. `cases/router.py` validates `patient_id`, creates case rows, and returns 404 on missing patient/case.
3. `inference/persistence.py` writes `case_id` and `patient_id` into `inference_tasks`, `recommendations`, `trace_events`, `evidence_nodes`, and `evidence_edges`.

Decision:
1. The formal patient/case flow is sufficient as a stable anchor for trace/evidence persistence.

### 3.2 Binding of `case_id` / `patient_id` into trace and evidence

Assessment:
1. `inference_tasks` stores `case_id` and `patient_id`.
2. `recommendations` stores `case_id`, `inference_task_id`, and `trace_id`.
3. `trace_events` stores `case_id` and nullable `patient_id`.
4. `evidence_nodes` stores `case_id` and nullable `patient_id`.
5. `evidence_edges` stores `case_id`.

Decision:
1. Binding coverage is correct for the formal flow.
2. This is enough to support later missing-value consultation, doctor feedback, dynamic reassessment, and model-version lineage work.

### 3.3 Implicit `case-001` fallback risk

Assessment:
1. The previous implicit fallback behavior has been removed.
2. `resolve_case_context()` now fails fast with `RuntimeError('case_not_found')` when the case is not found.
3. `create_case_inference_task()` converts that into `404 case_not_found`.
4. `ensure_stub_case()` only permits the explicit stub seed `case-001` and no longer falls back to the first case row.

Decision:
1. Implicit fallback risk is now effectively removed.
2. Residual risk is limited to the explicit dev-seed path, which is acceptable for stub-only operation.

### 3.4 `case_not_found` / `patient_not_found` semantics

Assessment:
1. `patient_not_found` is returned as a clear 404 from case creation.
2. `case_not_found` is returned as a clear 404 from inference resolution.
3. The error surface is now explicit enough for client and audit handling.

Decision:
1. Error semantics are clear and do not block the next stage.

### 3.5 Actor recording with access token

Assessment:
1. `create_case_inference_task()` maps bearer token roles to actor types via `_actor_from_request()`.
2. Doctor/admin identities are captured when token decoding succeeds.
3. Fallback actor values remain `orchestrator/backend_stub` or `system/backend_stub`.

Decision:
1. Actor recording is reasonable for the current stub stage.
2. Missing full auth attribution is not blocking for trace/evidence semantics.

### 3.6 `GET /api/v1/cases` and lineage semantics

Assessment:
1. Returning real database cases from `GET /api/v1/cases` is compatible with trace lineage.
2. The case list can serve as an anchor index, not as the lineage itself.
3. The real lineage source remains `GET /api/v1/traces/{trace_id}`, `.../events`, and `.../evidence-chain`.

Decision:
1. No semantic conflict found.
2. The cases list should not be mistaken for the trace graph.

### 3.7 Suitability for missing-value, feedback, and reassessment

Assessment:
1. Formal `case_id` / `patient_id` binding is sufficient groundwork for later missing-value consultation records.
2. It also supports doctor feedback and dynamic reassessment because those objects can now point back to stable case/patient anchors.
3. Model version management remains unaffected and can continue to key off `inference_task_id` / `trace_id`.

Decision:
1. Stage 20 is a sound foundation for the next missing-value consultation minimal closure.

### 3.8 Misleading real-diagnosis risk

Assessment:
1. No direct real-diagnosis claim was introduced by the reviewed case/patient flow.
2. The main residual risk is UX-level: a stub recommendation could be misread if not labeled clearly.

Decision:
1. No blocking wording issue found in the reviewed backend flow.

## 4. Required Modifications

None from the trace/evidence binding perspective.

## 5. Suggested Modifications

1. Keep `GET /api/v1/cases/{case_id}/traces` aligned with trace semantics if it later becomes a true trace list endpoint.
2. Continue marking stub outputs explicitly in API/UX so formal case binding is not mistaken for clinical diagnosis.
3. Preserve the explicit `case-001` seed path as dev-only and keep any future test-seed behavior opt-in.

## 6. Next Stage Recommendation

Recommended next stage: **missing-value consultation minimal closure**.

Reason:
1. Case/patient anchoring is now stable enough.
2. The next important contract to close is doctor-first missing-value handling with trace-aware audit records.
3. That step will naturally reuse the formal `case_id` / `patient_id` anchoring now in place.

## 7. Controller Writeback Summary

1. Stage 21 review result: **pass**.
2. No must-fix item remains for trace/evidence case binding semantics.
3. Implicit `case-001` fallback risk has been removed; only explicit dev-seed behavior remains.
4. `case_id` / `patient_id` binding is now stable across inference tasks, recommendations, trace events, evidence nodes, and evidence edges.
5. Actor recording is acceptable for stub stage; incomplete auth attribution is not blocking.
6. Returning real DB cases from `GET /api/v1/cases` does not harm lineage semantics as long as trace graph endpoints remain the lineage source.
7. The next recommended stage is the missing-value consultation minimal closure.
8. No schema change, Alembic execution, Nginx enablement, real-model integration, training, or `.pth/.pt/.onnx/.ckpt/.safetensors` operation was performed in this review.
