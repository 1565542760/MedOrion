# Coursework Stage C29: Clinical CSV Strict Artifact-Order Validation Backend Contract

## Purpose
Stage C29 defines a backend strict validation contract for CAP/COP clinical table inputs. The goal is to validate raw CSV / pasted clinical table data against the training artifact order before any snapshot is treated as model-ready.

This stage is validation-only. It does not trigger model inference and does not create a real predictive snapshot unless the full 36-feature contract is satisfied and every feature is type-checked successfully.

## Source of Truth
The strict artifact order is defined by:

- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json`

That artifact contains the complete 36-feature CAP/COP clinical order, including `Striated_shadow.1`.

Important boundary:

- `feature_schema.json` is auxiliary only.
- It contains 35 features and must not be used to substitute, relax, or silently complete the 36-feature validation contract.
- No alias/default fallback is allowed.
- No product schema order may override artifact order.

## Non Goals
This stage does not:

- load or run a model
- create a real inference snapshot automatically
- write recommendation, trace, evidence, or shadow output
- read real patient CSV data outside the validation request
- depend on frontend-only validation
- silently infer missing columns

## Proposed Endpoint

`POST /api/v1/cases/{case_id}/model-input/clinical-table/validate`

### Request
- `raw_columns: list[str]`
- `rows: list[dict[str, Any]]` or `sample_row: dict[str, Any]`
- `source_type: csv_paste | csv_upload_metadata | manual_entry`
- `not_for_diagnosis: true`
- `shadow_only: true`

### Response
- `artifact_id`
- `artifact_ref`
- `artifact_feature_count = 36`
- `artifact_feature_order`
- `feature_mappings`
- `type_coercion_results`
- `missing_required_features`
- `extra_raw_columns`
- `validation_status`
- `can_create_snapshot`
- `failure_reasons`

## Validation Rules
1. `artifact_feature_order` must come from the standardization artifact.
2. The provided `raw_columns` must match the artifact order exactly for `ready_for_inference`.
3. Missing any of the 36 features is a hard failure.
4. `Striated_shadow.1` is mandatory.
5. Extra columns are not allowed in a ready state.
6. Type coercion must succeed for every row that participates in validation.
7. No silent fallback, aliasing, or default fill is allowed.
8. `feature_schema.json` may be used only as a helper reference, never as the contract source.

## Validation Status Semantics
- `ready_for_inference`: strict order matches, all 36 features present, all required type checks pass.
- `insufficient_data_for_assessment`: one or more required features are missing.
- `schema_unverified`: order mismatch, extra columns, duplicate columns, row-level type coercion failure, or no row data.

## Snapshot Boundary
This endpoint does not create a real predictive snapshot.

A later snapshot may only be created if:

- the 36-feature artifact order is matched exactly
- no required feature is missing
- no type coercion failure occurs
- `not_for_diagnosis=true`
- `shadow_only=true`

## Privacy / RBAC
- The endpoint is case-scoped.
- It must use existing case access control.
- It must not write clinical evidence or audit provenance beyond the validation response.
- It must not expose any model internals or inference outputs.

## Implementation Note
The backend should read the standardization artifact directly and use the CAP/COP clinical feature definitions only as auxiliary metadata for type and unit checks. The 35-feature `feature_schema.json` must never be used to fill or weaken the 36-feature validation boundary.
