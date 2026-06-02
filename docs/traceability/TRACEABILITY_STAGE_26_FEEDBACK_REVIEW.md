# MedOrion Traceability Stage 26 Feedback Review

Last updated: 2026-06-02 Asia/Shanghai
Reviewer thread: MedOrion traceability and quality-control
Scope: Fast re-review of Stage 25 doctor feedback minimal closure.
Boundary: Review only. No schema change, no Alembic execution, no business expansion, no real model integration, no training, no Nginx/public exposure.

## 1. Review Inputs

Reviewed code:
1. `/home/sygxdg/MedOrion/app/backend/app/modules/feedback/router.py`
2. `/home/sygxdg/MedOrion/app/backend/app/modules/feedback/schemas.py`
3. `/home/sygxdg/MedOrion/app/backend/app/modules/cases/router.py`
4. `/home/sygxdg/MedOrion/app/backend/app/modules/inference/persistence.py`
5. `/home/sygxdg/MedOrion/app/backend/app/db/models.py`

Reviewed contracts:
1. `/home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_STAGE_01_CONTRACT.md`
2. `/home/sygxdg/MedOrion/docs/backend/BACKEND_STAGE_02_SCHEMA_API_PLAN.md`

## 2. Overall Conclusion

Stage 26 review result: **pass**.

Interpretation:
1. Stage 25 feedback loop records doctor feedback as an append-only trace/audit event.
2. Feedback is bound to case, trace, and recommendation without overwriting the original recommendation record.
3. The flow is suitable as the minimal doctor feedback closure for stub stage.

## 3. Focused Findings

### 3.1 `doctor_feedback_recorded` taxonomy fit

Assessment:
1. `doctor_feedback_recorded` is a valid Stage 01 trace event type.
2. It is used as an append-only audit event after feedback creation.
3. The event is written on the same trace as the recommendation and feedback record.

Decision:
1. Taxonomy fit is correct.

### 3.2 Event payload audit sufficiency

Assessment:
1. Payload includes `case_id`, `trace_id`, `feedback_id`, `recommendation_id`, `feedback_type`, `doctor_decision`, `rating`, `learning_eligible`, `actor_type`, `actor_id`, `actor_role`, and `runtime_stub`.
2. This is sufficient to reconstruct who said what, against which recommendation, and whether the item is eligible for offline learning.
3. The payload is clearly audit-oriented and does not look like a model update instruction.

Decision:
1. Payload coverage is sufficient for the minimal closure.

### 3.3 Feedback vs recommendation relationship

Assessment:
1. Feedback is inserted into `doctor_feedback` as a separate record.
2. The reviewed code does not overwrite the original recommendation row.
3. The trace event is appended independently, preserving provenance.
4. `GET /api/v1/feedback` and `GET /api/v1/cases/{case_id}/feedback` both list feedback records rather than mutating recommendation state.

Decision:
1. Relationship is correct and aligned with traceability contract.

### 3.4 Binding correctness

Assessment:
1. `case_id` is resolved through case context.
2. `recommendation_id` is validated as UUID and verified to belong to the case.
3. `trace_id` is inherited from the recommendation when not supplied.
4. If supplied and mismatched, the route returns `trace_mismatch`.
5. `doctor_id` is derived from token-backed current user when available.

Decision:
1. Binding is correct and sufficiently strict.

### 3.5 `trace_mismatch` strategy

Assessment:
1. Rejecting cross-trace feedback with `409 trace_mismatch` is appropriate.
2. It prevents accidental contamination of provenance chains.
3. The recommendation remains the anchor; feedback cannot silently drift to another trace.

Decision:
1. `trace_mismatch` handling is good and should stay strict.

### 3.6 `learning_eligible` as learning-entry marker

Assessment:
1. `learning_eligible` is a good gate for later governed learning pool ingestion.
2. It records a future-use intent without triggering any online training.
3. The field remains advisory and auditable.

Decision:
1. `learning_eligible` is appropriate for the stub stage.

### 3.7 `stub_doctor` fallback

Assessment:
1. When no bearer token is present, the route falls back to `stub_doctor` and marks the path as stub.
2. This is acceptable for stub-only operation and trace demo flows.
3. It should not be interpreted as final identity assurance.

Decision:
1. Acceptable for now.
2. Should be tightened later if the project moves toward operational auth/audit hardening.

### 3.8 `GET /api/v1/cases/{case_id}/feedback`

Assessment:
1. The endpoint is semantically reasonable as a convenience view for case-level feedback history.
2. It does not alter trace semantics because the canonical audit record still lives in `doctor_feedback` and `trace_events`.
3. It is consistent with the minimal UI flow and does not white-screen.

Decision:
1. Endpoint semantics are acceptable.

### 3.9 Uncommitted `app/modules/cases/router.py` changes

Assessment:
1. The modified case router includes feedback-listing convenience behavior.
2. It does not appear to mutate feedback provenance or overwrite recommendations.
3. It is coupled to the feedback feature surface, so it should be considered part of the same checkpoint window rather than ignored as unrelated drift.

Decision:
1. Not blocking.
2. Should be included in the next Git checkpoint review set because it affects the visible route surface for case feedback.

### 3.10 Misleading model-update / diagnosis risk

Assessment:
1. No evidence was found that feedback auto-updates a model or rewrites a recommendation.
2. The payload remains stub-marked.
3. The main risk is UI wording, not backend provenance.

Decision:
1. No blocking wording issue found.

## 4. Must-Fix vs Suggestion

Must-fix:
1. None identified from trace/evidence audit semantics.

Suggestion:
1. Later hardening can require token-backed actor identity even for feedback creation, but this is not required for the current stub-stage checkpoint.
2. Keep `learning_eligible` clearly documented as a governed offline-learning gate, not a training trigger.

## 5. Next Stage Recommendation

Recommended next stage: **quality review / attribution closure or continued governed learning plumbing**, depending on main-controller priority.

Reason:
1. Feedback closure is now present.
2. The next traceability step can focus on QC triage, error attribution, or learning-pool governance rather than provenance basics.

## 6. Controller Writeback Summary

1. Stage 26 review result: **pass**.
2. No must-fix item remains for the doctor feedback minimal closure.
3. `doctor_feedback_recorded` is correctly used as an append-only audit event.
4. Payload is sufficiently rich for audit and provenance reconstruction.
5. Feedback does not overwrite the original recommendation.
6. `trace_mismatch` is a good strictness check and should remain.
7. `learning_eligible` is appropriate as a future learning-entry marker.
8. `stub_doctor` fallback is acceptable for stub stage but should be tightened later if identity hardening becomes a goal.
9. `GET /api/v1/cases/{case_id}/feedback` is semantically reasonable.
10. The uncommitted `cases/router.py` change is not blocking, but it should be included in the next Git checkpoint review set because it affects the case feedback route surface.
11. No schema change, Alembic execution, Nginx enablement, real-model integration, training, or `.pth/.pt/.onnx/.ckpt/.safetensors` operation was performed in this review.
