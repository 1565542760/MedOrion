# Coursework Stage C35R: One-Click CAP/COP Shadow Workflow Review

## Verdict
- Stage C35 is **not fully acceptable as-is**.
- The workflow boundary is good in that preview and execute stay shadow-only and counts remain unchanged outside shadow artifacts.
- However, the multimodal branch can pass preview readiness and still fail at execute time with clinical_input_insufficient, which means the gate and runner are not using the same readiness basis.
- That mismatch should be tightened before checkpoint.

## Files Reviewed
- /home/sygxdg/MedOrion/docs/backend/COURSEWORK_STAGE_C35_ONE_CLICK_SHADOW_WORKFLOW_ENDPOINT.md
- /home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/workflow_orchestration.py
- /home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/router.py
- /home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/schemas.py

## Multimodal Readiness Mismatch Evaluation
- Preview mode uses the readiness gate and can mark multimodal as planned.
- Execute mode later calls the real multimodal branch and can still fail with clinical_input_insufficient.
- That is a contract smell: readiness must be strict enough that a branch planned as ready should not later fail because of a known input-contract deficiency.
- In practice, the branch should have been marked locked or skipped during gating if the selected snapshot or clinical payload was not fully compliant with the runner contract.

## Must-Fix Review
- Yes, there is a must-fix item.
- Multimodal readiness should be tightened so the gate checks the exact clinical payload requirements that the runner will enforce.
- The gating layer should verify at least:
eady_for_inference,
  - the snapshot contains the full 36-feature artifact order,
  - Striated_shadow.1 is present,
  - and the clinical payload passed to the runner matches the C18 runner contract.

## Clinical / Imaging Execution Evaluation
- Clinical and imaging branches executing successfully is acceptable for a shadow-only workflow.
- Those branches remain inside the shadow boundary because only shadow run/output artifacts are written.
- The important constraint is that execute must not surprise the workflow with a late input-contract failure that preview already should have predicted.

## Preview / Execute Boundary Evaluation
- Preview boundary is correct in the narrow sense: no runner invocation, no shadow rows, no recommendation, no trace, no evidence.
- Execute boundary is also correct in the narrow sense: only shadow run/output artifacts are written by the executed branch helpers.
- The issue is not leakage across boundaries; the issue is readiness consistency between preview and execute.

## Should C35 Be Checkpointed Now?
- Not yet.
- The multimodal mismatch should be fixed first so the workflow gate and runner contract line up.
- Once preview and execute agree on multimodal readiness, checkpoint is reasonable.

## Recommended Fix Direction
1. Make multimodal readiness explicitly inspect the selected clinical snapshot for exact artifact-order completeness.
2. Ensure Striated_shadow.1 is checked at gate time, not only at runner time.
3. Ensure the workflow sends the exact clinical payload shape expected by the C18 runner contract.
4. If those checks fail, mark the branch locked or skipped in preview rather than planned.
5. Keep the workflow shadow-only and do not expand it into recommendation, trace, or evidence writes.

## Safety Boundary
- Preview does not write shadow / recommendation / trace / evidence.
- Execute only writes shadow run/output for ready branches.
- Clinical and imaging shadow execution remains shadow-only and not a clinical conclusion.
- The review does not change any database state or model behavior.

## Compliance Boundary
- Read-only review and documentation only.
- No code changes.
- No database changes.
- No Alembic execution.
- No model execution.
- No shadow / recommendation / trace / evidence writes.
- No DICOM/NIfTI reads.
- No model file scanning, copying, or moving.
- No training.
