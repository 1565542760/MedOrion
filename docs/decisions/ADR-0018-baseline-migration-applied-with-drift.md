# ADR-0018: Baseline Migration Applied With Remaining Drift

Date: 2026-06-01
Status: Accepted status update
Source: Backend API and Database restricted apply report

## Decision

The restricted Alembic baseline migration was applied to the current development database.

Preflight confirmed the target was the local development PostgreSQL database and that public business tables were absent. alembic upgrade head was executed.

The first apply attempt failed because enum types were both manually created and auto-created during table creation. Backend removed the manual enum create/drop block and reran alembic upgrade head successfully.

The database is now at revision a9d28e4978dd.

## Applied Scope

The baseline applies 18 MVP tables, enum types, Priority A indexes, key trace constraints, reassessment snapshot lineage, and trace_events parent self-reference.

No backend Docker container, Nginx, model-service, diagnosis logic, model training, automatic real-time training, or .pth operation was touched.

## Remaining Issue

alembic check still reports new upgrade operations detected. This indicates ORM/database drift after apply.

Known drift sources:

- created_at/updated_at nullable/default mismatch between ORM and applied migration
- ORM field-level index=True declarations not represented in the applied baseline migration

## Consequences

Stage 05 drift convergence is required before backend deployment work. Deployment/MLOps must not start backend containers or enable Nginx yet.
