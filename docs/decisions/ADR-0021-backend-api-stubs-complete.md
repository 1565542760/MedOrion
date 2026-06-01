# ADR-0021: Backend API Stubs Complete

Date: 2026-06-01
Status: Accepted status update
Source: Backend API and Database Stage 07 report plus main-controller verification

## Decision

Backend Stage 07 API stubs and request logging are accepted as complete.

The backend now exposes safe placeholder API stubs for patient, case, asset/input, missing-value, recommendation, inference-task, reassessment, model-registry, feedback, trace, evidence-chain, and quality-review paths.

Pydantic schema stubs exist across the corresponding modules.

Application-layer request logging records method, path, status, duration_ms, request_id, and trace_id. The main controller verified request_id and trace_id propagation in container logs.

## Boundaries Preserved

Stubs do not implement real business CRUD, diagnosis logic, model calls, training, automatic real-time training, schema changes, or .pth file operations.

Nginx remains disabled. frontend and model-service remain stopped.

## Consequences

Frontend Doctor Workbench Stage 01 may begin. The frontend should initialize under /srv/medorion/app/frontend and use local backend stubs through a mock API adapter. Public exposure through Nginx remains blocked.
