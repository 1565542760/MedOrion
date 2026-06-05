# Stage 98A: Clinical MLP Fold5 Sample Case Input Fixture for Validation

## Purpose
This stage created a validation-only synthetic fixture for the CAP/COP clinical MLP fold5 input schema.
It is intended to validate feature-name alignment and missing-feature handling without model loading or inference.

## Fixture Location
- JSON fixture: docs/model_orchestration/fixtures/cap_cop_clinical_mlp_fold5_input_fixture.json
- This fixture is synthetic and validation-only.
- It is not real patient data and is not for diagnosis.

## Fixture Summary
- disease_task = cap_cop
- model_version_id = b12f315a-7f44-491d-bf46-b0da73f6da03
- model_input_schema_id = clinical_mlp_cap_cop_input_schema_v1
- disease_task_feature_set_id = cap_cop_clinical_feature_set_v1
- not_for_diagnosis = true
- validation_only = true
- metadata_only = true
- fixture_origin = synthetic_neutral_values

## 36 Feature Names Included
### Required features
- Age
- Sex
- Temperature
- RespiratoryRate
- SPO2
- WBC
- NeutrophilPercent
- CRP
- Dyspnea
- Consolidation
- Striated_shadow.1

### Optional / defaultable features
- HeartRate
- SystolicBP
- DiastolicBP
- LymphocytePercent
- Procalcitonin
- ESR
- Hemoglobin
- Platelet
- Sodium
- Potassium
- Chloride
- BUN
- Creatinine
- ALT
- AST
- Albumin
- Glucose
- Cough
- Fever
- ChestPain
- Wheeze
- Crackles
- PleuralEffusion
- Infiltration
- SmokingHistory

## Validation Run
- Endpoint: POST /api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/model-input-validation
- The fixture was posted with all 36 CAP/COP features present.
- Striated_shadow.1 was included and recognized.

## Validation Result
- current_assessment_status = ready_for_inference
- missing_required_features = []
- missing_features = []
- mapped_feature_count = 36
- default_strategy_available = false
- requires_doctor_confirmation = false
- insufficient_data_for_assessment = false
- runtime_stub = true

## Audit / Safety Observations
- The validation-only API call did not change recommendations.
- The validation-only API call did not add shadow audit rows.
- The validation-only API call did not add trace events or evidence nodes/edges.
- The validation-only API call did not load a model, call torch.load, or perform inference.

## Count Check
- recommendations = 30
- trace_events = 192
- evidence_nodes = 70
- evidence_edges = 35
- shadow_inference_runs = 16
- shadow_inference_outputs = 1

## Remaining Gap
The synthetic fixture proves the field mapping can be aligned for validation, but it does not yet provide a persistent case-model snapshot or a real production input pipeline.

## Stage 98B Recommendation
Recommended next step: implement a case_model_input_snapshot skeleton or an equivalent persisted input record flow.

## Compliance
This stage did not modify code, configuration, database schema, or Alembic migrations. It did not join allowlists, open the shadow switch, load models, call torch.load, train, infer, enable GPU, enable Nginx, modify the frontend, write recommendations, or write case trace/evidence.
