import uuid
from datetime import datetime
from typing import Any

from pydantic import EmailStr
from sqlmodel import JSON, Column, DateTime, Field, SQLModel

from app.models.utils import get_datetime_utc


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Intentionally not a foreign key: audit history must survive user deletion.
    actor_user_id: uuid.UUID | None = Field(default=None, index=True)
    action: str = Field(max_length=100, index=True)
    resource_type: str = Field(max_length=100, index=True)
    resource_id: str | None = Field(default=None, max_length=100, index=True)
    details: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    # 审计查看按时间倒序分页，created_at 必须有索引（否则表增长后全表排序）
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
        index=True,
    )


class AuditLogPublic(SQLModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    # 展示用：LEFT JOIN users 取邮箱；账号已删除时为 null（actor_user_id 仍保留）
    actor_email: EmailStr | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    created_at: datetime | None = None


class AuditLogsPublic(SQLModel):
    data: list[AuditLogPublic]
    count: int
