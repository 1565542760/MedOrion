# MedOrion model-service (Stage 02 Stub)

This service is a **stub-only** model-service for MedOrion Stage 02.

## Scope

- Implements API contract validation endpoints only.
- Does not load any real .pth model files.
- Does not train models.
- Does not perform real medical inference.
- CPU-first assumptions only.

## Endpoints

- GET /health
- GET /models
- GET /models/{model_version_id}
- POST /validate-input
- POST /infer

## Run with venv

`ash
cd /srv/medorion/app/model-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8100
`

## Run with Docker

`ash
cd /srv/medorion/app/model-service
docker build -t medorion-model-service-stub:stage02 .
docker run --rm -p 127.0.0.1:8100:8100 medorion-model-service-stub:stage02
`

## Notes

- Always pass upstream 	race_id for /infer.
- Missing 	race_id returns 	race_id_missing.
- Request logs include equest_id (x-request-id header or generated) and 	race_id (from body when present).
