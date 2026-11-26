from datetime import datetime

from sqlmodel import DateTime, Field, SQLModel

from app.models.utils import get_datetime_utc


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
