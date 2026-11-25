import uuid
from datetime import datetime

from pydantic import EmailStr, field_validator
from sqlmodel import DateTime, Field, SQLModel

from app.core.passwords import validate_password_not_common
from app.models.utils import get_datetime_utc


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    _check_password = field_validator("password")(validate_password_not_common)


# 初始化播种专用：密码来自运维配置（.env / GitHub Secrets）而非用户输入，
# 不做弱密码黑名单校验（否则本地/CI 默认的 changethis 演示配置直接建不出账号；
# 生产环境 changethis 已在 Settings 层被拒绝）
class SeedUserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    _check_password = field_validator("password")(validate_password_not_common)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    _check_password = field_validator("password")(validate_password_not_common)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    # 更改绑定邮箱必须复核当前密码（access token 被窃取不足以改登录凭据）
    current_password: str | None = Field(default=None, max_length=128)


class UserDeleteMe(SQLModel):
    # 自助注销是不可逆操作，必须复核当前密码
    current_password: str = Field(min_length=8, max_length=128)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    _check_password = field_validator("new_password")(validate_password_not_common)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    token_version: int = 0
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UserImportResult(SQLModel):
    created_count: int
    errors: list[str]


class UserRolesUpdate(SQLModel):
    role_ids: list[uuid.UUID]
