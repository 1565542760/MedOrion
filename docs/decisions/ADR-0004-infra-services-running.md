# ADR-0004: Infra Services Running

Date: 2026-05-31
Status: Accepted status update
Source: Deployment and MLOps infra startup report

## Context

Docker Hub HTTPS access timed out on direct outbound connections. The issue was network path related, not a Compose file or image-name problem.

The deployment thread did not configure a registry mirror. Instead, Docker daemon outbound traffic was routed through the existing local proxy at 127.0.0.1:7897 using a systemd drop-in file.

## Decision

The Docker daemon proxy setup is accepted for the current development server. The configuration path is /etc/systemd/system/docker.service.d/http-proxy.conf.

The official images postgres:16-alpine, redis:7-alpine, and minio/minio:latest were pulled successfully after the proxy was configured.

Infra-only services are accepted as running healthy under /srv/medorion/deploy:

- PostgreSQL: 127.0.0.1:5432
- Redis: 127.0.0.1:6379
- MinIO API: 127.0.0.1:9000
- MinIO Console: 127.0.0.1:9001

Nginx remains disabled and ports 80/443 remain closed.

## Consequences

The project may move from foundation setup into backend and trace/evidence contract planning.

Persistent data now exists under /srv/medorion/data. Destructive cleanup of that directory requires explicit confirmation.

The Docker image pull path depends on the local proxy. If the proxy stops, future image pulls may fail until the proxy is restored or a different registry strategy is approved.

Redis logs reported vm.overcommit_memory guidance; deployment/MLOps should evaluate this later as an operational tuning item, not an architecture blocker.
