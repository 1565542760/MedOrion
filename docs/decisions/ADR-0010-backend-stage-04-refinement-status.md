# ADR-0010: Backend Stage 04 Refinement Status

Date: 2026-05-31
Status: Accepted status update
Source: Backend API and Database Stage 04 report

## Decision

Backend Stage 04 refinement is accepted as mostly complete, with one configuration blocker.

Completed:

- Expanded enums for case, modality, inference, feedback, reassessment, missing-value, trace/evidence, and quality-review domains.
- Deferred model field skeletons for ClinicalObservation, LabResult, EmrDocument, ModelRegistry, ModelVersion, ReassessmentJob, DynamicStateSnapshot, TraceEvent, EvidenceNode, EvidenceEdge, and QualityReview.
- request_id and trace_id context/middleware.
- structured logging with request_id and trace_id.
- /health/live, /health/ready, and /health endpoints.

Health behavior:

- /health/live returns 200 alive.
- /health returns 200 compatibility status.
- /health/ready returns 200 degraded because DATABASE_URL credentials fail authentication.

Alembic status:

- Stage 04 revision exists: a9d28e4978dd_stage04_schema_baseline_non_destructive.py.
- It remains unapplied.
- Autogenerate is blocked by PostgreSQL credential mismatch.

## Constraint

Canonical business trace_id generation remains owned by inference_task service. Middleware may propagate request and trace context but must not replace business trace_id generation rules.

## Consequences

Deployment/MLOps should safely align backend local DATABASE_URL with the running PostgreSQL credentials without exposing secrets. Then backend can rerun readiness and refine Alembic autogenerate, still without applying migrations until main-controller approval.

No backend Docker container, model-service container, Nginx exposure, real diagnosis logic, model training, or automatic real-time training is approved by this ADR.
