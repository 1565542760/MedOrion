from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import SessionLocal
from app.modules.auth.security import AuthError, auth_http_exception, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'missing_token', 'message': 'Missing bearer token'})

    try:
        payload = decode_token(credentials.credentials, expected_type='access')
    except AuthError as exc:
        raise auth_http_exception(exc) from exc

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'invalid_token', 'message': 'Token missing subject'})

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'user_inactive', 'message': 'User not active'})
    return user


def require_roles(allowed_roles: list[str]) -> Callable:
    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code': 'forbidden', 'message': 'Insufficient role'})
        return user

    return _dependency
