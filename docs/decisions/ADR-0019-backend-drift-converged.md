# ADR-0019: Backend Drift Converged

Date: 2026-06-01
Status: Accepted status update
Source: Backend API and Database Stage 05 report plus main-controller verification

## Decision

Backend ORM/database drift convergence is complete.

Verified state:

- alembic current reports 9fd992e59a0c (head)
- alembic check reports No new upgrade operations detected
- /health/live returns 200 alive
- /health/ready returns 200 ready
- /health returns 200 ok

## Implementation Notes

TimestampMixin was aligned to the applied baseline by using nullable=True with server_default=func.now().

Unnecessary ORM field-level index=True declarations were reduced to avoid unplanned single-column index drift. Priority A compound indexes remain the primary index strategy.

inference_tasks.trace_id keeps unique/index behavior with named unique constraint uq_inference_tasks_trace_id.

A Stage 05 drift probe/head revision exists at /srv/medorion/app/backend/alembic/versions/9fd992e59a0c_stage05_drift_probe.py. It did not add business DDL expansion.

## Constraints Preserved

Backend Docker was not started, Nginx was not enabled, model-service was not started, and no diagnosis logic, model training, automatic real-time training, or .pth file operation occurred.

## Consequences

Deployment/MLOps may now draft and test the backend Dockerfile and Compose backend profile with local-only binding. Nginx public routing remains out of scope.
