# Deployment Stage 02 Scaffold

Date: 2026-05-31 Asia/Shanghai
Owner thread: MedOrion deployment and MLOps collaboration Codex
Status: Drafted on remote server, pending sudo-enabled installation and /srv materialization

## Current blocker

The SSH user can connect, but non-interactive sudo requires a password. Therefore this stage did not install packages and did not create root-owned /srv/medorion directories.

## Target root

Recommended production root remains:

```text
/srv/medorion
```

Target directory layout:

```text
/srv/medorion/
  app/
    backend/
    frontend/
    model-service/
  deploy/
    docker-compose.yml
    .env
    nginx/
  data/
    postgres/
    redis/
    minio/
  models/
    registry/
    runtime/
    archive/
  logs/
    backend/
    frontend/
    model-service/
    postgres/
    redis/
    minio/
    mlflow/
    nginx/
  backups/
    postgres/
    minio/
    models/
    configs/
  secrets/
```

No real secrets should be stored in versioned files. `/srv/medorion/secrets` is reserved for host-only secret files if later needed.

## Compose draft location

The draft currently lives at:

```text
/home/sygxdg/MedOrion/deploy/docker-compose.yml
/home/sygxdg/MedOrion/deploy/.env.example
/home/sygxdg/MedOrion/deploy/nginx/medorion.conf.template
```

It is designed to be copied under `/srv/medorion/deploy` after sudo access is available.

## Service boundaries requiring architecture confirmation

1. Public exposure strategy: only Nginx should expose 80/443 publicly. Compose services are bound to `127.0.0.1` by default.
2. Backend to model service protocol: draft uses HTTP at `http://model-service:8100`; gRPC or queue-based inference remains open.
3. MinIO exposure: draft keeps API and console local-only. External object access should be reviewed before opening ports.
4. MLflow: reserved under a `mlflow` profile and should not block the first CAP/COP vertical MVP.
5. GPU serving: not enabled. Requires NVIDIA Container Toolkit and a separate validation pass.

## Persistence policy

- PostgreSQL: `/srv/medorion/data/postgres`
- Redis append-only data: `/srv/medorion/data/redis`
- MinIO objects: `/srv/medorion/data/minio`
- Models: `/srv/medorion/models`
- Logs: `/srv/medorion/logs`
- Backups: `/srv/medorion/backups`

## Backup policy draft

- PostgreSQL: nightly `pg_dump` or physical backup once data size grows; retain daily 7, weekly 4, monthly 3.
- MinIO: mirror bucket snapshots to `/srv/medorion/backups/minio` or external storage; retain according to medical data governance policy.
- Models: immutable version directories under `/srv/medorion/models/registry`; back up metadata and artifact checksums.
- Configs: back up sanitized compose, Nginx, and operational scripts. Do not back up plaintext secrets to shared locations.

## Model service MVP policy

- Independent container boundary is mandatory.
- CPU-first default: `MODEL_DEVICE=cpu`.
- Conservative serving defaults: batch size 1, max concurrency 1.
- Model versions must be explicit directories with metadata, checksum, modality, disease-agent compatibility, and approval status.
- Live doctor feedback must not trigger automatic retraining.

## Next executable step when sudo is available

1. Install Docker Engine, Docker Compose Plugin, Nginx, python3-pip, python3-venv, and reviewed Node LTS tooling.
2. Create `/srv/medorion` directory layout.
3. Copy deployment drafts from `/home/sygxdg/MedOrion/deploy` to `/srv/medorion/deploy`.
4. Create `/srv/medorion/deploy/.env` from `.env.example` with real secrets supplied out-of-band.
5. Start infra-only services first: PostgreSQL, Redis, MinIO.
6. Run MinIO bucket initialization profile.
7. Add backend, frontend, and model-service only after their source directories and Dockerfiles exist.
