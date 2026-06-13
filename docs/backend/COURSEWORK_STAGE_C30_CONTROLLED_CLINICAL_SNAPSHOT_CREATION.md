# Coursework Stage C30: Controlled Snapshot Creation from Strict Clinical CSV Validation

## Goal
Stage C30 adds a controlled backend entry point that creates `case_model_input_snapshot` only after strict clinical CSV/table validation has passed on the server.

This stage does not run any model. It does not write recommendation, trace, evidence, or shadow output.

## Strict Gate
A snapshot may only be created when all of the following are true:

- 36-feature strict order validation passes
- all features are present
- all values can be coerced successfully
- `Striated_shadow.1` is present
- `validation_status = ready_for_inference`
- `can_create_snapshot = true`
- `not_for_diagnosis = true`
- `shadow_only = true`

The backend must re-run strict validation. It must not trust a frontend validation result.

## Proposed Endpoint

`POST /api/v1/cases/{case_id}/model-input/clinical-table/snapshots`

### Request
The request reuses the strict validation payload:

- `raw_columns`
- `rows` or `sample_row`
- `source_type = csv_paste | csv_upload_metadata | manual_entry`
- `trace_id` optional
- `not_for_diagnosis = true`
- `shadow_only = true`

### Response
On success:

- `snapshot_created = true`
- `snapshot` contains the created `case_model_input_snapshot`
- `validation_status = ready_for_inference`
- `can_create_snapshot = true`
- `mapped_features` contains the artifact-order 36-feature mapping
- `source_refs` contains lightweight provenance only
- `doctor_provided_features` contains feature-level provenance summary only, not the raw CSV

On validation failure:

- `snapshot_created = false`
- `snapshot = null`
- `failure_reasons` explains why the strict gate failed
- no snapshot is written

## Snapshot Materialization Rules
When a snapshot is written:

- `mapped_features` must follow the strict artifact order
- `source_refs` must not include the full raw CSV payload
- `doctor_provided_features` may include feature-level source summaries only
- `validation_status = ready_for_inference`
- `current_assessment_status = ready_for_inference`
- `insufficient_data_for_assessment = false`
- `runtime_stub = true`
- `not_for_diagnosis = true`

## Model Binding
The controlled snapshot is bound to the CAP/COP clinical MLP fold5 model version:

- `b12f315a-7f44-491d-bf46-b0da73f6da03`

The strict validation contract itself remains separate from the snapshot materialization step.

## Data Boundary
This stage does not:

- store the full CSV payload
- store raw patient CSV files
- create a shadow output
- call a model
- write recommendation, trace, or evidence
- auto-create a snapshot when validation fails

## Relationship to C29
C29 introduced strict clinical CSV validation. C30 turns that strict validation into a controlled server-side snapshot creation gate.

## Next Step Suggestion
If C30 is stable, the next safe step is to review the snapshot creation traceability document and then wire this snapshot into the existing shadow bridge path.
