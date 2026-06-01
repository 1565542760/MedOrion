# ADR-0002: Compose Service Boundaries and Exposure Policy

Date: 2026-05-31
Status: Accepted for MVP scaffold
Source: Deployment Stage 02 scaffold

## Context

The deployment thread produced a Docker Compose scaffold under /home/sygxdg/MedOrion/deploy. Privileged installation and /srv/medorion creation are blocked because non-interactive sudo requires a password.

## Decision

The Stage 02 Compose scaffold is accepted as the MVP deployment draft.

PostgreSQL, Redis, and MinIO are base infrastructure services. backend, frontend, model-service, and MLflow must remain profile-gated until their source directories and Dockerfiles exist.

All Compose service ports must bind to 127.0.0.1 by default. Nginx is the single intended public HTTP/HTTPS entry point on 80/443. MinIO API and console remain local-only unless a later security review approves exposure.

The backend may call the small-model service over HTTP at http://model-service:8100 for MVP. gRPC or queue-based inference remains open for later heavier workloads.

The small-model service is a separate container, CPU-first by default, with conservative serving defaults and read-only model mounts.

## Consequences

This preserves the global architecture boundary between backend orchestration and model inference. It also keeps public exposure narrow while infrastructure is immature.

The immediate blocker is operational rather than architectural: sudo access must be resolved before foundation installation, /srv/medorion creation, and infra-only service startup.
