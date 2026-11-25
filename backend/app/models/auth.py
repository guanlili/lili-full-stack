import uuid
from datetime import datetime

from pydantic import field_validator
from sqlmodel import DateTime, Field, SQLModel

from app.core.passwords import validate_password_not_common
from app.models.utils import get_datetime_utc


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    # refresh token 不再经响应体下发（HttpOnly Cookie，见 login 路由），字段保留作兼容
    refresh_token: str | None = None


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: uuid.UUID
    ver: int
    typ: str


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    _check_password = field_validator("new_password")(validate_password_not_common)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    token_hash: str = Field(max_length=64, unique=True, index=True)
    user_id: uuid.UUID = Field(index=True)
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))
    revoked_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
