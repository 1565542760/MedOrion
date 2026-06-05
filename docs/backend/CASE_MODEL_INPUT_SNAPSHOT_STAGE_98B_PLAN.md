# Stage 98B: Case Model Input Snapshot Skeleton Plan

## 1. Why Snapshot Is Needed
The Stage 98A validation fixture proved that the input mapping layer can reach 
ready_for_inference for the CAP/COP clinical MLP fold5 schema.
Before real shadow execution, we still need a persisted snapshot of what was actually fed into the model-input layer at that moment.
The snapshot is for provenance, audit, reproduction, and missing-value tracking.
It is not a model inference result.
It is not a recommendation.

## 2. Scope
A future snapshot record should capture:
- case_id
- patient_id
- trace_id
- model_version_id
- model_input_schema_id
- disease_task_feature_set_id
- preprocess_artifact_ref
- mapped_features_json
- missing_features_json
- defaulted_features_json
- doctor_provided_features_json
- source_refs_json
- alidation_status
- current_assessment_status
- insufficient_data_for_assessment
- not_for_diagnosis
- 
untime_stub
- created_at

## 3. CAP/COP Fold5 Baseline
- disease_task_feature_set_id = cap_cop_clinical_feature_set_v1
- model_input_schema_id = clinical_mlp_cap_cop_input_schema_v1
- 36 CAP/COP task-related attributes
- Striated_shadow.1 must remain present
- label_mapping = CAP=0, COP=1
- preprocess_artifact_ref = clinical_tabular_standardization_v1.json

## 4. Snapshot Status Taxonomy
Suggested statuses:
- 
ready_for_inference
- insufficient_data_for_assessment
- missing_required_features
- default_applied
- doctor_confirmation_required
- alidation_failed

## 5. Missing Value Provenance
- doctor_provided must not be confused with default_applied
- every defaulted value must carry a default_strategy
- if missing values cannot be closed, the state must be insufficient_data_for_assessment
- no silent fallback
- no hard-coded input fabrication

## 6. Future Table Draft
Table: case_model_input_snapshots

Suggested fields:
- id
- input_snapshot_id
- case_id
- patient_id
- trace_id
- model_version_id
- model_input_schema_id
- disease_task_feature_set_id
- preprocess_artifact_ref
- mapped_features_json
- missing_features_json
- defaulted_features_json
- doctor_provided_features_json
- source_refs_json
- alidation_status
- current_assessment_status
- insufficient_data_for_assessment
- 
untime_stub
- not_for_diagnosis
- created_at

Suggested indexes:
- case_id
- trace_id
- model_version_id
- input_snapshot_id unique

## 7. API Draft
- POST /api/v1/cases/{case_id}/model-input-snapshots
- GET /api/v1/model-input-snapshots/{input_snapshot_id}
- GET /api/v1/cases/{case_id}/model-input-snapshots
- GET /api/v1/traces/{trace_id}/model-input-snapshots

## 8. Relationship to Shadow Audit
- shadow_inference_runs may later reference input_snapshot_id
- shadow_inference_outputs do not replace the snapshot
- the snapshot is input provenance
- the shadow output is output audit
- the snapshot does not write recommendation
- the snapshot does not write case evidence chain unless a later stage separately approves an evidence summary link

## 9. Relationship to Fixture
- Stage 98A fixture is the validation baseline
- the fixture helped define the snapshot fields
- the fixture is not patient data
- the fixture must not be used as a real patient snapshot

## 10. Stage 99 Recommendation
A. case_model_input_snapshot migration contract
B. snapshot API skeleton
C. frontend snapshot viewer
D. stay in documentation

Recommended default: A.

## Final Guidance
Stage 98B stays in documentation and schema planning. It does not authorize real shadow execution, does not change the governance state, and does not create the snapshot table yet.
