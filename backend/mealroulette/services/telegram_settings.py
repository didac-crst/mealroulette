from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.telegram import TELEGRAM_SETTINGS_ID, TelegramSettings
from mealroulette.schemas.telegram import TelegramSettingsPublic, TelegramSettingsUpdateRequest
from mealroulette.services.telegram_subscribers import TelegramSubscriberService


class TelegramSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.subscribers = TelegramSubscriberService(db)

    def get_row(self) -> TelegramSettings:
        row = self.db.get(TelegramSettings, TELEGRAM_SETTINGS_ID)
        if row is None:
            row = TelegramSettings(id=TELEGRAM_SETTINGS_ID)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row

    @staticmethod
    def bot_token_configured() -> bool:
        token = get_settings().telegram_bot_token or ""
        return bool(token.strip())

    def to_public(self, row: TelegramSettings) -> TelegramSettingsPublic:
        return TelegramSettingsPublic(
            enabled=row.enabled,
            has_bot_token=self.bot_token_configured(),
            subscriber_count=len(self.subscribers.list_subscribers()),
            daily_reminder_time=row.daily_reminder_time,
            shopping_window_days=row.shopping_window_days,
            include_today=row.include_today,
            include_pantry_items=row.include_pantry_items,
            group_by_category=row.group_by_category,
            timezone=row.timezone,
            last_sent_at=row.last_sent_at,
            last_error=row.last_error,
        )

    def get_public(self) -> TelegramSettingsPublic:
        return self.to_public(self.get_row())

    def update(self, payload: TelegramSettingsUpdateRequest) -> TelegramSettingsPublic:
        row = self.get_row()
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.db.commit()
        self.db.refresh(row)
        return self.to_public(row)

    def require_send_config(self, row: TelegramSettings | None = None) -> tuple[TelegramSettings, str, list[str]]:
        settings_row = row or self.get_row()
        if not settings_row.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram reminders are disabled")
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TELEGRAM_BOT_TOKEN is not configured",
            )
        chat_ids = self.subscribers.list_chat_ids()
        if not chat_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Telegram subscribers yet. Send /subscribe to the bot.",
            )
        return settings_row, token, chat_ids

    def record_send_success(self, row: TelegramSettings) -> None:
        row.last_sent_at = datetime.now(UTC)
        row.last_error = None
        self.db.commit()

    def record_send_failure(self, row: TelegramSettings, error: str) -> None:
        row.last_error = error[:2000]
        self.db.commit()

    def save_update_offset(self, row: TelegramSettings, update_id: int) -> None:
        if row.last_update_id is None or update_id > row.last_update_id:
            row.last_update_id = update_id
            self.db.commit()

    @staticmethod
    def should_send_scheduled(
        row: TelegramSettings,
        *,
        has_bot_token: bool,
        subscriber_count: int,
        now: datetime | None = None,
    ) -> bool:
        if not row.enabled or not has_bot_token or subscriber_count == 0:
            return False
        current = now or datetime.now(UTC)
        try:
            zone = ZoneInfo(row.timezone)
        except Exception:
            zone = ZoneInfo("UTC")
        local = current.astimezone(zone)
        reminder = row.daily_reminder_time
        if (local.hour, local.minute) != (reminder.hour, reminder.minute):
            return False
        if row.last_sent_at is not None:
            last_local = row.last_sent_at.astimezone(zone)
            if last_local.date() == local.date():
                return False
        return True
