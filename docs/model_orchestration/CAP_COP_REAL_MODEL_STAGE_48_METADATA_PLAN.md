# MedOrion CAP/COP Real Model Stage 48 Metadata Registration Plan

Last updated: 2026-06-03 Asia/Shanghai
Owner thread: MedOrion real-model artifact documentation and metadata registration
Scope: Stage 48 documents the isolated CAP/COP artifact staging directory and prepares metadata registration plans for later registry entry. This stage does not load `.pth`, does not train, does not infer, does not enable GPU, does not copy datasets, does not scan original research folders, does not change database schema, and does not execute Alembic.

## 0. Scope and Non-Goals

Stage 48 goals:
1. Document the isolated CAP/COP agent artifact directory.
2. Fix the three submodel identities and their usage boundaries.
3. Summarize weight files, notebooks, logs, and preprocessing artifacts from the isolated staging directory.
4. Prepare metadata registration plans for later model registry onboarding.
5. Preserve the current `metadata_only=true` and `artifact_not_loaded=true` status.
6. Keep `not_for_diagnosis` as the active safety posture.
7. Define the next step toward registry-ready metadata without enabling real inference.

Stage 48 non-goals:
1. Do not load any model artifact.
2. Do not train.
3. Do not run inference.
4. Do not enable GPU.
5. Do not copy datasets.
6. Do not scan the original `/home/sygxdg/MRI3DModel` research tree.
7. Do not change database schema.
8. Do not execute Alembic.
9. Do not enable Nginx.
10. Do not promote any model to default.

## 1. CAP/COP Agent Directory Structure

Agent family root:
1. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0`

Observed top-level substructure:
1. `clinical_mlp/`
2. `imaging_resnet18_unimodal/`
3. `multimodal_resnet18_bigdata/`
4. `preprocessing/`
5. `provenance/`
6. `manifest.json`
7. `label_mapping.json`
8. `README.md`

Important staging note:
1. This directory is already isolated for MedOrion staging.
2. It is not the original research tree.
3. It is intended to become metadata-addressable through model registry.

## 2. Three Model Boundaries

All three models belong to the same disease-agent family:
1. `cap_cop_classifier_agent`

All three solve the same disease task:
1. CAP/COP binary classification

But they have different input and runtime boundaries.

### 2.1 `clinical_mlp_cap_cop_classifier`

Purpose:
1. Pure clinical tabular MLP.

Boundary:
1. Input is clinical CSV/tabular features only.
2. Uses clinical preprocessing parameters.
3. Must not depend on CT image tensors.
4. Must not depend on multimodal fusion logic.

### 2.2 `imaging_resnet18_cap_cop_classifier`

Purpose:
1. Pure CT image ResNet18.

Boundary:
1. Input is CT/NIfTI image only.
2. Does not use clinical StandardScaler.
3. Must not require the 36-feature clinical table.
4. Must not depend on tabular feature preprocessing.

### 2.3 `multimodal_resnet18_cap_cop_classifier`

Purpose:
1. CT image plus clinical table multimodal ResNet18.

Boundary:
1. Input is CT/NIfTI image plus 36 clinical features.
2. Uses clinical preprocessing parameters.
3. Must preserve image and tabular branches separately before fusion.
4. Must not be conflated with pure image or pure clinical models.

## 3. Label Mapping

CAP/COP label mapping is fixed as follows:
1. `CAP = 0`
2. `COP = 1`

Safety note:
1. This label mapping is for registry documentation and later contract binding.
2. It does not mean the model is loaded or activated.

## 4. Clinical Feature Contract

Clinical feature count for the CAP/COP clinical and multimodal models is fixed at:
1. `36`

Feature-contract note:
1. The isolated preprocessing artifact defines the inference-time tabular schema.
2. The `Striated_shadow.1` duplicate column is the canonical pandas-mangled duplicate that must be retained in the inference schema.
3. Production preprocessing must preserve the exact column order and duplicate-column handling behavior described by the staging artifact.

### 4.1 Duplicate-column handling logic

Observed pandas behavior summary:
1. The original source headers include a duplicate `Striated_shadow` column in the CAP/COP source data lineage.
2. When pandas reads the source, it preserves a mangled duplicate as `Striated_shadow.1`.
3. The inference schema therefore explicitly includes `Striated_shadow.1` as a distinct 36th feature.
4. The registry plan must record this as a schema rule, not as a bug to silently ignore.

### 4.2 Preprocessing parameter artifact

Required preprocessing parameter file:
1. `clinical_tabular_standardization_v1.json`

Purpose:
1. Encodes the tabular StandardScaler and imputation contract for clinical and multimodal models.
2. Must be registered as metadata, not treated as an executable model artifact.

## 5. Artifact Inventory Summary

### 5.1 Clinical MLP artifact summary

Root folder:
1. `clinical_mlp/`

Weights:
1. `clinical_mlp/weights/fold1_best.pth`
2. `clinical_mlp/weights/fold2_best.pth`
3. `clinical_mlp/weights/fold3_best.pth`
4. `clinical_mlp/weights/fold4_best.pth`
5. `clinical_mlp/weights/fold5_best.pth`

Notebook:
1. `clinical_mlp/notebooks/clinical_MLP.ipynb`

Training logs:
1. `clinical_mlp/logs/fold1_training_log.csv`
2. `clinical_mlp/logs/fold2_training_log.csv`
3. `clinical_mlp/logs/fold3_training_log.csv`
4. `clinical_mlp/logs/fold4_training_log.csv`
5. `clinical_mlp/logs/fold5_training_log.csv`

Preprocessing artifact:
1. `clinical_mlp/preprocess_artifacts/clinical_tabular_standardization_v1.json`

Feature schema:
1. `clinical_mlp/feature_schema.json`

### 5.2 Imaging ResNet18 artifact summary

Root folder:
1. `imaging_resnet18_unimodal/`

Weights:
1. `imaging_resnet18_unimodal/weights/fold1_best_unimodal.pth`
2. `imaging_resnet18_unimodal/weights/fold2_best_unimodal.pth`
3. `imaging_resnet18_unimodal/weights/fold3_best_unimodal.pth`
4. `imaging_resnet18_unimodal/weights/fold4_best_unimodal.pth`
5. `imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth`

Notebook:
1. `imaging_resnet18_unimodal/notebooks/restnet.ipynb`

Training logs:
1. `imaging_resnet18_unimodal/logs/fold1_unimodal_log.csv`
2. `imaging_resnet18_unimodal/logs/fold2_unimodal_log.csv`
3. `imaging_resnet18_unimodal/logs/fold3_unimodal_log.csv`
4. `imaging_resnet18_unimodal/logs/fold4_unimodal_log.csv`
5. `imaging_resnet18_unimodal/logs/fold5_unimodal_log.csv`

### 5.3 Multimodal ResNet18 artifact summary

Root folder:
1. `multimodal_resnet18_bigdata/`

Weights:
1. `multimodal_resnet18_bigdata/weights/fold1_best.pth`
2. `multimodal_resnet18_bigdata/weights/fold2_best.pth`
3. `multimodal_resnet18_bigdata/weights/fold3_best.pth`
4. `multimodal_resnet18_bigdata/weights/fold4_best.pth`
5. `multimodal_resnet18_bigdata/weights/fold5_best.pth`

Notebook:
1. `multimodal_resnet18_bigdata/notebooks/restnet_training_array_nii_notpre_add_label_mut.ipynb`

Training logs:
1. `multimodal_resnet18_bigdata/logs/fold1_training_log.csv`
2. `multimodal_resnet18_bigdata/logs/fold2_training_log.csv`
3. `multimodal_resnet18_bigdata/logs/fold3_training_log.csv`
4. `multimodal_resnet18_bigdata/logs/fold4_training_log.csv`
5. `multimodal_resnet18_bigdata/logs/fold5_training_log.csv`

Preprocessing artifact:
1. `multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json`

Feature schema:
1. `multimodal_resnet18_bigdata/feature_schema.json`

## 6. Metadata-Only Status

Current staging status is explicitly:
1. `metadata_only=true`
2. `artifact_not_loaded=true`
3. `not_for_diagnosis`

Meaning:
1. The artifacts are documented for later registry entry.
2. The artifacts are not yet activated by MedOrion.
3. No real inference is enabled.
4. The directory is ready for metadata planning, not for production use.

## 7. Model Registry Metadata Registration Plan

This section proposes registry-ready metadata for the three CAP/COP models.

### 7.1 Clinical MLP registration plan

- `model_name`: `clinical_mlp_cap_cop_classifier`
- `disease_agent`: `cap_cop_classifier_agent`
- `disease_task`: `CAP/COP binary classification`
- `model_version_id`: `cap_cop_classifier_agent_v1.0.0_clinical_mlp`
- `version_label`: `v1.0.0-clinical-mlp`
- `artifact_type`: `.pth`
- `artifact_uri`: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold5_best.pth` or another approved fold-level artifact selected by registry policy
- `artifact_hash`: use the manifest-recorded fold hash or pending hash verification if the registry process requires revalidation on the exact path
- `adapter_type`: `clinical_tabular_cpu_adapter`
- `preprocess_schema_version`: `clinical_tabular_standardization_v1`
- `postprocess_schema_version`: `cap_cop_binary_output_v1`
- `runtime_constraints`: `cpu-first, batch=1, concurrency=1, timeout governed, no GPU until separately approved`
- `limitations`: `clinical-only; requires stable tabular schema; not image-aware; not for diagnosis`
- `safety_notes`: `CAP/COP assistive classification only; output must remain advisory and trace-bound`

### 7.2 Imaging ResNet18 registration plan

- `model_name`: `imaging_resnet18_cap_cop_classifier`
- `disease_agent`: `cap_cop_classifier_agent`
- `disease_task`: `CAP/COP binary classification`
- `model_version_id`: `cap_cop_classifier_agent_v1.0.0_imaging_resnet18`
- `version_label`: `v1.0.0-imaging-resnet18`
- `artifact_type`: `.pth`
- `artifact_uri`: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth` or another approved fold-level artifact selected by registry policy
- `artifact_hash`: use the manifest-recorded fold hash or pending hash verification if the registry process requires revalidation on the exact path
- `adapter_type`: `ct_nifti_resnet18_cpu_adapter`
- `preprocess_schema_version`: `ct_nifti_unimodal_v1`
- `postprocess_schema_version`: `cap_cop_binary_output_v1`
- `runtime_constraints`: `cpu-first, batch=1, concurrency=1, no clinical StandardScaler, timeout governed`
- `limitations`: `CT/NIfTI only; not tabular; not multimodal; not for diagnosis`
- `safety_notes`: `CAP/COP assistive classification only; output must remain advisory and trace-bound`

### 7.3 Multimodal ResNet18 registration plan

- `model_name`: `multimodal_resnet18_cap_cop_classifier`
- `disease_agent`: `cap_cop_classifier_agent`
- `disease_task`: `CAP/COP binary classification`
- `model_version_id`: `cap_cop_classifier_agent_v1.0.0_multimodal_resnet18`
- `version_label`: `v1.0.0-multimodal-resnet18`
- `artifact_type`: `.pth`
- `artifact_uri`: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold5_best.pth` or another approved fold-level artifact selected by registry policy
- `artifact_hash`: use the manifest-recorded fold hash or pending hash verification if the registry process requires revalidation on the exact path
- `adapter_type`: `ct_nifti_plus_clinical_tabular_cpu_adapter`
- `preprocess_schema_version`: `clinical_tabular_standardization_v1 + ct_nifti_multimodal_v1`
- `postprocess_schema_version`: `cap_cop_binary_output_v1`
- `runtime_constraints`: `cpu-first, batch=1, concurrency=1, timeout governed, no GPU until separately approved`
- `limitations`: `requires both image and 36-feature clinical table; not image-only; not clinical-only; not for diagnosis`
- `safety_notes`: `CAP/COP assistive classification only; output must remain advisory and trace-bound`

### 7.4 Relationship summary

1. All three models belong to `cap_cop_classifier_agent`.
2. Each model has its own `model_name`, `model_version_id`, and `adapter_type`.
3. The unified agent gateway or orchestration layer may choose among them by disease task and modality.
4. They must not be collapsed into one undifferentiated artifact entry.

## 8. Registry Readiness Plan

Before these three models can enter the MedOrion registry later, the following must be available:
1. exact `artifact_uri` selection for each model version
2. artifact hash verification on the chosen exact file path
3. registry metadata record for each version
4. offline evaluation summary references
5. adapter contract version references
6. safety notes and limitations
7. trace/evidence linkage plan

## 9. Safety and Boundaries

1. No `.pth` is loaded in Stage 48.
2. No dataset is copied into MedOrion from the original research tree.
3. No original research directory scan is performed beyond the isolated staging folder.
4. No training or inference is executed.
5. No model is promoted to default.
6. No real diagnosis claim is made.

## 10. Stage 49 Recommendation

Stage 49 should focus on registry packaging and hash-verification preparation, but only after exact artifact-path authorization is available.

Recommended Stage 49 work:
1. finalize registry record shapes for the three CAP/COP versions
2. confirm exact artifact selection for onboarding
3. prepare hash verification bookkeeping
4. prepare preflight checks for later adapter enablement
5. keep all logic metadata-only until the user explicitly authorizes artifact onboarding

## 11. Main-Controller Writeback Summary

1. Stage 48 CAP/COP artifact documentation and metadata registration plan is created.
2. The three CAP/COP???? are fixed as `clinical_mlp_cap_cop_classifier`, `imaging_resnet18_cap_cop_classifier`, and `multimodal_resnet18_cap_cop_classifier`.
3. Each model has a distinct artifact path summary, notebook summary, and training log summary inside the isolated staging directory.
4. The feature contract is fixed at 36 clinical features, and `Striated_shadow.1` is the canonical pandas-mangled duplicate column.
5. The preprocessing artifact `clinical_tabular_standardization_v1.json` is documented as the shared clinical preprocessing parameter file for the clinical and multimodal models.
6. Stage 48 remains metadata-only, artifact-not-loaded, and not-for-diagnosis.
7. Stage 49 should focus on registry packaging and hash-verification readiness, but only after exact artifact-path authorization is available.
