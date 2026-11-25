import uuid
from datetime import datetime

from sqlmodel import DateTime, Field, SQLModel

from app.models.utils import get_datetime_utc


class FileAsset(SQLModel, table=True):
    __tablename__ = "file_asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    original_name: str = Field(max_length=255)
    stored_name: str = Field(max_length=255, unique=True, index=True)
    content_type: str | None = Field(default=None, max_length=255)
    size: int
    owner_user_id: uuid.UUID | None = Field(default=None, index=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class FileAssetPublic(SQLModel):
    id: uuid.UUID
    original_name: str
    content_type: str | None = None
    size: int
    owner_user_id: uuid.UUID | None = None
    created_at: datetime | None = None


class SystemSetting(SQLModel, table=True):
    __tablename__ = "system_setting"

    key: str = Field(primary_key=True, max_length=100)
    value: str = Field(max_length=4000)
    description: str | None = Field(default=None, max_length=255)
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class SystemSettingUpdate(SQLModel):
    value: str = Field(max_length=4000)
    description: str | None = Field(default=None, max_length=255)


class SystemSettingPublic(SQLModel):
    key: str
    value: str
    description: str | None = None
    updated_at: datetime | None = None
