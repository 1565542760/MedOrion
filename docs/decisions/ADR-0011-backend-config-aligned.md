# ADR-0011: Backend Configuration Aligned

Date: 2026-05-31
Status: Accepted status update
Source: Deployment and MLOps backend credential alignment report

## Decision

Backend local configuration has been aligned with the running infrastructure without exposing secret values in documentation.

The deploy .env contains POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD. The backend local .env was created on the server and aligned with PostgreSQL, Redis, MinIO, and a local model-service placeholder.

Health check status after alignment:

- /health/live: 200 alive
- /health/ready: 200 ready
- /health: 200 ok

Alembic can connect to PostgreSQL. alembic check reports that the target database is not up to date, which is expected because migrations have not been applied.

## Constraints

No Nginx enablement, backend Docker startup, Compose changes, systemd changes, or alembic upgrade occurred in this step.

Secret values must remain out of reports and documentation.

## Consequences

The backend thread is unblocked to run Alembic autogenerate/refinement for review only. Migrations must still not be applied until the main controller explicitly approves.
