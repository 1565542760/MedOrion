# Coursework Stage C13: CAP/COP Imaging ResNet18 Real Shadow Runner Preflight

Scope: this stage performs a strict preflight for moving the CAP/COP imaging ResNet18 route from a disabled prototype toward a controlled real shadow runner plan. This is still a planning and verification stage only. It does **not** read real patient images, does **not** run large-scale inference, and does **not** promote the model to default or canary.

## 1. Files Read

Read-only inspection was performed on:

1. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_imaging_resnet18_runner.py`
2. `/home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C9_IMAGING_RESNET18_ARTIFACT_PREFLIGHT.md`
3. `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C7_IMAGING_RESNET18_RUNNER_ADAPTER_PLAN.md`
4. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/README.md`
5. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/notebooks/restnet.ipynb`
6. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/logs/fold5_unimodal_log.csv`
7. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/preprocess_config.json`
8. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/dcmtonii_N4.py`
9. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/source_manifest.json`
10. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/Best_Metrics_Summary.csv`

## 2. Artifact / Provenance Evidence

### Confirmed exact artifact

- Weight file: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth`
- SHA256: `892fd836b0f361ca6ed4d90f5a57c71587984c817cc3ba1e6d88618f6da9f781`
- File size: `132801280` bytes

### Provenance evidence

- The staged artifact family exists under `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/`
- `README.md` states the folder is metadata/artifact staging only, no load, no real inference, and no training during staging
- `source_manifest.json` links the imaging family to the original research root `/home/sygxdg/MRI3DModel/3d_classification/restnet_classifaction`
- `preprocess_config.json` states the imaging preprocessing logic is based on:
  - nibabel loading of NIfTI,
  - `float32`,
  - z-score normalization when `std > 1e-5`,
  - adding a channel dimension,
  - MONAI `ScaleIntensity` + `Resize(IMG_SIZE)`
- `preprocess_config.json` also confirms the label mapping:
  - `0 = CAP`
  - `1 = COP`

### Architecture evidence

The notebook evidence supports a 3D MONAI ResNet18-style route:

- `IMG_SIZE = (96, 96, 96)`
- `BATCH_SIZE = 1`
- `nibabel` is used to read NIfTI volumes
- `Resize(IMG_SIZE)` is used in preprocessing
- `ScaleIntensity()` is used in preprocessing
- the model is built as a 3D ResNet family with `spatial_dims=3`
- the route is still CAP vs COP binary classification

## 3. Runtime Dependency Evidence

### MRI3D conda environment

The MRI3D runtime can import:

- `torch` `2.6.0+cu124`
- `torchvision` `0.21.0+cu124`
- `SimpleITK` `2.5.3`
- `nibabel` `5.4.2`
- `PIL` `12.2.0`
- `numpy` `2.4.4`

This is enough for:

- controlled tensor smoke tests,
- NIfTI I/O,
- image preprocessing,
- later CPU-only or GPU-guarded inference experiments.

### Current service containers

The current `model-service` and `backend` containers do not expose `torch`, which is consistent with the current metadata-only / disabled route and does not block a future controlled runner plan.

## 4. Preprocessing and Input Contract

### What is already known

For the imaging ResNet18 family, the most defensible current input contract is:

- modality: CT / NIfTI-style imaging
- file type: NIfTI (`.nii` / `.nii.gz`) for the runner contract
- dtype: `float32`
- channel layout: channel-first, e.g. `(1, D, H, W)`
- target image size: `IMG_SIZE = (96, 96, 96)`
- normalization: z-score style normalization in preprocessing
- resize: MONAI `Resize(IMG_SIZE)`
- label mapping: `CAP=0`, `COP=1`

### What remains unknown or not yet safely frozen

The following still need explicit finalization before any real shadow launch:

- exact interpolation mode used by resize,
- any spacing / resampling policy beyond the notebook-level resize,
- whether orientation normalization is required,
- whether the runtime should accept 2D demo images in addition to 3D volumes,
- whether heatmap outputs are required for the first real shadow phase,
- exact runtime budget for per-case shadow inference,
- final error-code mapping for a loaded real adapter.

### Recommended contract boundary

The runner should accept only explicitly referenced imaging inputs:

- `trace_id`
- `case_id`
- `patient_id` only if allowed by the enclosing contract
- `input_asset_id`
- `storage_uri`
- `modality = ct_image`
- `source_type`
- `deidentified = true`
- `not_for_diagnosis = true`
- `runtime_options`
- `idempotency_key`

It should not:

- scan directories,
- infer the correct series from neighboring files,
- substitute another scan,
- read raw patient data without the explicit reference path.

## 5. Can We Enter Real Shadow Inference?

### Decision

Yes, **conditionally**, for a controlled shadow implementation plan.

### Why the evidence is sufficient

We now have:

1. an exact weight path,
2. a verified SHA256,
3. a confirmed file size,
4. a notebook-backed 3D MONAI preprocessing path,
5. explicit CAP/COP label mapping,
6. MRI3D runtime dependency availability,
7. a disabled runner prototype that already enforces the contract boundary,
8. a backend bridge that already consumes the prototype state.

### What this does **not** mean

This does **not** mean the model is clinically validated or ready for default use.
It only means the project has enough provenance and runtime evidence to design a controlled real shadow runner stage.

## 6. Minimal Runner Implementation Plan

If the team proceeds to a real shadow runner later, the minimal implementation should do the following:

1. Parse the same explicit reference request contract already used by the prototype.
2. Validate `trace_id`, `case_id`, `input_asset_id`, `storage_uri`, `modality`, `deidentified`, and `not_for_diagnosis`.
3. Resolve only the exact artifact path.
4. Verify `sha256` before load.
5. Load the model only in a guarded, controlled path.
6. Use `torch.no_grad()` and `model.eval()`.
7. Accept only a synthetic or explicitly permitted demo tensor for smoke testing before any real patient ingress.
8. Keep output strictly shadow-only and non-diagnostic.

### Minimal runtime assumptions

- CPU-first by default
- batch size = 1
- no silent fallback
- no default promotion
- no canary
- no trace/evidence writes unless the later bridge contract explicitly asks for them

### Candidate output fields

The future shadow runner should emit at least:

- `trace_id`
- `case_id`
- `input_asset_id`
- `model_version_id`
- `artifact_hash`
- `adapter_code`
- `candidate_label`
- `probability`
- `confidence`
- `uncertainty`
- `limitations`
- `runtime_env`
- `not_for_diagnosis = true`

Optional later fields:

- `heatmap_reference`
- `region_state_summary`
- `shadow_run_id`

## 7. Blockers Remaining Before Live Shadow Execution

The remaining blockers are operational, not conceptual:

1. final shadow-adapter enable switch,
2. explicit image storage / ingestion path selection,
3. real shadow-audit emission contract,
4. final timeout and retry semantics,
5. explicit policy for whether the first shadow phase writes trace/evidence or stays read-only,
6. a deliberate decision about demo-image support versus NIfTI-only support.

## 8. Backend C11 Bridge Impact

The C11 bridge can already call the prototype and receive disabled-state responses.

For a future real runner:

- the bridge should continue to pass `trace_id` through unchanged,
- the bridge should stop treating `imaging_runner_not_loaded` as the terminal state once the real runner is enabled,
- the bridge will need to map real shadow outputs into the existing case-level shadow view without implying diagnosis,
- bridge code should still enforce no-silent-fallback semantics.

## 9. Frontend C12 Impact

The existing C12 UI can already display imaging bridge state.

For a future real runner, the frontend may need to surface:

- candidate label,
- probability/confidence,
- uncertainty,
- limitations,
- artifact hash,
- runtime environment,
- shadow/not-for-diagnosis state,
- optional heatmap or region-state links.

The UI must continue to present this as shadow support, not a formal diagnosis.

## 10. Compliance Boundary

This stage does **not**:

- read real patient images,
- run large-scale inference,
- train or fine-tune any model,
- `torch.load` any weight in this stage,
- scan or copy model directories,
- modify database schema,
- execute Alembic,
- write recommendation, trace, or evidence entries,
- enable default or canary,
- claim clinical validation.

## 11. Next Step Recommendation

The safest next stage is a controlled real-runner design stage that finalizes:

1. exact image ingress contract,
2. exact inference response schema,
3. shadow-audit emission scope,
4. whether a synthetic demo tensor is used for first smoke test,
5. whether the first real shadow execution is CPU-only or allowed to observe CUDA availability only.

