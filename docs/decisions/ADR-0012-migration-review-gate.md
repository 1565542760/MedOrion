# ADR-0012: Migration Review Gate

Date: 2026-05-31
Status: Accepted
Source: Main-controller pacing review

## Decision

MedOrion will pause database migration finalization and block Alembic apply until traceability and quality-control review the backend Stage 02/04 schema boundaries.

The project direction remains accepted. The risk is pacing: backend skeleton, database models, traceability contract, and model-service contracts matured quickly, and applying migrations too early could freeze unstable table structures, enums, or trace/evidence fields.

## Required Review Before Apply

Traceability must review:

- core backend trace references
- trace_events fields and taxonomy support
- evidence_nodes/evidence_edges fields and graph support
- quality_reviews fields and attribution support
- missing-value audit states and source distinctions
- recommendation trace_id, inference_task_id, and evidence_chain_id references
- dynamic_state_snapshots trace linkage

## Consequences

Backend may inspect or draft migration DDL, but must not run alembic upgrade until the review passes and the main controller explicitly approves.

Deployment/MLOps must not start backend containers or enable Nginx during this review gate.
