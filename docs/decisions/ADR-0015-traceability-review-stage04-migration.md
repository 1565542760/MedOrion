# ADR-0015: Traceability Review of Stage 04 Migration Draft

Date: 2026-05-31
Status: Accepted review result
Source: Traceability and Quality-Control migration review report

## Decision

The Stage 04 migration draft conditionally passes trace/evidence/quality main-contract review, but it is not approved for apply.

The draft covers the major traceability structures: trace_events, evidence_nodes, evidence_edges, quality_reviews, missing-value audit, recommendation linkage, and dynamic_state_snapshots. However, required corrections remain before apply can be considered.

## Required Corrections

1. Add explicit reassessment snapshot lineage. The schema must provide a stable queryable relation for previous/current snapshots, such as reassessment_jobs.previous_snapshot_id and reassessment_jobs.current_snapshot_id, or an equivalent relation.
2. Align ORM model indexes with migration Priority A compound indexes to prevent Alembic autogenerate drift.

## Recommended Corrections or Decisions

- Decide whether recommendations.evidence_chain_id remains nullable with service-layer enforcement or becomes not null for MVP.
- Consider self-reference or application-level validation for trace_events.parent_event_id.
- Consider source_record_type/source_record_id on trace_events if source-record queries are expected.
- Keep quality_reviews.resolved_at; expose closed_at as API alias if needed.
- Consider assigned reviewer fields later if QC assignment enters MVP.
- Decide whether PostgreSQL enum type names should use snake_case before apply.
- Confirm that the single baseline revision is intended only for an empty schema or approved baseline process.

## Consequences

Backend may produce a revised migration candidate. alembic upgrade remains blocked. Deployment/MLOps must not start backend containers or enable Nginx.
