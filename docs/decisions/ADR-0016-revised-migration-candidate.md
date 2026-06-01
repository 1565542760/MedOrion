# ADR-0016: Revised Stage 04 Migration Candidate

Date: 2026-06-01
Status: Accepted candidate status, not approved for apply
Source: Backend API and Database revised migration report

## Decision

Backend produced a revised Stage 04 migration candidate. The candidate is accepted for focused traceability re-review only. It is not approved for apply.

## Revisions

- Added reassessment_jobs.previous_snapshot_id.
- Added reassessment_jobs.current_snapshot_id.
- Added foreign keys from those fields to dynamic_state_snapshots.id.
- Aligned ORM and migration Priority A compound indexes.
- Added trace_events.parent_event_id self-reference.
- Added trace_events.source_record_type and source_record_id.

## Preserved Constraints

- inference_tasks.trace_id required and unique.
- recommendations.trace_id required.
- recommendations.inference_task_id required.
- case_missing_value_queries.trace_id required.
- value_source distinguishes doctor_provided and default_applied origins.

## Pending Decisions

recommendations.evidence_chain_id remains nullable. MVP service logic must fallback through trace_id plus evidence_refs_json when evidence_chain_id is null.

Enum DB type names remain compact. The main controller must decide whether snake_case normalization is required before apply.

The single baseline revision is acceptable only for an empty-schema baseline initialization. Non-empty target environments require a different migration strategy.

## Consequences

The next active step is focused traceability and quality-control re-review. alembic upgrade remains blocked.
