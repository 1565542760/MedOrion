# MedOrion Stage 33A: Model Registry Lifecycle Schema Migration Plan

## 1. Problem

Stage 33 CRUD cannot continue safely because the live database schema does not support the lifecycle states frozen in Stage 32.

Current `model_versions.approval_state` only supports:
- `draft`
- `approved`
- `deprecated`
- `revoked`

Stage 32 requires:
- `draft`
- `offline_evaluated`
- `approved`
- `shadow`
- `canary`
- `default`
- `deprecated`
- `archived`

Why this blocks CRUD:
- `approve` cannot express post-approval transitions cleanly.
- `promote` cannot write `shadow`, `canary`, or `default`.
- `rollback` cannot reliably restore prior lifecycle state.
- no-downtime model iteration and default switching require explicit state persistence.
- silent fallback would hide lifecycle errors and break auditability.

Why not use JSON or ad hoc strings to bypass lifecycle state:
- lifecycle state would become unenforceable by the database.
- list/detail APIs would drift from truth and invite invalid values.
- service-layer-only checks would be too easy to bypass.
- future promote/default rules need a canonical, queryable state field.

## 2. Current Schema Findings

Current `model_registry` table fields:
- `id`
- `model_name`
- `disease_agent`
- `task_type`
- `modality_scope_json`
- `owner_team`
- `description`
- `is_active`
- `created_at`
- `updated_at`

Current `model_versions` table fields:
- `id`
- `model_id`
- `version_label`
- `approval_state`
- `contract_version`
- `artifact_ref_json`
- `input_schema_json`
- `output_schema_json`
- `metrics_json`
- `runtime_constraints_json`
- `published_at`
- `created_at`
- `updated_at`

Current enum values for `approval_state`:
- `draft`
- `approved`
- `deprecated`
- `revoked`

What the current schema can already carry:
- model metadata summaries
- version metadata summaries
- artifact metadata as JSON
- schema/metrics/runtime constraint metadata as JSON

What it cannot carry:
- the 5 additional Stage 32 lifecycle states
- explicit default / canary / shadow state transitions
- reliable rollback lineage

## 3. Target Lifecycle

Stage 32 frozen states:

- `draft`: not yet ready for offline evaluation or approval.
- `offline_evaluated`: passed offline evaluation, not yet approved for runtime use.
- `approved`: approved for controlled deployment, but not default.
- `shadow`: mirrors traffic or runs in comparison mode only.
- `canary`: serves limited traffic or limited cohort.
- `default`: the default operational choice for scheduling.
- `deprecated`: superseded, still queryable for history only.
- `archived`: retired and not schedulable.

Scheduling eligibility:
- schedulable: `approved`, `shadow`, `canary`, `default`
- not schedulable: `draft`, `offline_evaluated`, `deprecated`, `archived`

## 4. Migration Options

### Option A: Extend PostgreSQL enum `modelapprovalstate`

Approach:
- add `offline_evaluated`, `shadow`, `canary`, `default`, `archived`
- keep the existing enum-backed column

Pros:
- strongest alignment with current ORM and current schema
- minimal application code churn
- simple lifecycle validation at the database level

Cons:
- enum changes are harder to roll back in PostgreSQL
- future lifecycle additions require new enum migrations
- downgrade safety is limited once data uses new labels

### Option B: Convert to `String + CHECK constraint`

Approach:
- change the column to a plain string
- add a `CHECK` constraint for the allowed lifecycle values

Pros:
- more flexible if lifecycle state may change again
- easier to add/remove allowed values in future migrations
- rollback is generally simpler than enum surgery

Cons:
- requires more ORM/code changes than Option A
- weaker type semantics than native enum
- must keep CHECK constraint and application validation in sync

## 5. Recommended Option

Recommended: **Option A, extend the existing PostgreSQL enum**.

Reasoning:
- Stage 32 lifecycle is explicitly frozen, so enum stability is acceptable.
- the live codebase already uses an enum-backed `approval_state`.
- this is the smallest change that restores CRUD progress without a broader refactor.
- the stage is about enabling CRUD skeleton, not redesigning the storage model.

Important caveat:
- enum expansion has rollback limitations in PostgreSQL.
- once live rows use new states, downgrades must be treated as non-trivial.

If the project expects frequent lifecycle churn beyond Stage 32, a later refactor to `String + CHECK` can be planned as a separate schema evolution, but it is not the minimal move for Stage 33A.

## 6. Required Field Changes

Minimal necessary changes to make Stage 33 CRUD safe and auditable:

Keep current field names:
- `approval_state` remains the lifecycle field for now.

Add or standardize audit fields:
- `approved_by`
- `approved_at`
- `promoted_by`
- `promoted_at`
- `archived_at`
- `rollback_from_version_id`

Recommended metadata handling without adding new columns immediately:
- keep `artifact_uri` and `artifact_hash` inside `artifact_ref_json`
- keep `input_schema_version` and `output_schema_version` inside `input_schema_json` / `output_schema_json`
- keep `evaluation_summary` inside `metrics_json`
- keep `resource_requirements` inside `runtime_constraints_json`
- keep `limitations` inside `runtime_constraints_json` or `metrics_json` as a standardized key

If stronger queryability is required later, dedicated columns can be added in a later migration, but they are not required for the minimal Stage 33A plan.

## 7. Default Version Rule

Required rule:
- each `model_id` may have at most one `default` version.

Preferred enforcement:
- database-side partial unique index on `model_versions(model_id)` where `approval_state = 'default'`

Why this matters:
- service-layer checks alone are too weak under concurrent promote requests.
- a partial unique index prevents duplicate default versions at commit time.

If partial unique index is not used:
- the service must serialize promote operations and re-check the model family in a transaction.
- this is higher risk and should only be a fallback, not the primary guarantee.

Recommended approach:
- enforce with a partial unique index plus service-side recheck.

## 8. Trace / Audit Requirements

Model lifecycle transitions should be auditable, but they should not be written into case-centric `trace_events`.

Recommendation:
- do not force model registry events into patient/case trace streams.
- add a dedicated future audit surface, such as `model_lifecycle_events`, for clean separation.

For Stage 33A:
- document lifecycle changes in backend logs and migration notes.
- do not build the audit table yet.

## 9. `.pth Artifact Rule`

Non-negotiable rules:
- do not scan, copy, move, or guess any `.pth/.pt/.onnx/.ckpt/.safetensors` path.
- `artifact_uri` is only a string metadata field provided explicitly by the caller.
- do not read artifact contents.
- do not compute hash unless the caller explicitly provides it.
- do not commit model artifacts to Git.

## 10. Proposed Alembic Steps

Planned migration sequence only, not execution:

1. Expand lifecycle support
- either extend the PostgreSQL enum to 8 states
- or convert the column to string + CHECK constraint

2. Add lifecycle audit fields
- `approved_by`, `approved_at`, `promoted_by`, `promoted_at`, `archived_at`, `rollback_from_version_id`

3. Add default-version protection
- partial unique index to ensure one `default` per `model_id`

4. Backfill
- map existing rows:
  - current `draft` stays `draft`
  - current `approved` stays `approved`
  - current `deprecated` stays `deprecated`
  - current `revoked` should be mapped by policy, likely to `archived` or kept as legacy only during backfill

5. Validate
- verify inserts for all eight states
- verify only one default per model
- verify approve/promote/rollback can update state without schema errors

6. Rollback risk
- enum expansion rollback is limited in PostgreSQL
- backfill mapping must be documented before upgrade

## 11. Impact On Stage 33 CRUD

After this migration plan is approved and applied, Stage 33 CRUD can resume as follows:

- `create registry`: create a model metadata row
- `create version`: create a version row with lifecycle metadata
- `approve`: move a version into `approved`
- `promote`: move a version into `shadow`, `canary`, or `default`
- `rollback`: restore a previous version while preserving audit history
- `evaluations`: return stored evaluation metadata without loading artifacts

Without the migration:
- CRUD cannot safely represent Stage 32 lifecycle states
- default switching and no-downtime iteration remain blocked
- any working implementation would be a misleading stub, not a valid contract

