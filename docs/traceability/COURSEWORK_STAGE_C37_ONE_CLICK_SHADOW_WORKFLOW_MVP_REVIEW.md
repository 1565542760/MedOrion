# Coursework Stage C37: CAP/COP One-Click Shadow Workflow MVP Review

## Verdict
The current one-click CAP/COP shadow workflow is suitable as a **coursework MVP demonstration**.
It is **not** yet a full end-to-end clinical table + DICOM -> CAP/COP shadow output pipeline, and it must not be described as diagnosis, formal recommendation, production, default, canary, or externally validated clinical automation.

## Files Reviewed
- /home/sygxdg/MedOrion/docs/traceability/COURSEWORK_STAGE_C25_CAP_COP_ONE_CLICK_SHADOW_WORKFLOW_SAFETY_DESIGN.md
- /home/sygxdg/MedOrion/docs/backend/COURSEWORK_STAGE_C33_ONE_CLICK_SHADOW_WORKFLOW_GATE.md
- /home/sygxdg/MedOrion/docs/backend/COURSEWORK_STAGE_C35_ONE_CLICK_SHADOW_WORKFLOW_ENDPOINT.md
- /home/sygxdg/MedOrion/docs/traceability/COURSEWORK_STAGE_C35_ONE_CLICK_SHADOW_WORKFLOW_REVIEW.md
- /home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C27_CAP_COP_MVP_READINESS_REPORT.md
- /home/sygxdg/MedOrion/docs/architecture/SOURCE_OF_TRUTH.md
- /home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/router.py
- /home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/workflow_readiness.py
- /home/sygxdg/MedOrion/app/frontend/src/app/cases/[caseId]/page.tsx
- /home/sygxdg/MedOrion/app/frontend/src/app/cases/[caseId]/shadow-audit/page.tsx

## MVP Review Conclusion
The workflow now behaves like a safe coursework-ready gate:
- preview is read-only,
- execute is guarded,
- branch execution is explicit,
- and disabled branches are skipped rather than silently replaced.

That is enough for a coursework MVP demo because it shows the user-facing workbench, readiness gating, and shadow-only outputs without crossing into recommendation or diagnosis.

## Branch Statuses
### Clinical MLP
- The clinical branch is usable in the current workflow.
- It can run as a shadow branch when the case has a ready clinical snapshot.
- The branch remains labeled shadow-only and not-for-diagnosis.

### Imaging ResNet18
- The imaging branch is also usable in the current workflow.
- It can run as a shadow branch when imaging input is eligible and preprocessing requirements are satisfied.
- Raw DICOM is not treated as model-ready input.

### Multimodal ResNet18
- The multimodal branch is still the strictest branch.
- For a real case, it remains guarded by the combined clinical + imaging contract.
- In the current MVP flow it is typically skipped unless the exact readiness contract is satisfied.
- For coursework demonstration, it should be treated as conditional, not guaranteed.

## Preview -> Guarded Execute Safety Assessment
This part is acceptable for the MVP.

Why it is safe enough:
- preview does not execute runners,
- execute only runs explicitly eligible branches,
- disabled branches remain skipped with reasons,
- there is no silent fallback between model families,
- and the workflow does not write recommendation, trace, or evidence records.

The current design is therefore a controlled orchestration flow, not a hidden clinical action.

## What Can Be Claimed
The report can safely claim that MedOrion now supports:
- a case-scoped one-click CAP/COP shadow workflow,
- preview and guarded execute behavior,
- explicit readiness gating,
- clinical / imaging / multimodal branch separation,
- shadow audit output for executed branches,
- and non-diagnostic user-facing warnings.

## What Cannot Be Claimed
The report must not claim:
- formal diagnosis,
- formal recommendation,
- default / canary / production readiness,
- external validation,
- automatic DICOM batch processing,
- a complete end-to-end clinical table + DICOM -> CAP/COP shadow pipeline,
- or that multimodal is universally runnable for every case.

## Most Important Missing Gap
The biggest remaining gap is the **real DICOM preprocessing execution path**:
- DICOM upload / storage,
- DICOM -> raw_image.nii.gz conversion,
- N4 / preprocessing execution,
- image.nii.gz registration,
- and then a fully reliable multimodal readiness path for genuinely complete clinical + imaging inputs.

Without that path, the workflow remains a strong coursework MVP but not a full pipeline.

## Should We Proceed to DICOM Real Preprocessing Execution?
Yes, if the next project goal is to close the remaining pipeline gap.

But it should be approached as the next controlled engineering step, not as a clinical claim:
- keep deidentification and provenance explicit,
- keep DICOM preprocessing as a separate governed job,
- and keep shadow audit / trace-evidence boundaries intact.

## Safety and Compliance Boundary
- Read-only review and documentation only.
- No code changes.
- No database changes.
- No Alembic execution.
- No model execution.
- No DICOM/NIfTI reads.
- No scanning, copying, or moving model files.
- No training.
- No recommendation writes.
- No trace/evidence writes.
- No shadow audit writes.
- No diagnosis language.
- No production/default/canary claims.
