# ADR-0001: MVP Deployment Foundation

Date: 2026-05-31
Status: Accepted for MVP planning
Source: Deployment-specialized thread read-only server inspection

## Context

The MedOrion remote server has Ubuntu 24.04.4, Python 3.12.3, Git 2.43.0, and an NVIDIA RTX 3050 Laptop GPU with 4 GiB VRAM. Docker, Docker Compose, Nginx, Node, npm, pnpm, pip3, and nvcc are not currently installed or not found in PATH. The /home partition has about 79 GiB available while the root partition has about 397 GiB available.

The current /home/sygxdg/MedOrion directory contains only architecture documentation and is not yet a Git repository.

## Decision

MedOrion MVP deployment should use Docker Compose as the deployment foundation.

The recommended deployment root is /srv/medorion. Code, persistent service data, model artifacts, object storage, logs, and backups must be separated by directory layer.

The backend should run as a containerized FastAPI service. PostgreSQL, Redis, and MinIO should be Compose-managed dependencies for the MVP. The frontend should be built separately and served either by an Nginx container or host Nginx behind HTTPS reverse proxy.

Small-model inference must run as a separate service container instead of being embedded in the FastAPI backend. The deployment should reserve mounted model storage with explicit model version directories. NVIDIA Container Toolkit is required before GPU container inference is treated as available.

MLflow or an equivalent model/experiment tracking service should be reserved in the deployment plan, but it should not block the earliest CAP/COP vertical MVP.

## Architecture Impact

Disease extensibility: each disease agent can later attach one or more model-serving containers without changing the backend monolith boundary.

Multimodal support: CT, MRI, EMR, clinical tables, labs, and future wearable data can share object storage and metadata persistence while modality adapters remain application-level modules.

Traceability: PostgreSQL should persist trace_id, evidence-chain metadata, model versions, prompt/template versions, missing-value handling, and doctor feedback. MinIO should store large artifacts referenced by evidence records.

MVP scope: CAP/COP remains the first vertical demonstration, but the deployment layout must not hard-code CAP/COP as the only disease task.

## Constraints

The available GPU has only 4 GiB VRAM. Initial model-serving strategy must prioritize lightweight models, quantized models, careful batching, and CPU fallback.

Continuous learning remains offline and governed. Deployment must not include automatic real-time training from live doctor feedback.

## Follow-Up Tasks

1. Deployment thread may install Docker Engine, Docker Compose Plugin, Nginx, Node LTS, and Python pip/venv tooling after explicit confirmation.
2. Deployment thread may create /srv/medorion with separated subdirectories for app, data, models, object storage, logs, and backups.
3. Deployment thread may draft a Compose file with backend, frontend, PostgreSQL, Redis, MinIO, reserved MLflow, and reserved small-model service entries.
4. Architecture thread must review any service boundary changes before they become global facts.
