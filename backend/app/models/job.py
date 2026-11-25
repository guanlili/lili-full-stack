import uuid
from datetime import datetime
from typing import Any

from sqlmodel import JSON, Column, DateTime, Field, SQLModel

from app.models.utils import get_datetime_utc


class Job(SQLModel, table=True):
    __tablename__ = "job"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_type: str = Field(max_length=100, index=True)
    status: str = Field(default="queued", max_length=30, index=True)
    owner_user_id: uuid.UUID | None = Field(default=None, index=True)
    result: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    error: str | None = Field(default=None, max_length=1000)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    finished_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )


class JobPublic(SQLModel):
    id: uuid.UUID
    task_type: str
    status: str
    owner_user_id: uuid.UUID | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime | None = None
    finished_at: datetime | None = None
