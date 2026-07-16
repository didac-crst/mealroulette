from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.telegram import TelegramSettings
from mealroulette.schemas.telegram import TelegramSettingsPublic, TelegramSettingsUpdateRequest
from mealroulette.services.telegram_link import TelegramLinkService


class TelegramSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.links = TelegramLinkService(db)

    def list_all_rows(self) -> list[TelegramSettings]:
        return list(self.db.scalars(select(TelegramSettings).order_by(TelegramSettings.id)))

    def get_row(self, household_id: UUID) -> TelegramSettings:
        row = self.db.scalar(
            select(TelegramSettings).where(TelegramSettings.household_id == household_id)
        )
        if row is None:
            row = TelegramSettings(household_id=household_id)
            self.db.add(row)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                row = self.db.scalar(
                    select(TelegramSettings).where(TelegramSettings.household_id == household_id)
                )
                if row is None:
                    raise
            else:
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
            subscriber_count=len(self.links.list_subscribed_chat_ids(row.household_id)),
            daily_reminder_time=row.daily_reminder_time,
            shopping_window_days=row.shopping_window_days,
            include_today=row.include_today,
            include_pantry_items=row.include_pantry_items,
            group_by_category=row.group_by_category,
            timezone=row.timezone,
            last_sent_at=row.last_sent_at,
            last_error=row.last_error,
        )

    def get_public(self, household_id: UUID) -> TelegramSettingsPublic:
        return self.to_public(self.get_row(household_id))

    def update(self, household_id: UUID, payload: TelegramSettingsUpdateRequest) -> TelegramSettingsPublic:
        row = self.get_row(household_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.db.commit()
        self.db.refresh(row)
        return self.to_public(row)

    def require_send_config(
        self,
        row: TelegramSettings | None = None,
        *,
        household_id: UUID | None = None,
        channel: str = "daily",
    ) -> tuple[TelegramSettings, str, list[str]]:
        if row is None:
            if household_id is None:
                raise ValueError("household_id is required when settings row is omitted")
            settings_row = self.get_row(household_id)
        else:
            settings_row = row
        if not settings_row.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram reminders are disabled")
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TELEGRAM_BOT_TOKEN is not configured",
            )
        if channel == "shopping":
            chat_ids = self.links.list_shopping_chat_ids(settings_row.household_id)
            empty_detail = "No linked Telegram users with shopping notifications enabled. Link Telegram in Settings."
        elif channel == "roulette":
            chat_ids = self.links.list_roulette_chat_ids(settings_row.household_id)
            empty_detail = "No linked Telegram users with roulette notifications enabled. Link Telegram in Settings."
        else:
            chat_ids = self.links.list_subscribed_chat_ids(settings_row.household_id)
            empty_detail = (
                "No linked Telegram users with daily reminders enabled. Link Telegram in Settings."
            )
        if not chat_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=empty_detail)
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
