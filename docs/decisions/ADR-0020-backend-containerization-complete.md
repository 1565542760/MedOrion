# ADR-0020: Backend Containerization Complete

Date: 2026-06-01
Status: Accepted status update
Source: Deployment and MLOps Stage 06 report plus main-controller verification

## Decision

Backend containerization is accepted as complete for local-only development use.

Created:

- /srv/medorion/app/backend/Dockerfile
- /srv/medorion/app/backend/.dockerignore

The image medorion/backend:local builds successfully. The backend container medorion-backend-1 starts successfully and binds only to 127.0.0.1:8000.

Container health endpoints return 200 for /health/live, /health/ready, and /health.

## Boundaries Preserved

Nginx remains inactive and disabled. frontend, model-service, and MLflow remain stopped. No Alembic command or schema change occurred during this stage. No diagnosis logic, model training, automatic real-time training, or .pth file operation occurred.

## Follow-Up

Backend API stub work should add or verify application-layer request logging so request_id and trace_id appear in logs. Current container logs mainly show uvicorn access logs.
