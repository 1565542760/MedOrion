# Coursework Stage C27: CAP/COP MVP Readiness Report

## Verdict
MedOrion is now ready to demonstrate a coursework-grade CAP/COP shadow workflow with clear provenance, readiness gating, and shadow audit separation.
It is **not** yet ready to claim a full end-to-end clinical table + DICOM -> CAP/COP shadow output pipeline, because the ingestion and preprocessing path still needs more backend engineering.

## What Is Already Completed

### 1. Clinical MLP
- CAP/COP clinical MLP shadow baseline exists.
- Fold5 artifact provenance is finalized.
- Shadow output can be produced through the controlled bridge path.
- The path remains labeled shadow-only and not-for-diagnosis.

### 2. Imaging ResNet18
- Controlled real-shadow backend exists.
- Frontend shadow audit display exists.
- The imaging path can participate in the case-level workbench and shadow audit flow.
- The path remains explicitly separated from diagnosis and formal recommendation.

### 3. Multimodal ResNet18
- Controlled real-shadow backend bridge exists.
- The multimodal route has been planned, prototyped, and provenance-reviewed.
- The route remains shadow-only and not a default or canary path.

### 4. DICOM Preprocessing Contract
- The DICOM preprocessing metadata contract is defined.
- Metadata-only preprocessing registration is supported as a contract, not as a full ingestion job.
- Raw DICOM is not treated as model-ready input.

### 5. Clinical Table Contract
- The clinical table / artifact-order input contract is defined.
- The 36-feature CAP/COP order is preserved.
- Striated_shadow.1 remains intentionally retained as a historical schema field.

### 6. Readiness Workflow
- Case-level readiness workflow exists.
- One-click shadow is now governed by explicit readiness and safety design.
- Disabled reasons are part of the workflow contract.
- The workflow must fail closed and must not silently fall back.

### 7. Shadow Audit / Access Audit
- Shadow audit storage exists separately from case trace/evidence.
- Access audit storage exists separately from shadow audit and case trace/evidence.
- The project can record who accessed what, and whether a shadow path ran, without implying diagnosis.

## What Can Be Demonstrated Now

### Synthetic / demo imaging shadow
- A synthetic or demo NIfTI-based shadow path can be demonstrated.
- This is only coursework/demo behavior and must be labeled accordingly.

### Controlled real-shadow
- The controlled shadow path can be demonstrated in a governed manner.
- The result is shadow-only and not a formal recommendation.

### Readiness workflow
- The case workbench can show whether a branch is ready or disabled.
- It can explain why a branch is disabled.
- It can keep clinical, imaging, and multimodal branches separate.

### DICOM preprocessing metadata-only registration
- The system can describe a DICOM preprocessing contract.
- It can register preprocessing intent and status at the metadata level.
- It does not yet provide the full ingestion / job execution pipeline.

## What We Cannot Claim

### Not allowed to claim
- formal diagnosis
- formal recommendation
- production, default, or canary readiness
- external validation completed
- automatic DICOM batch processing already implemented
- clinical equivalence to a deployed hospital system

### Not allowed to imply
- that any shadow score is a diagnosis
- that any candidate label is a treatment recommendation
- that synthetic/demo inputs are real patient inputs
- that fallback behavior is acceptable when data are missing

## What Is Still Missing for the Full Target

### 1. DICOM upload / storage
- A complete DICOM upload and storage flow.
- A reliable case-scoped object reference layer for imaging inputs.
- Clear handling of raw DICOM series vs model-ready imaging artifacts.

### 2. DICOM -> image.nii.gz preprocessing job
- An actual preprocessing job implementation.
- Status transitions such as pending, running, completed, and failed.
- Error handling and audit visibility for preprocessing failures.

### 3. Strict clinical CSV import validation
- Backend enforcement of the artifact-order 36-feature contract.
- Clear validation for missing, extra, or misordered columns.
- Deterministic mapping from clinical CSV to model input snapshot.

### 4. One-click workflow backend orchestration
- A single backend orchestration layer that can coordinate readiness checks, branch selection, shadow execution, and audit emission.
- Hard gate enforcement for clinical, imaging, and multimodal branches.
- No silent fallback between model families.

### 5. Final report / export
- A final coursework export/report path that can summarize the readiness, the shadow outputs, the limitations, and the compliance boundaries.
- A presentation-friendly output for the course deliverable.

## Coursework Compatibility Judgment

### Machine vision component
- Partially satisfied at the workflow level.
- Imaging ResNet18 shadow paths and preprocessing contracts provide the vision side of the story.
- The missing piece is the full DICOM ingestion and preprocessing job path.

### Digital twin component
- Partially satisfied through case-level readiness, shadow audit, and provenance-linked workbench views.
- The current workbench can represent a case-level state machine, but it is not yet a complete digital twin lifecycle with full ingestion and job execution.

### Experimental validation component
- Strong for controlled shadow and provenance review.
- Suitable for coursework demonstration of traceability, shadow gating, and audit separation.
- Not yet strong enough to claim a fully operational clinical pipeline.

### Scientific rigor boundary
- Good enough to support a careful coursework report if the report states exactly what is implemented and what is still pending.
- Not good enough to blur demo, shadow, and clinical conclusions.
- The report must keep the provenance, limitation, and non-diagnostic language explicit.

## Recommended Next Stages

### C28
Implement the DICOM preprocessing job plan and execution skeleton.

### C29
Implement the clinical CSV import backend contract with strict 36-feature validation.

### C30
Implement the one-click shadow orchestration backend skeleton.

### C31
Prepare the coursework final report / deck.

## Overall Readiness Conclusion
MedOrion is ready for a strong coursework demonstration of:
- provenance-aware case workbench behavior,
- readiness gating,
- shadow-only outputs,
- and audit separation.

It is **not yet ready** to claim a full clinical table + DICOM -> CAP/COP shadow output pipeline until the ingestion, preprocessing, and orchestration pieces are completed.

## Compliance Boundary
- Read-only investigation and documentation only.
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
