# Coursework Stage C39: Preprocessed DICOM Workflow Integration

## Goal
Connect the controlled C38 DICOM preprocessing output to the CAP/COP one-click shadow workflow.

## What Changed
The workflow gate and one-click workflow now recognize a DICOM-origin imaging input as ready once:
- preprocessing has completed
- storage_uri resolves to a managed-workspace NIfTI reference
- the resolved reference is image.nii.gz or another .nii/.nii.gz model-input reference
- deidentified=true
-
ot_for_diagnosis=true

## C38 Demo Case
- input_asset_id: img_c38_demo_dicom_001
- case_id: e0298498-e397-481e-9345-f20d5825995c
- storage_uri: /srv/medorion/workspaces/imaging_preprocessing/e0298498-e397-481e-9345-f20d5825995c/img_c38_demo_dicom_001/image.nii.gz
- preprocessing_status: completed

## Workflow Readiness Result
For the C38 demo case:
- clinical branch: ready
- imaging branch: ready
- multimodal branch: skipped
  - disabled reasons: clinical_input_insufficient, multimodal_clinical_schema_unverified

## Execute Behavior
The execute path now uses the completed preprocessed NIfTI reference for imaging branches.
For the C38 demo case, execute produced imaging shadow runs against the completed image.nii.gz reference.

## Safety Boundary
- No DICOM directory is accepted for shadow execution.
- DICOM series still require completed preprocessing.
- Non-managed workspace paths remain blocked.
- No model inference changes were introduced here.
- No recommendation, trace, or evidence writes were added.

## Validation Summary
- compileall: passed
- lembic current: 9c6a5d4e3f2 (head)
- lembic check: clean
- GET /health/ready: 200
- workflow-readiness: imaging ready on the C38 demo case
- workflow execute: imaging branch executed from completed preprocessed NIfTI reference

## Notes
- This stage keeps the workflow shadow-only and not-for-diagnosis.
- The imaging branch now correctly consumes the C38 preprocessing output without falling back to a DICOM directory.
