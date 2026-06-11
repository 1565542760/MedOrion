# Coursework Stage C18: CAP/COP Multimodal ResNet18 Controlled Runner Prototype

Scope: this stage introduces a controlled multimodal runner prototype for CAP/COP that can execute a single synthetic shadow inference path with exact fold1 artifact verification. It does **not** touch backend or frontend code, does **not** change database state, and does **not** use real patient images.

## 1. Files Read

Read-only inspection was performed on:

1. `/home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C17_MULTIMODAL_RESNET18_PROVENANCE_AND_RUNNER_PLAN.md`
2. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/feature_schema.json`
3. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json`
4. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/notebooks/restnet_training_array_nii_notpre_add_label_mut.ipynb`
5. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_imaging_resnet18_runner.py`
6. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`

## 2. Artifact / Provenance Basis

The controlled multimodal runner is built around the exact fold1 candidate:

- Path: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold1_best.pth`
- SHA256: `f17a4ed6f1f2f4b5e5c0d793a536b4b6e73d154ad2f5578fd844ae041967c809`
- File size: `132814281`

The shared provenance evidence confirms:

- label mapping: `CAP = 0`, `COP = 1`
- image branch: 3D NIfTI, `float32`, `96x96x96`
- clinical branch: 36-feature artifact order
- fusion: `AttentionFusion(dim_img=32, dim_clin=32)`

## 3. Runner Prototype Summary

The prototype now supports two modes:

### Disabled compatibility mode

If `enable_real_shadow` is absent or false, the runner remains shadow-disabled and returns a disabled response. This preserves a safe bridge-compatible fallback without silently activating inference.

### Controlled real-shadow prototype mode

If `enable_real_shadow=true`, the runner:

1. validates exact artifact path,
2. computes SHA256 before load,
3. loads the exact fold1 weight on CPU,
4. instantiates the multimodal ResNet18 + AttentionFusion architecture,
5. loads the state dict strictly,
6. preprocesses a synthetic NIfTI image fixture,
7. preprocesses an exact-order 36-feature clinical payload using the artifact parameters,
8. performs one `torch.no_grad()` forward pass,
9. returns a shadow-only JSON result.

## 4. Input Contract

The prototype requires:

- `trace_id`
- `case_id`
- `not_for_diagnosis=true`
- `shadow_only=true`
- `source_type=synthetic`
- `storage_uri` or `image_path`
- `clinical_features`
- optional `model_version_id` that is echoed back if supplied

### Clinical branch contract

The runner uses the artifact order from:

- `feature_schema.json`
- `preprocess_artifacts/clinical_tabular_standardization_v1.json`

The runner treats the 36-feature order as the model-level contract and fails fast if a feature is missing or unexpectedly named.

### Imaging branch contract

The runner only accepts an explicit `.nii` or `.nii.gz` synthetic fixture path. It performs:

- nibabel load
- float32 conversion
- 3D z-score normalization
- resize to `96x96x96`
- channel-first conversion to `[1,1,96,96,96]`

## 5. Clinical Preprocessing Result

The artifact-backed clinical preprocessing:

- preserves the 36-feature order,
- applies `x_scaled = (x - mean) / scale`,
- uses the persisted mean/scale statistics from the preprocessing artifact,
- fails immediately on missing features,
- does not silently substitute defaults.

The 36th feature is `Striated_shadow.1`, which is intentionally part of the artifact order.

## 6. Output Schema

### Success output

The success JSON includes:

- `status=success`
- `candidate_label`
- `probabilities={CAP, COP}`
- `confidence`
- `uncertainty`
- `logits`
- `label_mapping`
- `artifact_hash`
- `image_preprocessing_summary`
- `clinical_preprocessing_summary`
- `fusion_architecture`
- `not_for_diagnosis=true`
- `shadow_only=true`
- `real_inference=true`
- `source_type=synthetic`

### Failure output

The failure JSON includes:

- `status=failed`
- `error_code`
- `error_message`
- `not_for_diagnosis=true`

## 7. Backend / Frontend Impact

No backend or frontend changes are made in this stage.

The prototype is intentionally independent so it can be validated before any later bridge wiring.

## 8. Validation Plan

The prototype should be validated by:

1. `python -m py_compile app/model-runners/cap_cop_multimodal_resnet18_runner.py`
2. exact fold1 artifact hash check
3. synthetic NIfTI fixture forward
4. synthetic artifact-order clinical JSON forward

If those pass, the runner candidate is ready for a later bridge discussion.

## 9. Safety Boundary

This stage does **not**:

- read real patient images,
- scan directories,
- copy or move model files,
- train or fine-tune,
- write trace / evidence / recommendation,
- alter database schema,
- execute Alembic,
- enable default or canary,
- claim clinical diagnosis capability.

## 10. Next Step Recommendation

If validation succeeds, the next stage can focus on a controlled bridge plan for exposing the multimodal candidate behind an explicit shadow switch and a translation layer for clinical input references.
