from collections.abc import Callable
import logging
import time

from fastapi import Request, Response

from app.core.trace import generate_request_id, request_id_ctx, trace_id_ctx

logger = logging.getLogger('app.request')


async def trace_context_middleware(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get('x-request-id') or generate_request_id()
    trace_id = request.headers.get('x-trace-id') or '-'

    request.state.request_id = request_id
    request.state.trace_id = trace_id

    request_id_token = request_id_ctx.set(request_id)
    trace_id_token = trace_id_ctx.set(trace_id)

    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            'request completed method=%s path=%s status=%s duration_ms=%s request_id=%s trace_id=%s',
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
            request_id,
            trace_id,
        )
        request_id_ctx.reset(request_id_token)
        trace_id_ctx.reset(trace_id_token)

    response.headers['x-request-id'] = request_id
    if trace_id != '-':
        response.headers['x-trace-id'] = trace_id
    return response
