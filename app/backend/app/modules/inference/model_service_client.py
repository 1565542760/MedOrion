import json
import logging
import socket
from typing import Any
from urllib import error, request

from app.core.config import settings

logger = logging.getLogger('app.inference.model_service')


class ModelServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502, details: dict[str, Any] | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def infer_with_model_service(payload: dict[str, Any], *, request_id: str, trace_id: str) -> dict[str, Any]:
    url = settings.model_service_url.rstrip('/') + '/infer'
    body = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'x-request-id': request_id,
        'x-trace-id': trace_id,
    }

    logger.info('model-service call start url=%s trace_id=%s inference_task_id=%s', url, trace_id, payload.get('inference_task_id'))

    req = request.Request(url=url, data=body, headers=headers, method='POST')
    timeout_s = 8.0

    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
            logger.info('model-service call success status=%s trace_id=%s model_invocation_id=%s', resp.status, trace_id, data.get('model_invocation_id'))
            return data
    except error.HTTPError as exc:
        raw_err = exc.read().decode('utf-8') if exc.fp else '{}'
        detail: dict[str, Any] = {}
        try:
            parsed = json.loads(raw_err)
            if isinstance(parsed, dict):
                detail = parsed.get('detail', parsed)
        except json.JSONDecodeError:
            detail = {'raw': raw_err}

        code = detail.get('code', 'model_service_http_error') if isinstance(detail, dict) else 'model_service_http_error'
        message = detail.get('message', f'model-service http error: {exc.code}') if isinstance(detail, dict) else f'model-service http error: {exc.code}'
        logger.warning('model-service call failed status=%s code=%s trace_id=%s', exc.code, code, trace_id)
        raise ModelServiceError(code=code, message=message, status_code=exc.code, details={'detail': detail}) from exc
    except (error.URLError, socket.timeout, TimeoutError) as exc:
        logger.warning('model-service unavailable/timeout trace_id=%s error=%s', trace_id, str(exc))
        code = 'model_service_timeout' if isinstance(exc, socket.timeout | TimeoutError) else 'model_service_unavailable'
        status_code = 504 if code == 'model_service_timeout' else 503
        raise ModelServiceError(code=code, message='model-service unavailable or timeout', status_code=status_code) from exc
