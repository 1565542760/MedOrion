# Stage 59 Skeleton: Disease Task Feature Sets and Model Input Preview

## Goal
Stage 59 defines the first API skeleton that separates:
- disease-task feature sets
- model input schemas
- case input preview and validation

The key boundary is that the CAP/COP 36-field collection is a disease-task feature set, while each model version defines its own model input schema on top of that feature set.

## Naming Rules
### disease_task_feature_set
A disease-specific clinical attribute collection that can be shared by multiple models.

Example:
- `cap_cop_clinical_feature_set_v1`

### model_input_schema
A model-version-specific contract for how a model consumes a disease-task feature set.

Example:
- `clinical_mlp_cap_cop_input_schema_v1`
- `multimodal_resnet18_cap_cop_input_schema_v1`

## Model Selection Rules
Model selection must always be disease-task first.

Rules:
1. The system may only consider models that explicitly support the current `disease_task`.
2. CAP/COP classification may only consider models that support `cap_cop` or `CAP_COP_CLASSIFICATION` or an equivalent declared CAP/COP disease-task code.
3. Cross-disease model calls are not allowed.
4. If only one model supports the disease task, do not invoke LLM-based model selection. Go directly to that model's input validation.
5. Only when multiple models support the same disease task should model selection / orchestration be used.
6. In multi-model scenarios, ranking may consider field satisfaction, missing-feature severity, modality availability, lifecycle status, historical evaluation results, resource constraints, uncertainty, and whether doctor clarification is needed.
7. The LLM may assist with explanation or ranking, but the rule layer must still validate the final candidate before any call is allowed.

## API Skeleton
### GET /api/v1/disease-task-feature-sets/{feature_set_id}
Return feature set metadata.

### GET /api/v1/disease-task-feature-sets/{feature_set_id}/features
Return feature definitions, source field hints, and ordering.

### GET /api/v1/model-input-schemas/{model_version_id}
Return schema metadata and the referenced disease-task feature set.

### GET /api/v1/model-input-schemas/{model_version_id}/feature-requirements
Return required/optional features, units, value ranges, enum mapping, and default policy.

### POST /api/v1/cases/{case_id}/model-input-preview
Return a preview of mapped inputs.

### POST /api/v1/cases/{case_id}/model-input-validation
Return validation status and missing/invalid field details.

## Preview / Validation Semantics
Responses should clearly distinguish:
- source data found in case tables
- mapped model features
- missing fields
- doctor-provided values
- defaulted values
- schema mismatches
- unit mismatches
- enum mismatches
- `insufficient_data_for_assessment`

Recommended response fields:
- `disease_task_feature_set_id`
- `disease_task_feature_set_key`
- `model_input_schema_id`
- `model_input_schema_version`
- `snapshot_status`
- `mapped_features`
- `missing_features`
- `defaulted_features`
- `warnings`
- `insufficient_data_for_assessment`
- `missing_required_features`
- `why_required`
- `suggested_doctor_questions`
- `default_strategy_available`
- `current_assessment_status`
- `runtime_stub`
- `limitations`

## Validation / Insufficient Data Rules
Required feature handling must never use silent fallback.

Allowed paths only:
- ask the doctor through missing-value consultation
- apply an explicit default strategy if one exists
- return `insufficient_data_for_assessment` if the case still cannot be assessed

The system must not:
- fabricate input values
- confuse defaulted values with doctor-provided values
- proceed as if the result were fully reliable when key inputs are still missing

If the case cannot be assessed, the response should include:
- `missing_required_features`
- `why_required`
- `suggested_doctor_questions`
- `default_strategy_available`
- `current_assessment_status`
- `trace_id`
- `runtime_stub`
- `limitations`

## Default and Trace / Evidence Semantics
- Doctor-provided values should be represented as `doctor_provided`.
- Defaulted values should be represented as `default_applied`.
- Default-applied records must include `default_strategy_code`, `default_reason`, and `trace_id`.
- Default handling should be traceable, for example via a `missing_value_defaulted` evidence edge.
- If the system returns `insufficient_data_for_assessment`, it should still emit a trace event or audit note explaining the stop reason.

## Database Plan Draft
No tables are created in Stage 59, but the future plan should likely include:
- `disease_task_feature_sets`
- `disease_task_features`
- `model_input_schemas`
- `model_feature_requirements`
- `clinical_feature_mappings`
- `case_model_input_snapshots`
- `model_selection_decisions` (future audit-only suggestion)

## Constraints
- No database changes.
- No Alembic.
- No real model loading.
- No live inference.
- No frontend changes.
- No Nginx.
- No training.
- No writing case trace/evidence in this stage.
- No LLM bypass of rule-based selection.

## Next Step
Stage 60 can decide whether to add metadata-only backend read endpoints or a temporary preview service that stays separate from live inference.
