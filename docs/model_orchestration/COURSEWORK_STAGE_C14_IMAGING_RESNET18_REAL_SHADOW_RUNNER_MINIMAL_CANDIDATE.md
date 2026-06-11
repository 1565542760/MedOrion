# Coursework Stage C14: CAP/COP Imaging ResNet18 Real Shadow Runner Minimal Candidate

Scope: this stage upgrades the CAP/COP imaging ResNet18 runner from a disabled prototype into a minimal controlled real shadow runner candidate. The change is intentionally narrow: exact fold5 weight verification, CPU-only loading, single synthetic/demo/deidentified NIfTI inference, and explicit shadow-only output.

## 1. Files Read

Read-only inspection used:

1. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_imaging_resnet18_runner.py`
2. `/home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C13_IMAGING_RESNET18_REAL_RUNNER_PREFLIGHT.md`
3. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/`
4. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/preprocess_config.json`
5. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/dcmtonii_N4.py`
6. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/notebooks/restnet.ipynb`

## 2. Runner Implementation Summary

The runner now has two distinct paths:

### Disabled / metadata-only path

If `enable_real_shadow` is not set, the runner still returns:

- `status = disabled`
- `prototype_state = prototype_not_executed`
- `error.code = imaging_runner_not_loaded`

This preserves compatibility with the existing backend bridge behavior.

### Real shadow candidate path

If `enable_real_shadow = true`, the runner:

1. checks the exact artifact path,
2. computes SHA256 before load,
3. loads the exact fold5 artifact on CPU,
4. instantiates the imaging ResNet18 architecture,
5. loads the state dict strictly,
6. preprocesses a single explicit synthetic / demo / deidentified NIfTI input,
7. performs one `torch.no_grad()` forward pass,
8. returns a shadow-only JSON result.

## 3. Artifact / Runtime Result

### Exact artifact

- Path: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth`
- SHA256: `892fd836b0f361ca6ed4d90f5a57c71587984c817cc3ba1e6d88618f6da9f781`
- File size: `132801280`

### Runtime

Validation was performed in the MRI3D environment:

- Python: `/home/sygxdg/miniconda3/envs/MRI3D/bin/python`
- `torch`: `2.6.0+cu124`
- `torchvision`: `0.21.0+cu124`
- `SimpleITK`, `nibabel`, `PIL`, and `numpy` are available
- execution is CPU-only for this candidate path

## 4. Input / Preprocessing Contract

The minimal runner accepts explicit input references only:

- `trace_id`
- `case_id`
- `input_asset_id`
- `storage_uri`
- `modality = ct_image`
- `source_type`
- `deidentified`
- `not_for_diagnosis`
- `enable_real_shadow`

### Supported input modes

1. `source_type = synthetic`
   - the runner can use a synthetic tensor or a synthetic NIfTI fixture
   - this is the safest validation path
2. `source_type = deidentified`
   - the runner can read an explicitly referenced `.nii` or `.nii.gz` path
   - no directory scanning or path guessing is allowed

### Preprocessing summary

- input rank: 3D volume
- dtype: `float32`
- normalization: z-score
- resize target: `96 x 96 x 96`
- channel layout: channel-first
- batch size: 1
- concurrency: 1

## 5. Validation Result

Independent runner validation produced:

### Artifact check

- hash match: `true`
- exact weight loaded only after hash check

### Synthetic NIfTI forward

- input source: synthetic NIfTI fixture
- raw input shape: `[48, 52, 56]`
- preprocessed shape: `[1, 1, 96, 96, 96]`
- forward output shape: `[1, 2]`
- candidate label: `COP`
- probabilities:
  - `CAP = 0.277926`
  - `COP = 0.722074`

### Disabled compatibility path

The legacy disabled path still returns:

- `status = disabled`
- `error.code = imaging_runner_not_loaded`

## 6. Output Schema

Successful shadow output includes:

- `status = success`
- `candidate_label`
- `probabilities`
- `confidence`
- `uncertainty`
- `logits`
- `label_mapping`
- `artifact_hash`
- `preprocessing_summary`
- `runtime_env`
- `not_for_diagnosis = true`
- `real_inference = true`
- `shadow_only = true`

Failure output includes:

- `status = failed`
- `error_code`
- `error_message`
- `not_for_diagnosis = true`

## 7. Backend / Frontend Impact

### Backend C11 bridge

No backend change was made in this stage.

The existing bridge can continue to use the disabled path as-is until a later decision is made to route explicit `enable_real_shadow=true` requests.

### Frontend C12

No frontend change was made in this stage.

The existing shadow / audit display can continue to show disabled-state behavior until a later bridge decision exposes the success path.

## 8. Safety Boundary

This stage does **not**:

- use real patient imaging,
- batch run inference,
- change database schema,
- run Alembic,
- train or fine-tune,
- write trace / evidence,
- promote the model to default or canary,
- enable any silent fallback.

## 9. Next Step Recommendation

The next safe step is a bridge planning stage that decides whether the backend should keep the disabled-only path or explicitly allow shadow candidate mode via a separate gate.

