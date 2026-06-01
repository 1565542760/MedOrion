import json
import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request

from app.config import settings
from app.routers.api import router as api_router

logging.basicConfig(
    level=getattr(logging, settings.model_service_log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(message)s',
)
logger = logging.getLogger('model-service')

app = FastAPI(title='MedOrion Model Service Stub', version='0.1.0-stage02-stub')
app.include_router(api_router)


@app.middleware('http')
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get('x-request-id') or str(uuid.uuid4())
    trace_id = None

    if request.method in {'POST', 'PUT', 'PATCH'}:
        try:
            body_bytes = await request.body()
            if body_bytes:
                payload = json.loads(body_bytes)
                if isinstance(payload, dict):
                    trace_id = payload.get('trace_id')

            async def receive() -> dict[str, Any]:
                return {'type': 'http.request', 'body': body_bytes, 'more_body': False}

            request = Request(request.scope, receive)
        except Exception:
            trace_id = None

    logger.info(
        'request_started request_id=%s trace_id=%s method=%s path=%s',
        request_id,
        trace_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)
    response.headers['x-request-id'] = request_id

    logger.info(
        'request_completed request_id=%s trace_id=%s method=%s path=%s status=%s',
        request_id,
        trace_id,
        request.method,
        request.url.path,
        response.status_code,
    )
    return response
