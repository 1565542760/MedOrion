# Stage 58 Contract: Disease Task Feature Sets, Model Input Schemas, and Clinical Feature Mapping

## Purpose
MedOrion must not freeze every patient case into one global table schema. Different diseases, models, and agents will require different clinical fields, units, mapping rules, and missing-value behavior.

This contract defines two related but distinct layers:
- a **disease task feature set** that describes the clinical attributes relevant to a disease-task family
- a **model input schema** that describes the exact inputs expected by a specific `model_version_id`

The schema is metadata-only at this stage. It does not change the database, does not change the model service, and does not make CAP/COP fold5 default.

## Core Concepts

### disease_task_feature_set
A disease-task-level collection of clinical attributes that may be shared by multiple models.

Examples:
- `cap_cop_clinical_feature_set_v1`
- a future feature set for another disease family

A disease task feature set:
- describes the clinically relevant attribute universe for a disease task
- can be reused by multiple model versions
- can evolve over time through versioning
- is not the universal case table schema

### model_input_schema
A model-version-specific definition of the inputs expected by a given `model_version_id`.

A model input schema:
- may reference one disease task feature set
- may use the full feature set or only a subset
- defines which features are required or optional for this model version
- defines `default_strategy`, `missing_value_policy`, and `preprocess_artifact_ref`
- describes the exact feature names consumed by the model

A model input schema is not the same as the case table schema.

### model_feature_requirements
The ordered set of features that a model version expects. Each requirement defines:
- feature name used by the model
- feature type
- required or optional
- unit or categorical domain
- value constraints
- default and missing-value policy
- mapping from clinical sources

### clinical_feature_mapping
The mapping contract from one or more source clinical fields into a single model feature. A mapping can merge, normalize, transform, or select from several source fields. Mapping must be auditable and versioned.

### source_clinical_field
A concrete field originating from clinical observations, lab results, EMR text extraction, or a structured table. Examples include a lab numeric value, a structured symptom flag, or a derived clinical observation.

### model_feature_name
The exact feature key consumed by a model. This is model-specific and may differ from source field names.

### feature_type
The semantic type of a feature, such as:
- numeric
- integer
- boolean
- categorical
- ordinal
- text
- datetime
- binary_flag
- derived_score

### required / optional
Whether the model cannot proceed without the feature. Required features missing from source data must enter missing-value consultation or default handling.

### default_strategy
The policy used when a required feature remains unavailable after consultation or when the contract explicitly permits fallback. A default strategy must be explicit, deterministic, versioned, and traceable.

### missing_value_policy
The model- and feature-specific rule for handling missing values. The policy may require doctor consultation first, then default handling, then explicit audit logging.

### unit
The expected measurement unit for a feature, such as `mmHg`, `mg/dL`, `1/0`, or `days`.

### value_range
The acceptable numeric range or domain for a feature. For numeric features this can be min/max; for categorical features it can be an allowed label set.

### enum_mapping
The allowed mapping between source labels and model labels. Enum mapping must be explicit and versioned, especially when clinical source labels differ from model training labels.

### preprocess_artifact_ref
A reference to the preprocessing artifact or adapter metadata used to transform mapped clinical values into model-ready tensors or vectors. This is metadata only at this stage.

### schema_version
A version identifier for the disease task feature set and the model input schema. Schema versioning allows later models or diseases to define different input requirements without changing the global clinical data model.

## CAP/COP Disease Task Feature Set Special Case
The CAP/COP细分肺炎分类任务 currently uses a historical clinical attribute collection with 36 fields. That collection is valid as the disease-task feature set for this task family, not as a universal case schema.

Important rules:
- The historical field `Striated_shadow.1` must be preserved exactly as a named attribute in the CAP/COP feature set.
- The 36-field collection belongs to `cap_cop_clinical_feature_set_v1`.
- That feature set can be reused by multiple CAP/COP models.
- MedOrion must not force all patient tables to adopt these 36 fields.
- Another disease or model may require a different feature set, names, units, and missing-value behavior.

## Backend Mapping Flow
Future backend flow should be:
1. Read clinical data from case sources.
2. Gather values from clinical observations, lab results, EMR-derived structured fields, and structured tables.
3. Apply a feature mapping layer to convert source clinical fields into disease-task feature set attributes and then into model feature names.
4. Validate required features and units.
5. For missing features, create or reuse missing-value consultation.
6. If the doctor does not provide the value, apply the declared default strategy and record it.
7. Produce an auditable input snapshot.
8. Use that snapshot for model inference.

Mapping results must be auditable and must not be silent.

## Disease Task Filtering and Model Selection Rules
Before any model input validation or model selection, MedOrion must filter the candidate models by the current `disease_task`.

Rules:
1. Only models that explicitly support the current disease task may be considered.
2. CAP/COP classification must only consider models that support `cap_cop` or `CAP_COP_CLASSIFICATION` or an equivalent declared CAP/COP disease-task code.
3. Cross-disease model calls are not allowed.
4. If only one model supports the disease task, the system must not invoke LLM-based model selection. It should go directly to that model's input validation.
5. Model selection / orchestration is only needed when multiple models support the same disease task.
6. In multi-model scenarios, ranking may consider input completeness, missing-feature severity, modality availability, model lifecycle status, historical evaluation results, resource constraints, uncertainty, and whether doctor clarification is needed.
7. The LLM may assist with explanation and ranking, but the final call path must still be validated by the rule layer.

## Required Feature Missing Handling
Required feature handling must never use silent fallback.

Allowed paths only:
- ask the doctor through missing-value consultation
- apply an explicit default strategy if one exists
- return `insufficient_data_for_assessment` if the case still cannot be assessed

The system must not:
- fabricate input values
- confuse defaulted values with doctor-provided values
- proceed as if the result were fully reliable when key inputs are still missing

If the system cannot make a valid assessment, it must return:
- `insufficient_data_for_assessment`

Recommended response fields for that case:
- `missing_required_features`
- `why_required`
- `suggested_doctor_questions`
- `default_strategy_available`
- `current_assessment_status`
- `trace_id`
- `runtime_stub`
- `limitations`

## Trace / Evidence Notes for Missing Data
- Doctor-supplied values must be recorded as `doctor_provided`.
- Default-applied values must be recorded as `default_applied`.
- Default-applied records must include `default_strategy_code`, `default_reason`, and `trace_id`.
- Missing-value defaulting should use an evidence edge such as `missing_value_defaulted`.
- If the case is still insufficient for assessment, the system should at least keep a trace event or audit note explaining why it stopped.

Mapping results must be auditable and must not be silent.

## API Draft
The following API shapes are proposed for later implementation.

### GET /api/v1/disease-task-feature-sets/{feature_set_id}
Return the disease task feature set metadata for a disease family.

### GET /api/v1/disease-task-feature-sets/{feature_set_id}/features
Return the ordered feature list, types, units, and source field contracts.

### GET /api/v1/model-input-schemas/{model_version_id}
Return the model input schema for a specific model version.

### GET /api/v1/model-input-schemas/{model_version_id}/feature-requirements
Return the ordered feature requirements, types, units, and missing-value policies.

### POST /api/v1/cases/{case_id}/model-input-preview
Preview how a case would map to a model input schema, without launching inference.

### POST /api/v1/cases/{case_id}/model-input-validation
Validate whether the case can be mapped to the target schema, and surface missing features, unit mismatches, enum gaps, and insufficient data status.

## Database Plan Draft
This stage only defines the data model plan. It does not create tables.

### disease_task_feature_sets
Metadata for a disease-task feature set.
Suggested fields:
- id
- disease_task_code
- feature_set_key
- feature_set_name
- schema_version
- status
- description
- created_at
- updated_at

### disease_task_features
Feature-level definitions inside a disease-task feature set.
Suggested fields:
- id
- disease_task_feature_set_id
- source_field_name
- display_name
- feature_type
- required_in_task
- unit
- value_range
- enum_mapping
- feature_order
- notes

### model_input_schemas
Metadata for a model version's input contract.
Suggested fields:
- id
- model_version_id
- disease_task_feature_set_id
- schema_version
- schema_name
- status
- preprocess_artifact_ref
- description
- created_at
- updated_at

### model_feature_requirements
Feature-level requirements for a model input schema.
Suggested fields:
- id
- model_input_schema_id
- model_feature_name
- source_field_name
- feature_type
- required
- unit
- value_range
- enum_mapping
- default_strategy
- missing_value_policy
- feature_order
- notes

### clinical_feature_mappings
Mapping rules from source clinical fields into model features.
Suggested fields:
- id
- model_input_schema_id
- model_feature_requirement_id
- source_clinical_field
- source_table
- transform_rule
- aggregation_rule
- enum_mapping
- is_primary_source
- mapping_version
- notes

### case_model_input_snapshots
Auditable snapshots of mapped model inputs for a specific case and model version.
Suggested fields:
- id
- case_id
- patient_id
- disease_task_feature_set_id
- model_version_id
- model_input_schema_id
- trace_id
- snapshot_version
- input_json
- missing_fields_json
- defaulted_fields_json
- source_refs_json
- assessment_status
- insufficient_reason_json
- created_at
- created_by

### model_selection_decisions (future audit suggestion only)
A later-stage audit table may record how multiple eligible models were ranked and why one was selected. This stage does not create it.
Suggested fields:
- id
- trace_id
- case_id
- patient_id
- disease_task_feature_set_id
- candidate_models_json
- selected_model_version_id
- decision_reason_json
- selected_by
- selected_at
- runtime_stub

## Relationship To Existing Tables
The proposed input schema layer must work with existing MedOrion tables, not replace them.

Relevant existing tables:
- `model_versions`
- `clinical_observations`
- `lab_results`
- `case_missing_value_queries`
- `trace_events`
- `evidence_nodes`
- `recommendations`

Future behavior:
- The disease-task feature set points to a shared clinical attribute family.
- The model version points to one input schema version.
- Case clinical data is read from source tables.
- Missing features can create missing-value consultation.
- Default handling remains traceable.
- Input snapshots can later be referenced by inference, recommendation, or audit flows.

## Trace / Evidence Requirements
The mapping layer must be auditable.

Requirements:
- Model input mapping must produce an input snapshot.
- Missing-value handling must preserve the same `trace_id` across consultation and inference.
- Default fill values must not be confused with doctor-provided values.
- The input snapshot must record which fields were mapped, defaulted, or left missing.
- Real inference should later bind at least:
  - `model_version_id`
  - `model_input_schema_id`
  - `disease_task_feature_set_id`
  - `preprocess_artifact_ref`
  - `input_snapshot_id`

## Explicit Prohibitions
This stage must not:
- change the database schema
- run Alembic
- change the model service
- change the frontend
- enable Nginx
- train models
- start live inference
- treat CAP/COP fold5 as default
- turn the 36-field CAP/COP attribute set into a universal case schema

## Stage 59 Suggestion
The next stage should define either:
- the first backend feature-set and input-schema read APIs, or
- the first case input preview and validation skeleton.

That next stage should still keep the schema metadata-only unless the review explicitly approves persistence.
