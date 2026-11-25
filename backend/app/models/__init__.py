"""领域模型聚合包。

按领域拆分到子模块（user / role / auth / audit / asset / job / access），
job 为模板示例后台任务表，开新坑时由 init_project 脚本一并摘除。
本文件统一 re-export，保持 `from app.models import XxxModel` 这一历史导入路径不变。
所有 table 模型必须在本包被导入后才会注册进 SQLModel.metadata（见 alembic/env.py）。
"""

from sqlmodel import SQLModel

from app.models.access import AccessPublic, PageAccessPublic
from app.models.asset import (
    FileAsset,
    FileAssetPublic,
    SystemSetting,
    SystemSettingPublic,
    SystemSettingUpdate,
)
from app.models.audit import AuditLog, AuditLogPublic, AuditLogsPublic
from app.models.auth import Message, NewPassword, RefreshToken, Token, TokenPayload
from app.models.job import Job, JobPublic
from app.models.role import (
    Permission,
    PermissionPublic,
    Role,
    RoleCreate,
    RoleDetailPublic,
    RolePermission,
    RolePermissionsUpdate,
    RolePublic,
    RolesPublic,
    UserRole,
    UserRolesPublic,
)
from app.models.user import (
    SeedUserCreate,
    UpdatePassword,
    User,
    UserCreate,
    UserDeleteMe,
    UserImportResult,
    UserPublic,
    UserRegister,
    UserRolesUpdate,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

__all__ = [
    "SQLModel",
    "AccessPublic",
    "PageAccessPublic",
    "FileAsset",
    "FileAssetPublic",
    "SystemSetting",
    "SystemSettingPublic",
    "SystemSettingUpdate",
    "AuditLog",
    "AuditLogPublic",
    "AuditLogsPublic",
    "Message",
    "NewPassword",
    "RefreshToken",
    "Token",
    "TokenPayload",
    "Job",
    "JobPublic",
    "Permission",
    "PermissionPublic",
    "Role",
    "RoleCreate",
    "RoleDetailPublic",
    "RolePermission",
    "RolePermissionsUpdate",
    "RolePublic",
    "RolesPublic",
    "UserRole",
    "UserRolesPublic",
    "SeedUserCreate",
    "UpdatePassword",
    "User",
    "UserCreate",
    "UserDeleteMe",
    "UserImportResult",
    "UserPublic",
    "UserRegister",
    "UserRolesUpdate",
    "UserUpdate",
    "UserUpdateMe",
    "UsersPublic",
]
