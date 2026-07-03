from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mealroulette.schemas.telegram import TelegramSendResult
from mealroulette.services.shopping import ShoppingListService
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_format import format_shopping_list_message
from mealroulette.services.telegram_on_demand import TelegramOnDemandService
from mealroulette.services.telegram_settings import TelegramSettingsService


class TelegramReminderService:
    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.settings_service = TelegramSettingsService(db)
        self.shopping_service = ShoppingListService(db)
        self.client = client or TelegramClient()
        self.on_demand_service = TelegramOnDemandService(db, self.client)

    def _broadcast(
        self,
        settings_row,
        token: str,
        chat_ids: list[str],
        message: str,
        *,
        parse_mode: str | None = None,
    ) -> TelegramSendResult:
        failures: list[str] = []
        sent_count = 0
        for chat_id in chat_ids:
            try:
                self.client.send_message(token, chat_id, message, parse_mode=parse_mode)
                sent_count += 1
            except TelegramApiError as exc:
                failures.append(f"{chat_id}: {exc}")

        if sent_count == 0:
            error = "; ".join(failures) if failures else "No messages sent"
            self.settings_service.record_send_failure(settings_row, error)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=error)

        detail = f"Sent to {sent_count} subscriber(s)"
        if failures:
            detail += f"; {len(failures)} failed"
        self.settings_service.record_send_success(settings_row)
        return TelegramSendResult(sent=True, detail=detail, recipient_count=sent_count)

    def send_test_message(self) -> TelegramSendResult:
        settings_row, token, chat_ids = self.settings_service.require_send_config()
        return self._broadcast(
            settings_row,
            token,
            chat_ids,
            "MealRoulette test\n\nTelegram is configured correctly.",
        )

    def send_daily_reminder(self, *, _today: date | None = None) -> TelegramSendResult:
        settings_row = self.settings_service.get_row()
        message = self.on_demand_service.build_reminder_message(settings_row.shopping_window_days)
        _, token, chat_ids = self.settings_service.require_send_config(settings_row)
        return self._broadcast(settings_row, token, chat_ids, message, parse_mode="HTML")

    def send_shopping_list(self, shopping_list_id: int) -> TelegramSendResult:
        settings_row = self.settings_service.get_row()
        shopping_list = self.shopping_service.get_list(shopping_list_id)
        message = format_shopping_list_message(
            shopping_list,
            group_by_category=settings_row.group_by_category,
            heading=f"MealRoulette shopping list ({shopping_list.from_date} → {shopping_list.to_date})",
        )
        _, token, chat_ids = self.settings_service.require_send_config(settings_row)
        return self._broadcast(settings_row, token, chat_ids, message)

    def run_scheduled_reminder(self, now: datetime | None = None) -> TelegramSendResult | None:
        settings_row = self.settings_service.get_row()
        if not TelegramSettingsService.should_send_scheduled(
            settings_row,
            has_bot_token=TelegramSettingsService.bot_token_configured(),
            subscriber_count=len(self.settings_service.subscribers.list_subscribers()),
            now=now,
        ):
            return None
        return self.send_daily_reminder()
