import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=['argon2', 'bcrypt'], deprecated='auto')


class AuthError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _make_exp(minutes: int = 0, days: int = 0) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes, days=days)


def create_access_token(user_id: str, username: str, role: str) -> tuple[str, datetime]:
    exp = _make_exp(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        'sub': user_id,
        'username': username,
        'role': role,
        'typ': 'access',
        'exp': exp,
        'iat': datetime.now(UTC),
        'jti': uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, exp


def create_refresh_token(user_id: str, username: str, role: str) -> tuple[str, datetime]:
    exp = _make_exp(days=settings.jwt_refresh_token_expire_days)
    payload = {
        'sub': user_id,
        'username': username,
        'role': role,
        'typ': 'refresh',
        'exp': exp,
        'iat': datetime.now(UTC),
        'jti': uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, exp


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as exc:
        raise AuthError(code='invalid_token', message='Token is invalid', status_code=status.HTTP_401_UNAUTHORIZED) from exc

    if payload.get('typ') != expected_type:
        raise AuthError(code='invalid_token_type', message=f'Expected {expected_type} token', status_code=status.HTTP_401_UNAUTHORIZED)

    return payload


def auth_http_exception(exc: AuthError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={'code': exc.code, 'message': exc.message})
