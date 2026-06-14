# Coursework Stage C40: Multimodal Clinical Payload Alignment

## Scope
This stage aligned the CAP/COP one-click workflow execution payload so that the clinical, imaging, and multimodal branches all use the same strict snapshot and preprocessed imaging semantics.

## Root Cause
Two mismatches were blocking `execute` while readiness and preview were already correct:

1. `clinical_mlp` execute still relied on an old precheck path and only passed `input_snapshot_id` to the fold5 runner. The fold5 runner expects `mapped_features` in the exact artifact order from `clinical_tabular_standardization_v1.json`.
2. `multimodal_resnet18` execute forwarded imaging contract metadata with `source_format=dicom_series`, which the runner rejects even when preprocessing has completed and `storage_uri` points to a managed `image.nii.gz`.

## Fix
### Clinical branch
- Reused the strict snapshot selector from the workflow readiness path.
- Bypassed the stale pre-execution insufficiency gate for the strict snapshot path.
- Passed `mapped_features` to the fold5 runner in the exact artifact order expected by the clinical runner preprocess artifact.

### Multimodal branch
- Reused the strict multimodal snapshot selector.
- Preserved the preprocessing gate: only completed preprocessing inputs are accepted.
- Passed preprocessed NIfTI semantics to the runner (`source_format` / `preprocessed_format` set from the completed preprocessed form), never a raw DICOM directory reference.

## Strict Helper / Selector Behavior
- Workflow readiness remains `ready_all` for the validated fixture case.
- The multimodal clinical snapshot selector requires:
  - `validation_status=ready_for_inference`
  - `current_assessment_status=ready_for_inference`
  - `not_for_diagnosis=true`
  - 36-feature payload completeness
  - exact artifact-order alignment
  - `Striated_shadow.1` present
- The runner payload builder now reuses the same strict feature extraction path.

## Verification
Validated on case `e0298498-e397-481e-9345-f20d5825995c` with strict snapshot `snap_f5dca77aefdb4666`.

### Readiness
- `overall_status=ready_all`
- clinical: `ready`
- imaging: `ready`
- multimodal: `ready`

### Preview
- clinical: `planned`
- imaging: `planned`
- multimodal: `planned`

### Execute
- clinical: `executed`
- imaging: `executed`
- multimodal: `executed`

### Shadow artifacts written by the final execute validation
- clinical shadow run/output created
- imaging shadow run/output created
- multimodal shadow run/output created

### Count changes from the final execute validation
- `shadow_inference_runs`: +3
- `shadow_inference_outputs`: +3
- `recommendations`: unchanged
- `trace_events`: unchanged
- `evidence_nodes`: unchanged
- `evidence_edges`: unchanged

### Runtime checks
- `python -m compileall app/backend/app` passed
- `alembic current` -> `b9c6a5d4e3f2 (head)`
- `alembic check` -> clean
- `GET /health/ready` -> 200

## Compliance Notes
- No schema changes
- No Alembic migration
- No recommendation write
- No trace/evidence write
- No model file scanning/copying/moving
- Shadow-only execution remained in place
