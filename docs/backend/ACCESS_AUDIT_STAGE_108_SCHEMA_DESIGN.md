# Stage 108: Access Audit Schema Design

## 1. Goals

This stage defines the access audit semantics for the platform so we can track who accessed what, when, and under which access mode, without turning access logs into clinical provenance or recommendation data.

The design is intended to support case, snapshot, shadow audit, trace/evidence, feedback, quality review, and orchestration audit access tracking. It should record the access actor, the target resource, the case/patient/trace binding when relevant, the access mode, the result, and the denial reason when access is blocked.

The goal is not to build a full compliance platform in one step. The goal is to define the event model clearly enough that later helper and API work can emit a lightweight, privacy-aware access record without changing the clinical payload model.

## 2. Non Goals

This stage does not:

- modify code
- modify the database
- run Alembic
- add frontend changes
- write actual audit rows
- change `require_case_access`
- enable real models
- write recommendation data
- write trace events or evidence nodes/edges

## 3. Current State

The platform currently has:

- Stage 104 `access_control.py` helper skeleton
- Stage 106 ownership schema and `case_assignments`
- Stage 107 ownership-aware helper logic with dev fallback compatibility

What is still missing is an audit layer that records access decisions and denied attempts. Today we can decide access, but we do not yet persist a structured access event that explains who touched which resource and why.

## 4. Access Audit Event Concepts

A good access audit event should capture:

- `access_event_id`
- `actor_user_id`
- `actor_role`
- `actor_type`
- `access_mode` (`summary`, `detail`, `admin`)
- `resource_type`
- `resource_id`
- `case_id`
- `patient_id`
- `trace_id`
- `decision` (`allowed`, `denied`)
- `denial_reason`
- `policy_source`
- `request_id`
- `route_path`
- `method`
- `metadata_json`
- `created_at`

Future fields such as IP and user agent can be considered later, but they should not be introduced casually if they expand the privacy burden too early.

## 5. Recommended Table Draft

Suggested table name: `access_audit_events`

Suggested columns:

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
- `created_at` timestamp

Notes:

- This table should not store raw mapped features, source refs, or doctor-provided clinical payload.
- `metadata_json` should only hold lightweight context.
- The table should be optimized for audit review, not for clinical reconstruction.

## 6. Resource Types

The audit design should support at least these resource types:

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

## 7. Decision / Policy Taxonomy

Recommended `decision` values:

- `allowed`
- `denied`

Recommended `denial_reason` values:

- `missing_token`
- `access_denied`
- `case_not_found`
- `resource_not_found`
- `role_not_allowed`
- `ownership_missing`
- `assignment_revoked`
- `tenant_mismatch`
- `dev_fallback_disabled`

Recommended `policy_source` values:

- `owner`
- `primary_doctor`
- `assignment`
- `admin_override`
- `service_internal`
- `dev_fallback`
- `public_metadata`
- `denied_no_policy`

## 8. What Should Be Audited First

The safest rollout sequence is:

1. `model_input_snapshot` detail reads
2. shadow audit detail reads
3. trace/evidence reads
4. denied access attempts
5. case summary/list access
6. model registry detail access
7. orchestration audit reads

Denied access attempts are especially important because they are easy to omit and difficult to reconstruct later.

## 9. Privacy / PHI Boundaries

This access audit must remain a behavior log, not a clinical payload store.

It should not record:

- mapped feature values
- source refs payloads
- doctor-provided clinical raw inputs
- tokens
- secrets

The audit can reference `case_id`, `patient_id`, and `trace_id`, but the access audit itself should also be protected by RBAC because it can reveal sensitive navigation patterns and usage behavior.

IP address and user agent should remain a later-stage consideration. They are useful, but they also expand compliance and retention obligations, so they should not be added casually.

## 10. Relation to Trace / Evidence

Access audit is not the same as clinical trace or evidence.

- It should not write `trace_events`
- It should not write `evidence_nodes`
- It should not write `evidence_edges`
- It should not be mixed into the provenance graph

It exists to explain access decisions and denials, not to represent clinical reasoning.

## 11. Migration Strategy

Recommended Stage 109 direction:

- **A.** access audit migration contract
- **B.** access audit API/helper skeleton design
- **C.** extend the helper so it can optionally emit audit events, without building the table yet
- **D.** pause

Recommended default: **A**.

The strongest next step is to write the migration contract first, then decide whether the helper should emit into a concrete table or remain a stub for another stage.

## 12. Backward Compatibility

The dev/stub stage can start with partial coverage.

- It is acceptable to record only detail reads and denied attempts at first.
- Existing APIs should keep working.
- The platform should not break if some resources are not yet instrumented.
- Dev fallback behavior should remain explicit and not be mistaken for production access policy.

## 13. Risks

Main risks:

- access audit may over-record PHI if payload data is copied in accidentally
- audit rows may become broadly readable and create a second privacy surface
- audit logging can grow quickly and create noise or storage pressure
- denied attempts may be missing if only success paths are instrumented
- dev fallback may be confused with the real production policy unless the boundary is documented carefully

## 14. Stage 109 Recommendation

Recommended next step: **A. access_audit_events migration contract**

This keeps the work in documentation and schema design first, which is the right pace for this part of the platform. After the contract is agreed, the helper and API skeleton can be planned with much less ambiguity.
