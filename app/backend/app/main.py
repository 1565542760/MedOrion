from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import trace_context_middleware
from app.db.session import readiness_check_db

configure_logging()

app = FastAPI(title=settings.app_name)
app.middleware('http')(trace_context_middleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get('/health', tags=['health'])
def health() -> dict:
    return {'status': 'ok', 'service': 'backend', 'env': settings.app_env}


@app.get('/health/live', tags=['health'])
def health_live() -> dict:
    return {'status': 'alive', 'service': 'backend'}


@app.get('/health/ready', tags=['health'])
def health_ready() -> dict:
    db_ok, db_message = readiness_check_db()
    status = 'ready' if db_ok else 'degraded'
    return {
        'status': status,
        'service': 'backend',
        'checks': {
            'config_loaded': True,
            'database': {'ok': db_ok, 'detail': db_message},
        },
    }
