# MedOrion CAP/COP Real Model Stage 49 Adapter Contract

Last updated: 2026-06-03 Asia/Shanghai
Owner thread: MedOrion real-model adapter and registry readiness
Scope: Stage 49 defines inference adapter contracts and registry-ready metadata drafts for the three CAP/COP models. This stage does not load `.pth`, does not train, does not infer, does not enable GPU, does not copy datasets, does not scan original research folders, does not change database schema, does not execute Alembic, does not enable Nginx, and does not mark any model as default/approved/promoted.

## 0. Scope and Non-Goals

Stage 49 goals:
1. Define inference adapter contracts for the clinical MLP, imaging ResNet18, and multimodal ResNet18 CAP/COP models.
2. Define registry-ready metadata drafts for later onboarding.
3. Define input and output schema expectations for each adapter.
4. Define preprocessing and postprocessing dependencies.
5. Define confidence, uncertainty, error, timeout, CPU-first, and trace/evidence requirements.
6. Define future call strategy options without implementing scheduling logic.
7. Preserve the current metadata-only, artifact-not-loaded, not-for-diagnosis posture.

Stage 49 non-goals:
1. Do not load any real model artifact.
2. Do not train.
3. Do not run inference.
4. Do not enable GPU.
5. Do not copy datasets.
6. Do not scan the original research tree.
7. Do not change database schema.
8. Do not execute Alembic.
9. Do not enable Nginx.
10. Do not mark any model as default.
11. Do not declare real diagnosis availability.

## 1. Goals

Stage 48 documented the isolated CAP/COP artifact staging directory and prepared metadata registration plans. Stage 49 adds the adapter contract layer that explains how each model would later be wrapped for MedOrion without actually enabling it.

Why this stage matters:
1. MedOrion needs an adapter boundary between registry metadata and inference-time request/response shapes.
2. Each CAP/COP model family has different modality expectations and preprocessing dependencies.
3. The system must know how to interpret outputs consistently before any later activation.
4. The registry must be able to store model, adapter, preprocessing, and postprocessing metadata together.
5. The platform must remain safe and explicit about not-for-diagnosis status.

## 2. Non Goals

1. No real artifact loading.
2. No `.pth` operations.
3. No training.
4. No automatic real-time training.
5. No GPU enablement.
6. No production deployment.
7. No database migration execution.
8. No silent fallback.
9. No promotion to default.
10. No diagnosis claims.

## 3. Shared CAP/COP Contract Invariants

These invariants apply to all three models.

1. Disease agent family: `cap_cop_classifier_agent`.
2. Disease task: CAP/COP binary classification.
3. Label mapping: `CAP = 0`, `COP = 1`.
4. Clinical feature count for clinical and multimodal adapters: `36`.
5. `Striated_shadow.1` must be preserved as the pandas-mangled duplicate column corresponding to CAP/COP source behavior.
6. Clinical and multimodal adapters must use `clinical_tabular_standardization_v1.json`.
7. Each adapter must remain assistive only and not for diagnosis.

## 4. Adapter Identity Rules

Each adapter must have its own adapter code and must not be collapsed into a single generic entry.

Required adapter codes:
1. `clinical_mlp_cap_cop_adapter`
2. `imaging_resnet18_cap_cop_adapter`
3. `multimodal_resnet18_cap_cop_adapter`

Rules:
1. Adapter code identifies the runtime contract wrapper, not the model artifact itself.
2. Model name identifies the model family/versioning entity.
3. Disease agent identifies the family owner.
4. Adapter type identifies the runtime integration path.

## 5. Clinical MLP Adapter Contract

### 5.1 Adapter identity

- `adapter_code`: `clinical_mlp_cap_cop_adapter`
- `model_name`: `clinical_mlp_cap_cop_classifier`
- `disease_agent`: `cap_cop_classifier_agent`
- `supported_task`: `CAP/COP binary classification`
- `supported_modalities`: `clinical_table`

### 5.2 Input schema

Input schema expectation:
1. Clinical tabular features only.
2. Uses the 36-feature clinical schema.
3. Expects the exact standardized feature order defined by `clinical_tabular_standardization_v1.json`.
4. Preserves `Striated_shadow.1` as the duplicate-column feature.
5. Does not require CT/NIfTI input.

Input schema draft fields:
1. `trace_id`
2. `inference_task_id`
3. `case_id`
4. `patient_id` nullable
5. `disease_agent`
6. `requested_task`
7. `clinical_context_refs`
8. `modality_refs`
9. `missing_value_context`
10. `runtime_options`
11. `idempotency_key`
12. `clinical_features`

### 5.3 Output schema

Output schema expectation:
1. `candidate_label`
2. `probability`
3. `confidence`
4. `uncertainty`
5. `limitations`
6. `input_quality_flags`
7. `missing_value_impact`
8. `recommended_next_actions_for_doctor_review`
9. `runtime_stub_or_real_adapter`

Output schema draft fields:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `model_version_id`
5. `model_id`
6. `disease_agent`
7. `task_type`
8. `status`
9. `outputs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `evidence_nodes_to_create`
14. `evidence_edges_to_create`
15. `trace_events_to_emit`
16. `error` nullable

### 5.4 Preprocessing dependency

Required dependency:
1. `clinical_tabular_standardization_v1.json`

Preprocessing rules:
1. numeric coercion with non-numeric values coerced explicitly
2. median imputation for missing tabular values as documented by the staging artifact
3. StandardScaler alignment with persisted parameters when real activation is later allowed
4. exact feature order preservation
5. duplicate-column preservation for `Striated_shadow.1`

### 5.5 Postprocessing rule

1. Map raw numeric output to CAP/COP label space.
2. Package confidence and uncertainty explicitly.
3. Include limitations and next-review actions.
4. Do not invent certainty beyond the model output.

### 5.6 Error codes

Required error codes:
1. `invalid_input`
2. `missing_required_input`
3. `unsupported_modality`
4. `model_not_found`
5. `model_version_not_approved`
6. `inference_timeout`
7. `resource_exhausted`
8. `dependency_unavailable`
9. `internal_error`
10. `trace_id_missing`

### 5.7 Runtime constraints

1. CPU-first.
2. batch = 1.
3. concurrency = 1.
4. timeout governed.
5. no GPU until separately approved.
6. no silent fallback.

### 5.8 Trace/evidence requirements

Must emit or carry:
1. `trace_id`
2. `inference_task_id`
3. `model_version_id`
4. `model_invocation_id`
5. `adapter_code`
6. `artifact_ref` or registry ref
7. `runtime_stub_or_real_adapter`
8. `input_refs`
9. `output_refs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `fallback_reason` nullable

### 5.9 Boundary note

1. `not_for_diagnosis` is mandatory.
2. `runtime_stub_or_real_adapter` must explicitly state stub or real-disabled boundary.
3. This adapter is a contract only, not an enabled real inference path.

## 6. Imaging ResNet18 Adapter Contract

### 6.1 Adapter identity

- `adapter_code`: `imaging_resnet18_cap_cop_adapter`
- `model_name`: `imaging_resnet18_cap_cop_classifier`
- `disease_agent`: `cap_cop_classifier_agent`
- `supported_task`: `CAP/COP binary classification`
- `supported_modalities`: `ct_image`, `nifti_volume`

### 6.2 Input schema

Input schema expectation:
1. CT/NIfTI volume only.
2. No clinical StandardScaler.
3. No 36-feature tabular dependency.
4. Volume must be normalized as documented for the image branch.

Input schema draft fields:
1. `trace_id`
2. `inference_task_id`
3. `case_id`
4. `patient_id` nullable
5. `disease_agent`
6. `requested_task`
7. `modality_refs`
8. `runtime_options`
9. `idempotency_key`
10. `ct_volume_ref`

### 6.3 Output schema

Output schema expectation:
1. `candidate_label`
2. `probability`
3. `confidence`
4. `uncertainty`
5. `limitations`
6. `input_quality_flags`
7. `recommended_next_actions_for_doctor_review`
8. `runtime_stub_or_real_adapter`

Output schema draft fields:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `model_version_id`
5. `model_id`
6. `disease_agent`
7. `task_type`
8. `status`
9. `outputs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `evidence_nodes_to_create`
14. `evidence_edges_to_create`
15. `trace_events_to_emit`
16. `error` nullable

### 6.4 Preprocessing dependency

Required image preprocessing contract:
1. NIfTI/CT volume input.
2. `float32` conversion.
3. z-score normalization when standard deviation exceeds the configured threshold.
4. channel-first tensor layout.
5. resize to `(96, 96, 96)`.
6. no clinical scaler usage.

### 6.5 Postprocessing rule

1. Map raw output to CAP/COP label space.
2. Package confidence and uncertainty.
3. Include limitations and imaging-specific review actions.
4. Do not imply clinical tabular evidence was used.

### 6.6 Error codes

Required error codes:
1. `invalid_input`
2. `missing_required_input`
3. `unsupported_modality`
4. `model_not_found`
5. `model_version_not_approved`
6. `inference_timeout`
7. `resource_exhausted`
8. `dependency_unavailable`
9. `internal_error`
10. `trace_id_missing`

### 6.7 Runtime constraints

1. CPU-first.
2. batch = 1.
3. concurrency = 1.
4. timeout governed.
5. no GPU until separately approved.
6. no silent fallback.

### 6.8 Trace/evidence requirements

Must emit or carry:
1. `trace_id`
2. `inference_task_id`
3. `model_version_id`
4. `model_invocation_id`
5. `adapter_code`
6. `artifact_ref` or registry ref
7. `runtime_stub_or_real_adapter`
8. `input_refs`
9. `output_refs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `fallback_reason` nullable

### 6.9 Boundary note

1. `not_for_diagnosis` is mandatory.
2. `runtime_stub_or_real_adapter` must explicitly state stub or real-disabled boundary.
3. This adapter is a contract only, not an enabled real inference path.

## 7. Multimodal ResNet18 Adapter Contract

### 7.1 Adapter identity

- `adapter_code`: `multimodal_resnet18_cap_cop_adapter`
- `model_name`: `multimodal_resnet18_cap_cop_classifier`
- `disease_agent`: `cap_cop_classifier_agent`
- `supported_task`: `CAP/COP binary classification`
- `supported_modalities`: `ct_image`, `clinical_table`

### 7.2 Input schema

Input schema expectation:
1. CT/NIfTI image plus clinical table features.
2. Must use the same 36-feature clinical preprocessing contract as the clinical MLP.
3. Must preserve the image branch and tabular branch separately before fusion.
4. Must preserve `Striated_shadow.1` in the tabular schema.

Input schema draft fields:
1. `trace_id`
2. `inference_task_id`
3. `case_id`
4. `patient_id` nullable
5. `disease_agent`
6. `requested_task`
7. `clinical_context_refs`
8. `modality_refs`
9. `missing_value_context`
10. `runtime_options`
11. `idempotency_key`
12. `ct_volume_ref`
13. `clinical_features`

### 7.3 Output schema

Output schema expectation:
1. `candidate_label`
2. `probability`
3. `confidence`
4. `uncertainty`
5. `limitations`
6. `input_quality_flags`
7. `missing_value_impact`
8. `recommended_next_actions_for_doctor_review`
9. `runtime_stub_or_real_adapter`

Output schema draft fields:
1. `trace_id`
2. `inference_task_id`
3. `model_invocation_id`
4. `model_version_id`
5. `model_id`
6. `disease_agent`
7. `task_type`
8. `status`
9. `outputs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `evidence_nodes_to_create`
14. `evidence_edges_to_create`
15. `trace_events_to_emit`
16. `error` nullable

### 7.4 Preprocessing dependency

Required dependencies:
1. `clinical_tabular_standardization_v1.json`
2. CT/NIfTI volume preprocessing rules

Preprocessing rules:
1. image preprocessing must follow the imaging contract
2. clinical tabular preprocessing must follow the 36-feature contract
3. fused inference must keep the two branches separate until fusion
4. no clinical StandardScaler omission is allowed in the tabular branch

### 7.5 Postprocessing rule

1. Map fused output to CAP/COP label space.
2. Package confidence and uncertainty.
3. Include combined limitations and next-review actions.
4. Do not present the result as a standalone diagnosis.

### 7.6 Error codes

Required error codes:
1. `invalid_input`
2. `missing_required_input`
3. `unsupported_modality`
4. `model_not_found`
5. `model_version_not_approved`
6. `inference_timeout`
7. `resource_exhausted`
8. `dependency_unavailable`
9. `internal_error`
10. `trace_id_missing`

### 7.7 Runtime constraints

1. CPU-first.
2. batch = 1.
3. concurrency = 1.
4. timeout governed.
5. no GPU until separately approved.
6. no silent fallback.

### 7.8 Trace/evidence requirements

Must emit or carry:
1. `trace_id`
2. `inference_task_id`
3. `model_version_id`
4. `model_invocation_id`
5. `adapter_code`
6. `artifact_ref` or registry ref
7. `runtime_stub_or_real_adapter`
8. `input_refs`
9. `output_refs`
10. `confidence`
11. `uncertainty`
12. `limitations`
13. `fallback_reason` nullable

### 7.9 Boundary note

1. `not_for_diagnosis` is mandatory.
2. `runtime_stub_or_real_adapter` must explicitly state stub or real-disabled boundary.
3. This adapter is a contract only, not an enabled real inference path.

## 8. Registry-Ready Metadata Draft

The following is a registry-ready metadata draft only. It does not approve, promote, or default any model.

Required future registration fields:
1. `model_name`
2. `model_version_id`
3. `version_label`
4. `artifact_uri`
5. `artifact_hash`
6. `adapter_type`
7. `preprocess_schema_version`
8. `postprocess_schema_version`
9. `runtime_constraints`
10. `limitations`
11. `safety_notes`

### 8.1 Clinical MLP metadata draft

- `model_name`: `clinical_mlp_cap_cop_classifier`
- `model_version_id`: `cap_cop_classifier_agent_v1.0.0_clinical_mlp`
- `version_label`: `v1.0.0-clinical-mlp`
- `artifact_uri`: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold5_best.pth` or another registry-selected exact artifact path
- `artifact_hash`: registry-ready exact-path hash value or explicit pending-hash state if verification is not yet finalized
- `adapter_type`: `clinical_mlp_cap_cop_adapter`
- `preprocess_schema_version`: `clinical_tabular_standardization_v1`
- `postprocess_schema_version`: `cap_cop_binary_output_v1`
- `runtime_constraints`: `cpu-first, batch=1, concurrency=1, timeout governed`
- `limitations`: `clinical-only; 36-feature schema; requires Striated_shadow.1 duplicate handling; not for diagnosis`
- `safety_notes`: `assistive output only; trace-bound; not a diagnosis`

### 8.2 Imaging ResNet18 metadata draft

- `model_name`: `imaging_resnet18_cap_cop_classifier`
- `model_version_id`: `cap_cop_classifier_agent_v1.0.0_imaging_resnet18`
- `version_label`: `v1.0.0-imaging-resnet18`
- `artifact_uri`: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth` or another registry-selected exact artifact path
- `artifact_hash`: registry-ready exact-path hash value or explicit pending-hash state if verification is not yet finalized
- `adapter_type`: `imaging_resnet18_cap_cop_adapter`
- `preprocess_schema_version`: `ct_nifti_unimodal_v1`
- `postprocess_schema_version`: `cap_cop_binary_output_v1`
- `runtime_constraints`: `cpu-first, batch=1, concurrency=1, timeout governed, no clinical scaler`
- `limitations`: `CT/NIfTI only; float32; channel-first; resize to (96,96,96); not for diagnosis`
- `safety_notes`: `assistive output only; trace-bound; not a diagnosis`

### 8.3 Multimodal ResNet18 metadata draft

- `model_name`: `multimodal_resnet18_cap_cop_classifier`
- `model_version_id`: `cap_cop_classifier_agent_v1.0.0_multimodal_resnet18`
- `version_label`: `v1.0.0-multimodal-resnet18`
- `artifact_uri`: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/weights/fold5_best.pth` or another registry-selected exact artifact path
- `artifact_hash`: registry-ready exact-path hash value or explicit pending-hash state if verification is not yet finalized
- `adapter_type`: `multimodal_resnet18_cap_cop_adapter`
- `preprocess_schema_version`: `clinical_tabular_standardization_v1 + ct_nifti_multimodal_v1`
- `postprocess_schema_version`: `cap_cop_binary_output_v1`
- `runtime_constraints`: `cpu-first, batch=1, concurrency=1, timeout governed`
- `limitations`: `requires image plus 36-feature clinical table; uses shared clinical preprocessing; not for diagnosis`
- `safety_notes`: `assistive output only; trace-bound; not a diagnosis`

## 9. Future Call Strategy Options

This stage may document possible future selection patterns, but it does not implement scheduling logic.

Possible future strategy patterns:
1. `single_model_call`
2. `parallel_model_call`
3. `multimodal_preferred`
4. `clinical_fallback`
5. `imaging_fallback`

Important rule:
1. These are design-time options only.
2. They do not override registry policy.
3. They do not create scheduling logic in this stage.
4. They do not convert any model into default.

## 10. Safety and Boundaries

1. No `.pth` is loaded in Stage 49.
2. No training or inference is executed.
3. No GPU is enabled.
4. No datasets are copied.
5. No original research directory is scanned.
6. No database schema is changed.
7. No Alembic is executed.
8. No Nginx is enabled.
9. No model is marked default.
10. No diagnosis claim is made.
11. All three adapters remain metadata-only contracts.

## 11. Stage 50 Recommendation

Stage 50 should prepare the real-model adapter skeleton and registry-ready wiring, but still remain non-loading until explicit user-authorized artifact onboarding occurs.

Recommended Stage 50 work:
1. adapter skeleton contract packaging
2. registry metadata field finalization
3. exact-path hash verification readiness
4. artifact onboarding checklist wiring
5. trace/evidence field mapping for future real adapter activation

## 12. Main-Controller Writeback Summary

1. Stage 49 adapter contract and registry-ready metadata draft are created.
2. Adapter codes are fixed as `clinical_mlp_cap_cop_adapter`, `imaging_resnet18_cap_cop_adapter`, and `multimodal_resnet18_cap_cop_adapter`.
3. Clinical and multimodal adapters both require `clinical_tabular_standardization_v1.json` and the 36-feature schema.
4. Imaging adapter uses CT/NIfTI preprocessing only and does not use clinical scaler.
5. Label mapping is fixed as `CAP=0`, `COP=1`.
6. `Striated_shadow.1` must be preserved as the pandas duplicate-column artifact to match training behavior.
7. Registry-ready metadata draft is prepared for all three models, but no approval, default, or promotion is implied.
8. Stage 50 should continue toward adapter skeleton preparation, still without loading real weights.
