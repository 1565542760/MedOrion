# Coursework Stage C17: CAP/COP Multimodal ResNet18 Provenance + Runner Compatibility Plan

Scope: this stage is a read-only provenance and compatibility plan for the CAP/COP multimodal ResNet18 route. It does **not** implement a runner, does **not** load model weights, does **not** run real inference, and does **not** change backend or frontend code.

## 1. Files Read

Read-only inspection was performed on:

1. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/`
2. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/source_manifest.json`
3. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/Best_Metrics_Summary.csv`
4. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_imaging_resnet18_runner.py`
5. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`
6. `/home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C13_IMAGING_RESNET18_REAL_RUNNER_PREFLIGHT.md`
7. `/home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C14_IMAGING_RESNET18_REAL_SHADOW_RUNNER_MINIMAL_CANDIDATE.md`

## 2. Artifact / Provenance Evidence

### Family contents confirmed

The multimodal artifact family contains:

- `weights/`
- `logs/`
- `notebooks/`
- `preprocess_artifacts/`
- `feature_schema.json`

Notably, there is **no family-local `README.md`** in this directory tree, and there is no family-local `provenance/` subfolder. That is a provenance gap compared with the imaging family.

### Exact weight path and fold selection

All five fold weights are present:

- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold1_best.pth`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold2_best.pth`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold3_best.pth`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold4_best.pth`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold5_best.pth`

The strongest fold by the shared provenance metrics for `ResNet_Multimodal_Big` is **Fold_1**:

- AUC: `0.943076923076923`
- ACC: `0.8431372549019608`
- SE: `1.0`
- SP: `0.6923076923076923`

Therefore, the most defensible exact artifact candidate to cite first is:

`/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold1_best.pth`

Verified file metadata for that exact artifact:

- SHA256: `f17a4ed6f1f2f4b5e5c0d793a536b4b6e73d154ad2f5578fd844ae041967c809`
- File size: `132814281` bytes

### Label mapping

The multimodal family uses the same binary label mapping:

- `CAP = 0`
- `COP = 1`

### Provenance evidence

The shared provenance root confirms:

- source root: `/home/sygxdg/MRI3DModel`
- imaging family source tree: `/home/sygxdg/MRI3DModel/3d_classification/bigdata/restnet`
- metrics summary file exists and records `ResNet_Multimodal_Big`

The multimodal family also ships a `manifest.json` at the staged root, which records the exact weight and notebook paths for the family, but it does not by itself remove the need for careful input-contract review.

## 3. Runtime Dependency Conclusion

The MRI3D conda environment can import the runtime stack needed for a future multimodal runner:

- `torch 2.6.0+cu124`
- `torchvision 0.21.0+cu124`
- `monai 1.5.2`
- `SimpleITK 2.5.3`
- `nibabel 5.4.2`
- `PIL 12.2.0`
- `numpy 2.4.4`

That is sufficient for:

- 3D imaging preprocessing,
- clinical tabular preprocessing,
- a later controlled runner candidate,
- CPU-only smoke testing.

## 4. Input Contract: Known vs Unknown

### What is known

The notebook shows a multimodal model with:

- a 3D ResNet18 image branch,
- a 36-feature clinical branch,
- attention-based feature fusion,
- a 2-class classifier head.

The notebook explicitly uses:

- image shape target `IMG_SIZE = (96, 96, 96)`
- image loading via `nibabel`
- per-volume z-score normalization
- `ScaleIntensity()`
- `Resize(IMG_SIZE)`
- `BATCH_SIZE = 1`
- `n_clinical = 36`

The clinical preprocessing artifact confirms:

- `feature_count = 36`
- the 36-feature order includes `Striated_shadow.1` as the last feature
- `Striated_shadow.1` exists because the pandas/CSV behavior preserved a duplicate-column training artifact
- missing values are handled by median fill after numeric coercion
- StandardScaler parameters were derived in the preprocessing artifact

### What is unknown and must not be guessed

The following are not safe to invent from the current evidence:

- the final product-layer clinical input order if it differs from the artifact order,
- whether the runtime should accept a different clinical input abstraction than the 36-feature artifact order,
- the exact missing/default policy for clinical fields in a new runner,
- the exact spacing / orientation policy for the imaging branch,
- the exact fusion behavior outside the notebook-level attention fusion,
- whether segmentation is part of inference (the notebook uses seg only for training guidance),
- whether `case_model_input_snapshot` or `case_imaging_inputs` already map directly into the multimodal contract without a translation layer.

## 5. Relationship to Clinical MLP Schema_Unverified

The multimodal route is related to the clinical MLP work, but it is **not** the same thing.

### Reuse that is supported

- The multimodal branch can reuse the same `clinical_tabular_standardization_v1.json` artifact.
- It can reuse the same 36-feature clinical ordering, including `Striated_shadow.1`.
- It can reuse the same CAP/COP label mapping.

### What still cannot be claimed

The product-layer clinical schema is still marked `schema_unverified` in the broader project context. So:

- the multimodal route must not turn that product-layer shape into a global truth,
- the multimodal runner should treat the 36-feature artifact as a model-level contract,
- a translation layer may still be needed if the UI or backend presents a different clinical input form.

In other words, the multimodal model can reuse the 36-feature artifact, but the product schema remains a separate boundary.

## 6. Relationship to Imaging ResNet18 Runner

### Reuse that is supported

- imaging-style 3D preprocessing is a good starting point,
- the same NIfTI / `float32` / `96x96x96` image handling appears in the notebook,
- the runner can likely reuse the same CPU-first, batch=1, no-silent-fallback discipline,
- the same `trace_id` / explicit reference pattern is still appropriate.

### What cannot be reused blindly

- the multimodal model is not image-only,
- it should not reuse the imaging runner’s output schema without adding the clinical branch context,
- it should not assume a single-image-only bridge contract is enough,
- it should not assume the imaging spacing/orientation assumptions are already validated for multimodal use.

## 7. Recommended Runner Design

The future multimodal runner should be designed as a dual-input controlled candidate:

- image input: explicit `storage_uri` / `input_asset_id`
- clinical input: explicit model-level feature mapping reference, not a universal case-table assumption
- modality scope: `ct_image + clinical_table`
- preprocessing: image branch + clinical artifact branch
- execution: CPU-first, batch=1, single process, `torch.no_grad()`, `eval()`

### Suggested request contract

- `trace_id`
- `case_id`
- `patient_id` only if the enclosing contract permits it
- `image_input_ref` or `input_asset_id`
- `clinical_input_ref` or `model_input_snapshot_ref`
- `clinical_feature_mapping_id`
- `storage_uri`
- `source_type`
- `modality_scope`
- `deidentified`
- `not_for_diagnosis`
- `enable_real_shadow`
- `runtime_options`

### Suggested output contract

- `status`
- `trace_id`
- `case_id`
- `model_version_id`
- `artifact_hash`
- `label_mapping`
- `candidate_label`
- `probabilities`
- `confidence`
- `uncertainty`
- `fusion_summary`
- `preprocessing_summary`
- `limitations`
- `runtime_env`
- `not_for_diagnosis = true`
- `shadow_only = true`

### Runner guardrails

- exact artifact path only,
- exact hash check before load,
- no directory scanning,
- no silent fallback,
- no default / canary activation,
- no real patient inference without an explicit approved input reference.

## 8. Backend Bridge Plan

The backend bridge should not assume the multimodal route is already a drop-in replacement for imaging or clinical shadow flows.

Recommended bridge shape:

- a dedicated multimodal shadow endpoint,
- explicit capability validation for `ct_image + clinical_table`,
- explicit model version selection,
- explicit shadow-only status emission,
- no silent fallback if either branch is missing.

The bridge should preserve `trace_id` and keep the multimodal flow distinct from imaging-only and clinical-only bridges.

## 9. Frontend / Digital Twin Plan

The frontend should present multimodal output as a fused support signal, not as a diagnosis.

Recommended UX shape:

- an imaging pane,
- a clinical summary pane,
- a fusion / confidence pane,
- a digital twin state panel showing the combined case state,
- a clear shadow / not-for-diagnosis label.

For the digital twin, the multimodal route should update:

- image-derived state,
- clinical-derived state,
- fused candidate label,
- uncertainty,
- provenance,
- review requirement.

It should not claim that the system has a finished universal case schema.

## 10. C18 Recommendation

Yes, C18 is reasonable as a **runner prototype** stage, but only after the missing input-contract questions are answered explicitly.

C18 should focus on:

1. the multimodal runner skeleton,
2. the exact clinical feature mapping contract,
3. the exact image reference contract,
4. the output schema,
5. the bridge wiring for a controlled shadow candidate.

## 11. Compliance Boundary

This stage does **not**:

- load model weights,
- `torch.load`,
- train,
- run real inference,
- read real patient images,
- scan unknown directories,
- copy or move model files,
- write recommendation / trace / evidence,
- alter database schema,
- execute Alembic,
- enable default or canary.

