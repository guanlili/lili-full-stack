import uuid
from datetime import datetime

from sqlmodel import DateTime, Field, SQLModel

from app.models.user import UserBase  # noqa: F401  re-export 供下游使用
from app.models.utils import get_datetime_utc


class RoleBase(SQLModel):
    name: str = Field(min_length=1, max_length=100, index=True, unique=True)
    description: str | None = Field(default=None, max_length=255)


class Role(RoleBase, table=True):
    __tablename__ = "role"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class RoleCreate(RoleBase):
    pass


class RolePublic(RoleBase):
    id: uuid.UUID
    created_at: datetime | None = None


class RolesPublic(SQLModel):
    data: list[RolePublic]
    count: int


class PermissionBase(SQLModel):
    codename: str = Field(min_length=1, max_length=100, index=True, unique=True)
    description: str | None = Field(default=None, max_length=255)


class Permission(PermissionBase, table=True):
    __tablename__ = "permission"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class PermissionPublic(PermissionBase):
    id: uuid.UUID


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permission"

    role_id: uuid.UUID = Field(foreign_key="role.id", primary_key=True)
    permission_id: uuid.UUID = Field(foreign_key="permission.id", primary_key=True)


class UserRole(SQLModel, table=True):
    __tablename__ = "user_role"

    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    role_id: uuid.UUID = Field(foreign_key="role.id", primary_key=True)


class RolePermissionsUpdate(SQLModel):
    permissions: list[str]


class RoleDetailPublic(RolePublic):
    permissions: list[str]
    is_default: bool
    user_count: int


class UserRolesPublic(SQLModel):
    data: list[RolePublic]
