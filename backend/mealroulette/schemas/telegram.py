from datetime import datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field


class TelegramSubscriberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: str
    telegram_user_id: str | None = None
    username: str | None = None
    display_name: str | None = None
    subscribed_at: datetime


class TelegramSettingsPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    has_bot_token: bool
    subscriber_count: int
    daily_reminder_time: time
    shopping_window_days: int
    include_today: bool
    include_pantry_items: bool
    group_by_category: bool
    timezone: str
    last_sent_at: datetime | None = None
    last_error: str | None = None


class TelegramSettingsUpdateRequest(BaseModel):
    enabled: bool | None = None
    daily_reminder_time: time | None = None
    shopping_window_days: int | None = Field(default=None, ge=1, le=14)
    include_today: bool | None = None
    include_pantry_items: bool | None = None
    group_by_category: bool | None = None
    timezone: str | None = None


class TelegramSendResult(BaseModel):
    sent: bool
    detail: str
    recipient_count: int = 0
