# ADR-0013: Stage 04 Migration Draft Review Gate

Date: 2026-05-31
Status: Accepted review status
Source: Backend API and Database Stage 04 migration report plus main-controller pacing review

## Decision

The Stage 04 Alembic migration draft is accepted as a review artifact only. It is not approved for apply.

The draft file is /srv/medorion/app/backend/alembic/versions/a9d28e4978dd_stage04_schema_baseline_non_destructive.py.

It reportedly covers the 18 MVP tables, enum types, foreign keys, indexes, and key trace constraints. alembic upgrade was not executed, and the database remains intentionally not up to date.

## Required Review

Traceability and quality-control must review before apply approval:

- trace_events fields and taxonomy support
- evidence_nodes/evidence_edges graph support
- quality_reviews closure and attribution support
- missing-value audit state and value source fields
- recommendation trace_id, inference_task_id, and evidence_chain_id linkage
- dynamic_state_snapshots trace linkage

## Known Review Notes

Enum type names currently use compact naming such as valuesourcetype instead of the snake_case style used in planning documents. Naming should be reviewed before apply.

The versions directory reportedly has a single effective baseline revision. Because no migration has been applied yet, a baseline may be acceptable, but revision lineage must be confirmed before apply.

## Consequences

Backend must not run alembic upgrade. Deployment/MLOps must not start backend containers or enable Nginx. The next active thread is traceability and quality-control review.
