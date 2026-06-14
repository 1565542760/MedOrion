# Coursework Stage C38: Controlled DICOM Real Preprocessing Execution

## Goal
Implement a controlled, single-case, auditable real DICOM preprocessing execution path for CAP/COP imaging inputs.

## Safety Boundary
- Single demo / synthetic / deidentified case only.
- No batch processing.
- No model inference.
- No recommendation, trace, or evidence writes.
- No arbitrary path writes.
- No directory scanning.

## Controlled Execution Result
The controlled preprocessing path was executed successfully for the demo imaging input:
- `input_asset_id`: `img_c38_demo_dicom_001`
- `case_id`: `e0298498-e397-481e-9345-f20d5825995c`
- `patient_id`: `c12cd3bb-c959-4419-958b-8f918a7247ba`
- `trace_id`: `trace_c38_demo_dicom_001`
- `source_type`: `synthetic`
- `source_format`: `dicom_series`
- `deidentified`: `true`
- `not_for_diagnosis`: `true`

## Managed Workspace
- Workspace root: `/srv/medorion/workspaces/imaging_preprocessing/e0298498-e397-481e-9345-f20d5825995c/img_c38_demo_dicom_001`
- Raw NIfTI: `raw/raw_image.nii.gz`
- Model input NIfTI: `image.nii.gz`

## Toolchain
- `dcm2niix` executed in controlled mode.
- SimpleITK N4 bias correction executed in controlled mode.
- No model runner was called.

## Persisted State
The input row was updated to reflect preprocessing completion:
- `preprocessing_status = completed`
- `storage_uri` now points to `image.nii.gz`
- `provenance_json` and `quality_flags_json` record the preprocessing contract and execution metadata.

## Validation
- `alembic current` -> `b9c6a5d4e3f2 (head)`
- `alembic check` -> clean
- `GET /health/ready` -> 200
- `compileall` -> passed for backend app code

## Counts Observed After Execution
- `recommendations`: 30
- `trace_events`: 194
- `evidence_nodes`: 70
- `evidence_edges`: 35
- `shadow_inference_runs`: 38
- `shadow_inference_outputs`: 12
- `case_model_input_snapshots`: 8
- `case_assignments`: 0
- `access_audit_events`: 7

## Notes
- This is a controlled single-case preprocessing proof, not a general preprocessing service.
- It remains shadow-only and not-for-diagnosis.
- No clinical recommendation or evidence graph entries were created.
