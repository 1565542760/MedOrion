from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequestV1(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class TokenPairResponseV1(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int


class LogoutRequestV1(BaseModel):
    refresh_token: str = Field(min_length=1)


class RefreshRequestV1(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserMeResponseV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    display_name: str | None = None
    email: EmailStr | None = None
    role: str
    is_active: bool


class AuthEnvelopeV1(BaseModel):
    route: str
    runtime_stub: bool = True
    data: dict


class AuthErrorResponseV1(BaseModel):
    code: str
    message: str


class RefreshTokenRecord(BaseModel):
    user_id: str
    token_hash: str
    expires_at: datetime
