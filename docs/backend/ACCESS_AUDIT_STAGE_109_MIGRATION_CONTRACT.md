# Stage 109: Access Audit Events Migration Contract

## 1. Goals

Stage 109 converts the Stage 108 access audit design into a migration contract so the team can later produce a candidate Alembic revision with less ambiguity.

The goal is to define the table shape, index strategy, foreign-key guidance, taxonomy boundaries, privacy boundaries, and rollout order before any ORM or migration is generated.

## 2. Non Goals

This stage does not:

- modify code
- modify ORM models
- generate Alembic
- execute Alembic
- build the table
- write any access audit rows
- wire helper emit logic
- add frontend work
- write recommendation / trace / evidence data
- connect real model execution

## 3. Table: access_audit_events

Suggested fields:

- `id` UUID primary key
- `access_event_id` string unique not null
- `actor_user_id` UUID nullable, FK -> `users.id`
- `actor_type` string nullable
- `actor_role` string nullable
- `access_mode` string not null
- `resource_type` string not null
- `resource_id` string nullable
- `case_id` UUID nullable, FK -> `cases.id`
- `patient_id` UUID nullable, FK -> `patients.id`
- `trace_id` string nullable
- `decision` string not null
- `denial_reason` string nullable
- `policy_source` string nullable
- `request_id` string nullable
- `route_path` string nullable
- `method` string nullable
- `metadata_json` JSONB default `{}`
- `created_at` timestamp not null

### Nullable field rationale

- `actor_user_id` is nullable because service/internal callers, unauthenticated denials, and some future automation events may not have a user row.
- `actor_type` and `actor_role` are nullable because anonymous or service-side events may not map cleanly to a human role.
- `resource_id` is nullable because some denied attempts happen before a resource is fully resolved.
- `case_id`, `patient_id`, and `trace_id` are nullable because not every access target is case-scoped or trace-scoped.
- `denial_reason` and `policy_source` are nullable because allowed events do not need a denial explanation, and some older or fallback code paths may not know the exact policy source yet.
- `request_id`, `route_path`, and `method` are nullable because the first migration contract should support helper-level emit as well as HTTP-level emit.
- `metadata_json` is non-null with an empty object default so callers always have a safe place for lightweight context.

## 4. FK Guidance

Recommended FKs:

- `actor_user_id -> users.id` nullable
- `case_id -> cases.id` nullable
- `patient_id -> patients.id` nullable

Not recommended as hard FKs in Stage 109:

- `trace_id`
- `resource_id`

### Why

- `resource_type` / `resource_id` represent a polymorphic audit reference.
- A single audit table should not require one FK per resource kind.
- Access audit should not become invalid just because the underlying resource was archived, deleted, or redacted later.
- Nullable FKs allow denied / missing-resource scenarios to be recorded without inventing placeholder rows.

## 5. Index Guidance

Recommended indexes:

- unique `access_event_id`
- `actor_user_id`
- `case_id`
- `patient_id`
- `trace_id`
- `resource_type`
- `resource_id`
- `decision`
- `access_mode`
- `created_at`
- `(case_id, created_at)`
- `(actor_user_id, created_at)`
- `(resource_type, resource_id)`
- `(decision, created_at)`

### Minimal recommended set

If we want to keep the first migration compact, the minimum useful set is:

- unique `access_event_id`
- `case_id`
- `patient_id`
- `trace_id`
- `resource_type`
- `resource_id`
- `decision`
- `access_mode`
- `created_at`
- `(case_id, created_at)`
- `(actor_user_id, created_at)`

### Optional set

The following are useful but can be deferred if we want to reduce write amplification:

- `actor_user_id` as a single-column index if `(actor_user_id, created_at)` is enough
- `(resource_type, resource_id)` if resource lookups are expected to be frequent
- `(decision, created_at)` if denial analytics become a primary use case

This is already a fairly full index set, so Stage 110 should be careful not to over-index further unless there is a proven query pattern.

## 6. Taxonomy

Use string taxonomy plus app-level validation first. Do not introduce a DB enum in this stage unless there is a strong existing pattern that demands it.

### access_mode

- `summary`
- `detail`
- `admin`

### resource_type

- `case`
- `patient`
- `model_input_snapshot`
- `shadow_inference_run`
- `shadow_inference_output`
- `trace`
- `evidence_node`
- `evidence_edge`
- `recommendation`
- `doctor_feedback`
- `quality_review`
- `orchestration_run`
- `orchestration_step`
- `agent_invocation`
- `model_registry`
- `model_version`

### decision

- `allowed`
- `denied`

### denial_reason

- `missing_token`
- `access_denied`
- `case_not_found`
- `resource_not_found`
- `role_not_allowed`
- `ownership_missing`
- `assignment_revoked`
- `tenant_mismatch`
- `dev_fallback_disabled`

### policy_source

- `owner`
- `primary_doctor`
- `assignment`
- `admin_override`
- `service_internal`
- `dev_fallback`
- `public_metadata`
- `denied_no_policy`

## 7. Privacy / PHI Boundary

This audit table must stay lightweight.

It must not store:

- full clinical payloads
- `mapped_features` raw values
- `source_refs` raw values
- `doctor_provided_features` raw values
- tokens
- secrets
- full request bodies

What it may store:

- small counts
- access mode
- decision branch
- denial reason
- policy source
- request path / method
- lightweight metadata useful for troubleshooting

The access audit table itself should also be access-controlled because it can reveal sensitive usage patterns.

## 8. Relation to Trace / Evidence

Access audit is not clinical trace.

- It is not `trace_events`
- It is not `evidence_nodes`
- It is not `evidence_edges`
- It should not enter the clinical provenance graph

Its job is to explain who accessed which system resource and why, not to represent clinical reasoning.

## 9. Initial Emit Scope Recommendation

Recommended first emit targets:

1. denied attempts
2. `model_input_snapshot` detail reads
3. shadow audit detail reads
4. trace/evidence detail reads

Deferred targets:

- every list request
- high-volume summary reads
- frontend hover/expand events
- model registry public-ish list reads

## 10. Downgrade / Migration Risk

If the table is empty, downgrade is straightforward.

Once it contains rows, downgrade becomes destructive because access history is lost. That is acceptable only if the migration is still in a development or early staging context and the team explicitly accepts the loss.

The downgrade should not affect clinical tables, ownership tables, or shadow audit tables.

## 11. Stage 110 Recommendation

Recommended next step: **A. ORM + Alembic candidate for access_audit_events**

This keeps the next step in the candidate schema lane instead of jumping directly to runtime emit logic.
