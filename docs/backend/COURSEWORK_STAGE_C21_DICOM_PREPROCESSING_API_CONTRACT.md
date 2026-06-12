# Coursework Stage C21: CAP/COP DICOM Preprocessing API / Data Contract

## Verdict
- The existing `case_imaging_inputs` table is sufficient for the C21 preprocessing contract.
- No schema migration is required for the metadata-only coursework skeleton.
- The backend should register DICOM-series metadata, expose preprocessing status, and refuse to pretend that raw DICOM is already model-ready.

## Files Read
- `/home/sygxdg/MedOrion/app/backend/app/modules/imaging_inputs/router.py`
- `/home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/imaging_contract.py`
- `/home/sygxdg/MedOrion/app/backend/app/db/models.py`
- `/home/sygxdg/MedOrion/app/backend/app/api/v1/router.py`
- The C20 imaging contract code already checkpointed as commit `202b600`
- The user-provided `dcmtonii_N4.py` preprocessing flow as summarized in chat

## Current Backend Capability
- `case_imaging_inputs` already stores imaging metadata and provenance via JSON columns.
- The imaging input router already supports case-scoped create/list/detail flows.
- The shadow contract helper already distinguishes preprocessed NIfTI references from DICOM-like inputs.
- Case-level access control already exists and should continue to gate imaging resources.

## Gap
- The backend has no explicit preprocessing lifecycle contract for DICOM series.
- There is no metadata-only way to say:
  - a DICOM series was registered
  - preprocessing is pending
  - preprocessing is completed or failed
  - preprocessing is not implemented in this coursework skeleton
- The course must not blur raw DICOM registration with model-ready NIfTI inputs.

## Recommended Contract
### Core identifiers
- `case_id`
- `patient_id`
- `trace_id`
- `input_asset_id`

### Required imaging provenance fields
- `source_format = dicom_series`
- `preprocessed_format = nifti_nii_gz`
- `preprocessing_script = dcmtonii_N4.py`
- `conversion_tool = dcm2niix`
- `bias_correction = N4BiasFieldCorrection`
- `raw_output_file = raw_image.nii.gz`
- `model_input_file = image.nii.gz`
- `label_file = label.nii.gz` for annotation reference only
- `preprocessing_status = pending / completed / failed / not_implemented`
- `not_for_diagnosis = true`
- `deidentified = true`

### Storage and provenance
- `storage_uri` or managed object reference is allowed as a metadata reference.
- The backend must not treat a DICOM directory-like reference as a model-ready image.
- The backend must not run `dcm2niix` or N4 inside this skeleton.
- The backend must not create a real `image.nii.gz` in this stage.

## Proposed API Skeleton
### 1. Register a DICOM-series imaging reference
- `POST /api/v1/cases/{case_id}/imaging-inputs/dicom-series`

Purpose:
- Register metadata only.
- Record that the reference is DICOM-series based.
- Record the preprocessing contract, but do not execute any conversion.

### 2. Request / simulate preprocessing contract state
- `POST /api/v1/imaging-inputs/{input_asset_id}/preprocess`

Purpose:
- Return a contract-aware response such as `preprocessing_not_implemented`.
- Do not execute `dcm2niix`.
- Do not execute N4.
- Do not create real image files.

### 3. Read preprocessing status
- `GET /api/v1/imaging-inputs/{input_asset_id}/preprocessing-status`

Purpose:
- Return the current preprocessing status plus the contract metadata.
- Provide a clean answer to whether the reference is pending, completed, failed, or not implemented.

## Request / Response Draft
### Registration request
```json
{
  "patient_id": "uuid",
  "trace_id": "trace-id",
  "modality": "CT",
  "source_type": "real_deidentified",
  "storage_uri": "/path/to/dicom/reference",
  "deidentified": true,
  "not_for_diagnosis": true,
  "provenance_json": {
    "source_format": "dicom_series",
    "preprocessed_format": "nifti_nii_gz",
    "preprocessing_script": "dcmtonii_N4.py",
    "conversion_tool": "dcm2niix",
    "bias_correction": "N4BiasFieldCorrection",
    "raw_output_file": "raw_image.nii.gz",
    "model_input_file": "image.nii.gz",
    "label_file": "label.nii.gz",
    "preprocessing_status": "pending"
  },
  "quality_flags_json": {
    "deidentified": true,
    "not_for_diagnosis": true,
    "source_format": "dicom_series"
  }
}
```

### Status response
```json
{
  "input_asset_id": "img_...",
  "case_id": "uuid",
  "patient_id": "uuid",
  "trace_id": "trace-id",
  "preprocessing_status": "pending",
  "source_format": "dicom_series",
  "preprocessed_format": "nifti_nii_gz",
  "preprocessing_script": "dcmtonii_N4.py",
  "conversion_tool": "dcm2niix",
  "bias_correction": "N4BiasFieldCorrection",
  "raw_output_file": "raw_image.nii.gz",
  "model_input_file": "image.nii.gz",
  "label_file": "label.nii.gz",
  "not_for_diagnosis": true,
  "deidentified": true,
  "provenance_json": {},
  "quality_flags_json": {}
}
```

## Contract Rules
- DICOM directories must never be treated as model-ready inputs.
- A DICOM-series registration may be stored as pending metadata, but it is not a shadow runner input.
- `label.nii.gz` remains a training / evaluation label reference only.
- The backend must not silently convert raw DICOM into a shadow-ready input.
- The backend must not pretend preprocessing happened when it did not.

## Relationship to `case_imaging_inputs`
- Reuse the existing table.
- Use `provenance_json` and `quality_flags_json` to express the preprocessing lifecycle.
- Do not introduce a new table unless a future job queue or preprocessing audit is separately approved.
- Keep the raw DICOM registration separate from the model-ready NIfTI reference.

## Relationship to Shadow / Access / Trace Audit
- Access audit may record metadata-only registration or read operations if needed.
- Shadow audit should only appear when a real runner path is actually invoked.
- Trace/evidence tables must not be used for preprocessing registration.
- This stage is contract design, not inference.

## Future Persistence If Needed
If lifecycle tracking later needs more structure, a future migration could add fields such as:
- `preprocessing_status`
- `preprocessing_requested_at`
- `preprocessing_completed_at`
- `preprocessing_error_code`
- `preprocessing_error_message`
- `preprocessed_storage_uri`

Those are not required for this coursework stage.

## Next Step Recommendation
- Keep C21 metadata-only.
- Implement the small backend skeleton that registers DICOM-series metadata and exposes preprocessing status.
- Do not move directly to real preprocessing execution or batch processing.
- Only after the skeleton stabilizes should a future stage decide whether a dedicated preprocessing job table is worth adding.

## Compliance Boundary
- No real DICOM reads.
- No `dcm2niix` execution.
- No N4 execution.
- No real image creation.
- No training.
- No inference.
- No recommendation, trace, or evidence writes.
- No default / canary shadow enablement.
- No model file scanning, copying, or moving.
