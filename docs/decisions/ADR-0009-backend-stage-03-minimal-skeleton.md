# ADR-0009: Backend Stage 03 Minimal Skeleton

Date: 2026-05-31
Status: Accepted status update
Source: Backend API and Database Stage 03 report

## Decision

The Backend Stage 03 minimal skeleton is accepted.

The skeleton is located at /srv/medorion/app/backend and uses Python venv plus requirements.txt.

Implemented scope:

- FastAPI application skeleton
- /health endpoint verified locally with uvicorn
- app/api/v1, app/core, app/db, and app/modules/* structure
- SQLAlchemy core model skeletons
- key enums ValueSourceType, InferenceTaskStatus, RecommendationStatus, MissingValueQueryStatus
- Alembic skeleton and initial revision 0e36c2285187_stage03_initial_skeleton.py
- config loading for DATABASE_URL, REDIS_URL, S3_ENDPOINT_URL, and MODEL_SERVICE_URL
- structured logging scaffold with trace_id field

Key trace constraints are present in the model skeleton:

- inference_tasks.trace_id required and unique
- recommendations.trace_id required
- recommendations.inference_task_id required
- case_missing_value_queries.trace_id required
- value_source distinguishes doctor-provided values from default-applied values

## Non-Goals Preserved

No complete business logic, real diagnosis logic, model training, model-service startup, backend container startup, Nginx exposure, or automatic real-time training was introduced.

The Alembic revision has not been applied to PostgreSQL, and no destructive migration has been performed.

## Consequences

The next backend step should complete deferred model fields/enums, review/refine the non-destructive migration, add trace_id middleware/logging propagation, and split liveness/readiness.

Deployment/MLOps should wait before starting backend or enabling Nginx until the backend skeleton and Dockerfile/profile are explicitly approved.
