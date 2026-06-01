import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import RefreshToken, User
from app.modules.auth.dependencies import get_current_user, get_db
from app.modules.auth.schemas import LoginRequestV1, LogoutRequestV1, RefreshRequestV1, TokenPairResponseV1, UserMeResponseV1
from app.modules.auth.security import (
    AuthError,
    auth_http_exception,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])
logger = logging.getLogger('app.auth')
AUTH_STORAGE_NOT_READY = {
    'code': 'auth_storage_not_ready',
    'message': 'Authentication storage is not ready.',
}


@router.post('/login', response_model=TokenPairResponseV1)
def login(payload: LoginRequestV1, db: Session = Depends(get_db)) -> TokenPairResponseV1:
    try:
        user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.exception('auth storage not ready during login lookup')
        raise HTTPException(status_code=503, detail=AUTH_STORAGE_NOT_READY) from exc

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'invalid_credentials', 'message': 'Invalid username or password'})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code': 'user_inactive', 'message': 'User is inactive'})
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'invalid_credentials', 'message': 'Invalid username or password'})

    access_token, access_exp = create_access_token(str(user.id), user.username, user.role)
    refresh_token, refresh_exp = create_refresh_token(str(user.id), user.username, user.role)

    try:
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=refresh_exp,
            )
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception('auth storage not ready during login token persist')
        raise HTTPException(status_code=503, detail=AUTH_STORAGE_NOT_READY) from exc

    expires_in = max(1, int((access_exp - datetime.now(UTC)).total_seconds()))
    return TokenPairResponseV1(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)


@router.post('/logout')
def logout(payload: LogoutRequestV1, db: Session = Depends(get_db)) -> dict:
    try:
        token_hash = hash_token(payload.refresh_token)
        rec = db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).scalar_one_or_none()
        if rec is not None and rec.revoked_at is None:
            rec.revoked_at = datetime.now(UTC)
            db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception('auth storage not ready during logout')
        raise HTTPException(status_code=503, detail=AUTH_STORAGE_NOT_READY) from exc
    return {'status': 'ok', 'route': '/api/v1/auth/logout', 'runtime_stub': True}


@router.get('/me', response_model=UserMeResponseV1)
def me(user: User = Depends(get_current_user)) -> UserMeResponseV1:
    return UserMeResponseV1(
        user_id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@router.post('/refresh', response_model=TokenPairResponseV1)
def refresh(payload: RefreshRequestV1, db: Session = Depends(get_db)) -> TokenPairResponseV1:
    try:
        _ = decode_token(payload.refresh_token, expected_type='refresh')
    except AuthError as exc:
        raise auth_http_exception(exc) from exc

    try:
        token_hash = hash_token(payload.refresh_token)
        token_record = db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.exception('auth storage not ready during refresh lookup')
        raise HTTPException(status_code=503, detail=AUTH_STORAGE_NOT_READY) from exc

    if token_record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'refresh_not_found', 'message': 'Refresh token not found'})
    if token_record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'refresh_revoked', 'message': 'Refresh token revoked'})
    if token_record.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'refresh_expired', 'message': 'Refresh token expired'})

    user = db.execute(select(User).where(User.id == token_record.user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'user_inactive', 'message': 'User not active'})

    try:
        token_record.revoked_at = datetime.now(UTC)
        access_token, access_exp = create_access_token(str(user.id), user.username, user.role)
        new_refresh_token, new_refresh_exp = create_refresh_token(str(user.id), user.username, user.role)
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(new_refresh_token),
                expires_at=new_refresh_exp,
            )
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception('auth storage not ready during refresh token rotation')
        raise HTTPException(status_code=503, detail=AUTH_STORAGE_NOT_READY) from exc

    expires_in = max(1, int((access_exp - datetime.now(UTC)).total_seconds()))
    return TokenPairResponseV1(access_token=access_token, refresh_token=new_refresh_token, expires_in=expires_in)
