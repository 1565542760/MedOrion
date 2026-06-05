# Stage 99: Case Model Input Snapshot Migration Contract

## 1. Why Migration Is Needed
A real shadow execution path needs a reproducible snapshot of the exact input mapping that was prepared for the model.
The snapshot must bind the case, trace, model version, and input schema together so the input provenance can be audited and reproduced later.
It must also separate doctor-provided values from default-applied values and from still-missing fields.
The snapshot is input provenance only.
It is not a recommendation.
It is not a shadow output.
It is not a case evidence artifact.

## 2. Proposed Table
Table name:
- `case_model_input_snapshots`

## 3. Suggested Fields
- `id`
- `input_snapshot_id`
- `case_id`
- `patient_id`
- `trace_id`
- `model_version_id`
- `model_input_schema_id`
- `disease_task_feature_set_id`
- `preprocess_artifact_ref`
- `mapped_features_json`
- `missing_features_json`
- `defaulted_features_json`
- `doctor_provided_features_json`
- `source_refs_json`
- `validation_status`
- `current_assessment_status`
- `insufficient_data_for_assessment`
- `runtime_stub`
- `not_for_diagnosis`
- `created_at`
- `updated_at`

## 4. Field Semantics
- `mapped_features_json`: the final feature/value map prepared for the model.
- `missing_features_json`: fields that remain missing after mapping.
- `defaulted_features_json`: fields populated by an explicit default strategy.
- `doctor_provided_features_json`: fields filled by doctor input, separate from defaults.
- `source_refs_json`: provenance references for where values came from.
- `validation_status`: the validation outcome for the input snapshot.
- `current_assessment_status`: the current readiness state for the model input.
- `insufficient_data_for_assessment`: whether the case still lacks enough input for a reliable assessment.
- `runtime_stub`: must remain true in this phase.
- `not_for_diagnosis`: must remain true.

## 5. FK / Relationship Recommendations
Suggested foreign keys:
- `case_id -> cases.id`
- `patient_id -> patients.id`
- `model_version_id -> model_versions.id`

Suggested relationships:
- `trace_id` can remain a query key instead of a hard FK.
- `input_snapshot_id` should be unique.
- `shadow_inference_runs` can later reference `input_snapshot_id`.

## 6. Index Recommendations
Suggested indexes:
- `input_snapshot_id` unique
- `case_id`
- `trace_id`
- `model_version_id`
- `patient_id`
- `(case_id, created_at)`
- `(trace_id, model_version_id)`

## 7. Status Taxonomy
Suggested values:
- `ready_for_inference`
- `insufficient_data_for_assessment`
- `missing_required_features`
- `default_applied`
- `doctor_confirmation_required`
- `validation_failed`

## 8. Boundary with Missing-Value Consultation
- `default_applied` and `doctor_provided` must remain distinct.
- any defaulted value must carry a `default_strategy`.
- doctor-supplied values should carry their own doctor answer trace.
- no silent fallback.
- no hard-coded input fabrication.

## 9. Boundary with Case Trace / Evidence
- snapshots should not write `evidence_nodes`.
- snapshots should not write `trace_events`.
- if a later stage ever references the snapshot in evidence, it should do so by reference or summary only.
- the snapshot is not a clinical recommendation.

## 10. Boundary with Shadow Audit
- shadow runs can reference `input_snapshot_id`.
- shadow output does not replace the snapshot.
- the snapshot is the input side.
- the shadow output is the output side.

## 11. Migration Risk
- JSONB-heavy storage needs stable schema versioning.
- PHI and patient data audit risk must be managed carefully.
- synthetic fixtures must not be mistaken for real patient input.
- the CAP/COP 36-field shape must not become a global case-table shape.

## 12. Stage 100 Recommendation
Recommended next step: generate an Alembic review draft for this snapshot table.
Do not apply it immediately.
First review ORM and migration alignment.

## Final Guidance
Stage 99 defines the future migration contract only. It does not create the table, does not change the database, and does not authorize real shadow execution.