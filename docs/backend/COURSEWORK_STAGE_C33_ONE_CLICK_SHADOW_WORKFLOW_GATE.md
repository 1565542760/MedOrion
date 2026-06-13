# Coursework Stage C33: CAP/COP One-Click Shadow Workflow Gate Preview

## Goal
Provide a backend-only readiness preview for the CAP/COP one-click shadow workflow.
The preview must answer whether the current case can run:
- clinical MLP
- imaging ResNet18
- multimodal ResNet18

This stage is preview-only.
It does not invoke a runner, does not write shadow audit rows, and does not produce recommendations.

## Endpoint
GET /api/v1/cases/{case_id}/cap-cop-shadow/workflow-readiness

## Response Shape
The response returns:
- overall_status: eady_partial, eady_all, or locked
- ranches.clinical_mlp
- ranches.imaging_resnet18
- ranches.multimodal_resnet18

Each branch returns:
- status: eady, locked, schema_unverified, preprocessing_required, or unavailable
- can_run
- disabled_reasons
- equired_inputs
- detected_inputs
- 
ext_action

## Branch Rules
### Clinical MLP
Ready only when a latest ready clinical snapshot exists and it is:
- alidation_status = ready_for_inference
- current_assessment_status = ready_for_inference
- 
ot_for_diagnosis = true
- untime_stub = true

If the latest snapshot is schema-unverified, the branch is marked schema_unverified.
If the latest snapshot is insufficient, the branch is marked locked.
If no snapshot exists, the branch is unavailable.

### Imaging ResNet18
Ready only when a latest ready imaging input exists and it satisfies:
- deidentified = true
- 
ot_for_diagnosis = true
- input is already preprocessed NIfTI or a synthetic candidate

If the latest imaging input is a DICOM series and preprocessing is not completed, the branch is preprocessing_required.
If no imaging input exists, the branch is unavailable.

### Multimodal ResNet18
Ready only when both clinical and imaging branches are ready for the same case.
If either branch is blocked or unavailable, the multimodal branch is not ready.

## Safety Boundary
This preview:
- does not call any runner
- does not write shadow_inference_runs
- does not write shadow_inference_outputs
- does not write recommendations
- does not write trace_events
- does not write evidence_nodes or evidence_edges
- does not read DICOM files
- does not read NIfTI files
- does not change schema or migrations

## Case Coverage
The preview is case-scoped and uses existing clinical snapshot and imaging input records for the case.
It is meant to support the one-click workflow UX without performing execution.
