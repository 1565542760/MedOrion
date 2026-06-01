from contextvars import ContextVar
import uuid

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='-')
trace_id_ctx: ContextVar[str] = ContextVar('trace_id', default='-')


def generate_request_id() -> str:
    return f'req_{uuid.uuid4().hex}'
