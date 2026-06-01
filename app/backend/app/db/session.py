from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def readiness_check_db() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True, 'ok'
    except SQLAlchemyError as exc:
        return False, str(exc)
