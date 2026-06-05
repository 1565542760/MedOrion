# Stage 97: Clinical MLP Fold5 Input Readiness / Missing Feature Closure Plan

## 1. Current Blocker
Stage 96 proved that allowlist and adapter alias governance can pass cleanly.
The current blocker is input_insufficient.
That means the feature set, input mapping, and missing-feature handling are not yet sufficient for real shadow execution.

## 2. Required Input Contract
- disease_task_feature_set_id = cap_cop_clinical_feature_set_v1
- model_input_schema_id = clinical_mlp_cap_cop_input_schema_v1
- 36 CAP/COP task-related attributes
- Striated_shadow.1 must remain present
- label_mapping = CAP=0, COP=1
- preprocess_artifact_ref = clinical_tabular_standardization_v1.json

## 3. Missing Feature Closure Paths
Only these three paths are allowed:
- missing-value consultation
- explicit default strategy
- insufficient_data_for_assessment

Forbidden:
- silent fallback
- hard-coded input fabrication
- masking defaults as doctor-entered values

## 4. Case Data Source Plan
Future case data may come from:
- structured clinical observations
- lab results
- EMR structured tables
- imported patient tables
- future model-specific tables

This plan must not freeze the entire system into a CAP/COP-only 36-field layout.

## 5. Feature Mapping Readiness Checklist
Each feature should be confirmed for:
- source_clinical_field
- model_feature_name
- required or optional
- unit
- value range
- enum mapping
- missing_value_policy
- default_strategy
- doctor question text
- audit behavior

## 6. Validation Flow Before Shadow
Planned flow:
1. build model input preview
2. identify missing required features
3. create missing-value queries when needed
4. apply explicit defaults only when allowed
5. produce an input snapshot
6. only if valid, allow future shadow execution to proceed
7. still no recommendation write

## 7. What Stage 98 Could Do
A. create a sample case input fixture for fold5 validation only
B. implement a case_model_input_snapshot skeleton
C. improve missing-value UI for model input
D. stay in documentation

Recommended default: A or B.

## 8. Explicit Non-Actions
- no model load
- no torch.load
- no inference
- no training
- no allowlist change
- no shadow switch enablement
- no recommendation write
- no trace/evidence write

## Final Guidance
Stage 97 stays in readiness planning. It does not authorize real shadow execution, and it does not change the governance state by itself.
