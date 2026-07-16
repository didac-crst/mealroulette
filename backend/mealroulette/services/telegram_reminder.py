from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.household import HouseholdNotificationSubscription
from mealroulette.schemas.telegram import TelegramSendResult
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.shopping import ShoppingListService
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_format import format_shopping_list_message
from mealroulette.services.telegram_link import TelegramLinkService
from mealroulette.services.telegram_on_demand import TelegramOnDemandService
from mealroulette.services.telegram_settings import TelegramSettingsService

logger = logging.getLogger(__name__)


class TelegramReminderService:
    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.settings_service = TelegramSettingsService(db)
        self.links = TelegramLinkService(db)
        self.memberships = HouseholdMembershipService(db)
        self.client = client or TelegramClient()

    def _on_demand(self, household_id: UUID) -> TelegramOnDemandService:
        return TelegramOnDemandService(self.db, self.client, household_id=household_id)

    def _bot_token(self) -> str:
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TELEGRAM_BOT_TOKEN is not configured",
            )
        return token

    def _send_one(
        self,
        token: str,
        chat_id: str,
        message: str,
        *,
        parse_mode: str | None = None,
    ) -> None:
        try:
            self.client.send_message(token, chat_id, message, parse_mode=parse_mode)
        except TelegramApiError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

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

        detail = f"Sent to {sent_count} recipient(s)"
        if failures:
            detail += f"; {len(failures)} failed"
        self.settings_service.record_send_success(settings_row)
        return TelegramSendResult(sent=True, detail=detail, recipient_count=sent_count)

    def send_test_message(self, household_id: UUID) -> TelegramSendResult:
        settings_row, token, chat_ids = self.settings_service.require_send_config(household_id=household_id)
        return self._broadcast(
            settings_row,
            token,
            chat_ids,
            "MealRoulette test\n\nTelegram is configured correctly.",
        )

    def send_personal_test_message(self, user_id: UUID, household_id: UUID) -> TelegramSendResult:
        link = self.links.get_link_for_user(user_id)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link Telegram in Settings before sending a test.",
            )
        token = self._bot_token()
        self._send_one(token, link.chat_id, "MealRoulette test\n\nYour Telegram account is linked correctly.")
        return TelegramSendResult(sent=True, detail="Test sent to your linked Telegram.", recipient_count=1)

    def send_daily_reminder(self, household_id: UUID) -> TelegramSendResult:
        settings_row = self.settings_service.get_row(household_id)
        message = self._on_demand(household_id).build_reminder_message(settings_row.shopping_window_days)
        _, token, chat_ids = self.settings_service.require_send_config(settings_row)
        return self._broadcast(settings_row, token, chat_ids, message, parse_mode="HTML")

    def send_personal_daily_reminder(self, user_id: UUID, household_id: UUID) -> TelegramSendResult:
        link = self.links.get_link_for_user(user_id)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link Telegram in Settings before sending a reminder.",
            )
        subscription = self.memberships.ensure_notification_subscription(user_id, household_id)
        token = self._bot_token()
        message = self._on_demand(household_id).build_reminder_message(subscription.shopping_window_days)
        self._send_one(token, link.chat_id, message, parse_mode="HTML")
        subscription.last_reminder_sent_at = datetime.now(UTC)
        self.db.commit()
        return TelegramSendResult(sent=True, detail="Reminder sent to your linked Telegram.", recipient_count=1)

    def send_shopping_list(self, shopping_list_id: int, household_id: UUID) -> TelegramSendResult:
        settings_row = self.settings_service.get_row(household_id)
        shopping_list = ShoppingListService(self.db, household_id).get_list(shopping_list_id)
        message = format_shopping_list_message(
            shopping_list,
            group_by_category=settings_row.group_by_category,
            heading=f"MealRoulette shopping list ({shopping_list.from_date} → {shopping_list.to_date})",
        )
        _, token, chat_ids = self.settings_service.require_send_config(settings_row, channel="shopping")
        return self._broadcast(settings_row, token, chat_ids, message)

    @staticmethod
    def should_send_personal_scheduled(
        subscription: HouseholdNotificationSubscription,
        *,
        now: datetime | None = None,
    ) -> bool:
        if not subscription.notify_daily_reminder:
            return False
        current = now or datetime.now(UTC)
        try:
            zone = ZoneInfo(subscription.timezone)
        except Exception:
            zone = ZoneInfo("UTC")
        local = current.astimezone(zone)
        reminder = subscription.daily_reminder_time
        if (local.hour, local.minute) != (reminder.hour, reminder.minute):
            return False
        if subscription.last_reminder_sent_at is not None:
            last_local = subscription.last_reminder_sent_at.astimezone(zone)
            if last_local.date() == local.date():
                return False
        return True

    def _try_claim_personal_scheduled(
        self,
        subscription_id: UUID,
        *,
        now: datetime,
    ) -> tuple[HouseholdNotificationSubscription, datetime | None] | None:
        """Atomically claim a due subscription. Returns (row, previous_sent_at) or None."""
        row = self.db.scalar(
            select(HouseholdNotificationSubscription)
            .where(HouseholdNotificationSubscription.id == subscription_id)
            .with_for_update()
        )
        if row is None or not self.should_send_personal_scheduled(row, now=now):
            return None
        link = self.links.get_link_for_user(row.user_id)
        if link is None:
            return None
        household_settings = self.settings_service.get_row(row.household_id)
        if not household_settings.enabled:
            return None
        previous = row.last_reminder_sent_at
        row.last_reminder_sent_at = now
        self.db.commit()
        self.db.refresh(row)
        return row, previous

    def _deliver_claimed_personal_reminder(
        self,
        subscription: HouseholdNotificationSubscription,
    ) -> TelegramSendResult:
        link = self.links.get_link_for_user(subscription.user_id)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link Telegram in Settings before sending a reminder.",
            )
        token = self._bot_token()
        message = self._on_demand(subscription.household_id).build_reminder_message(
            subscription.shopping_window_days
        )
        self._send_one(token, link.chat_id, message, parse_mode="HTML")
        return TelegramSendResult(sent=True, detail="Reminder sent to your linked Telegram.", recipient_count=1)

    def _release_claim(
        self,
        subscription_id: UUID,
        previous_sent_at: datetime | None,
    ) -> None:
        row = self.db.get(HouseholdNotificationSubscription, subscription_id)
        if row is None:
            return
        row.last_reminder_sent_at = previous_sent_at
        self.db.commit()

    def run_scheduled_reminder(self, now: datetime | None = None) -> list[TelegramSendResult]:
        results: list[TelegramSendResult] = []
        if not (get_settings().telegram_bot_token or "").strip():
            return results

        current = now or datetime.now(UTC)
        subscription_ids = list(
            self.db.scalars(select(HouseholdNotificationSubscription.id))
        )
        for subscription_id in subscription_ids:
            claimed = self._try_claim_personal_scheduled(subscription_id, now=current)
            if claimed is None:
                continue
            subscription, previous_sent_at = claimed
            try:
                results.append(self._deliver_claimed_personal_reminder(subscription))
            except Exception:
                logger.exception(
                    "Scheduled personal Telegram reminder failed user_id=%s household_id=%s",
                    subscription.user_id,
                    subscription.household_id,
                )
                self._release_claim(subscription.id, previous_sent_at)
        return results
