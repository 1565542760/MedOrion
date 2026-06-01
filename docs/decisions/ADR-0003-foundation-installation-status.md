# ADR-0003: Foundation Installation Status

Date: 2026-05-31
Status: Accepted status update
Source: Deployment and MLOps foundation installation report

## Context

The deployment thread used a temporary sudo channel to install foundation packages and create the target deployment directory. The password was not written to project files, environment files, scripts, Markdown, or reports.

## Installed Foundation

- Docker 29.1.3
- Docker Compose 2.40.3
- Nginx 1.24.0
- Node.js v22.22.2
- npm 10.9.7
- python3-pip 24.0
- python3-venv
- ripgrep 14.1.0

The Docker service is active and enabled. The user sygxdg is in the docker group and can run docker directly.

Nginx is installed but intentionally inactive and disabled, so MedOrion has no public HTTP/HTTPS exposure yet.

## Directory Materialization

/srv/medorion now exists with the expected top-level layers: app, deploy, data, models, object-storage, logs, backups, and secrets.

The deployment scaffold has been copied from /home/sygxdg/MedOrion/deploy to /srv/medorion/deploy.

## Current Blocker

Infra-only startup did not complete because Docker image pulls timed out for PostgreSQL, Redis, and MinIO. No infra containers are running, and ports 5432, 6379, 9000, and 9001 are not listening.

## Decision

The foundation installation is accepted as complete, but Stage 1 remains incomplete until PostgreSQL, Redis, and MinIO can be pulled and started.

The next deployment priority is Docker image connectivity: retry pulls, configure a suitable mirror, or prepare a private/local image transfer strategy.

NVIDIA Container Toolkit remains deferred to a later GPU inference stage.
