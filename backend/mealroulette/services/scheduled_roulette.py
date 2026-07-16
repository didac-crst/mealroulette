from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.planning import MealPlan, MealPlanItem
from mealroulette.schemas.telegram import TelegramSendResult
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler_settings import SchedulerSettingsService
from mealroulette.services.scheduler_service import SchedulerService
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_format_html import format_planning_message_html
from mealroulette.services.telegram_on_demand import TelegramOnDemandService, local_today
from mealroulette.services.telegram_settings import TelegramSettingsService


@dataclass(frozen=True)
class ScheduledRouletteResult:
    meal_plan_id: int
    week_start_date: date
    assignments_count: int
    warnings: list[str]
    telegram: TelegramSendResult | None = None


class ScheduledRouletteService:
    def __init__(
        self,
        db: Session,
        client: TelegramClient | None = None,
        household_id: UUID = DEFAULT_HOUSEHOLD_ID,
    ) -> None:
        self.db = db
        self.household_id = household_id
        self.settings_service = SchedulerSettingsService(db)
        self.planning_service = PlanningService(db, household_id=household_id)
        self.scheduler_service = SchedulerService(db, household_id=household_id)
        self.client = client or TelegramClient()
        self.on_demand_service = TelegramOnDemandService(db, self.client, household_id=household_id)
        self.telegram_settings_service = TelegramSettingsService(db)

    def run_scheduled(self, now: datetime | None = None) -> ScheduledRouletteResult | None:
        settings_row = self.settings_service.get_row(self.household_id)
        if not self.settings_service.should_run_scheduled(settings_row, now=now):
            return None
        return self._execute(settings_row)

    def run_now(self, household_id: UUID | None = None) -> ScheduledRouletteResult:
        if household_id is not None and household_id != self.household_id:
            scoped = ScheduledRouletteService(self.db, client=self.client, household_id=household_id)
            return scoped.run_now()
        return self._execute(self.settings_service.get_row(self.household_id))

    def _execute(self, settings_row) -> ScheduledRouletteResult:
        telegram_settings = self.telegram_settings_service.get_row(self.household_id)
        reference_today = local_today(telegram_settings)
        week_start = self.target_week_start(reference_today, settings_row.target_week_offset)
        plan = self.planning_service.get_or_create_plan(week_start)

        try:
            result, _variety = self.scheduler_service.generate_week(plan.id, today=reference_today)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Scheduled roulette failed"
            self.settings_service.record_roulette_failure(str(detail), settings_row)
            raise
        except Exception as exc:
            self.settings_service.record_roulette_failure(str(exc), settings_row)
            raise

        self.settings_service.record_roulette_success(settings_row)
        telegram_result = None
        if settings_row.notify_telegram:
            telegram_result = self._notify_telegram(settings_row, week_start)

        return ScheduledRouletteResult(
            meal_plan_id=plan.id,
            week_start_date=week_start,
            assignments_count=len(result.assignments),
            warnings=result.warnings,
            telegram=telegram_result,
        )

    @staticmethod
    def target_week_start(reference_date: date, target_week_offset: int) -> date:
        current_week = PlanningService.week_start_for(reference_date)
        return current_week + timedelta(weeks=target_week_offset)

    def _notify_telegram(self, settings_row, week_start: date) -> TelegramSendResult | None:
        if not TelegramSettingsService.bot_token_configured():
            return None

        chat_ids = self.telegram_settings_service.links.list_roulette_chat_ids(self.household_id)
        if not chat_ids:
            return None

        token = (get_settings().telegram_bot_token or "").strip()
        days = settings_row.notify_planning_days
        from_date = week_start
        to_date = week_start + timedelta(days=days - 1)
        items = list(
            self.db.scalars(
                select(MealPlanItem)
                .join(MealPlan, MealPlanItem.meal_plan_id == MealPlan.id)
                .where(
                    MealPlan.household_id == self.household_id,
                    MealPlanItem.date >= from_date,
                    MealPlanItem.date <= to_date,
                )
                .options(*PlanningService._meal_plan_item_trait_options())
                .order_by(MealPlanItem.date, MealPlanItem.meal_slot)
            )
        )
        public_items = [self.planning_service.to_item_public(item) for item in items]
        message = format_planning_message_html(
            public_items,
            from_date=from_date,
            to_date=to_date,
            days=days,
            bot_username=self.on_demand_service.bot_username(),
            heading="New roulette",
        )

        telegram_row = self.telegram_settings_service.get_row(self.household_id)
        failures: list[str] = []
        sent_count = 0
        for chat_id in chat_ids:
            try:
                self.client.send_message(token, chat_id, message, parse_mode="HTML")
                sent_count += 1
            except TelegramApiError as exc:
                failures.append(f"{chat_id}: {exc}")

        if sent_count == 0:
            error = "; ".join(failures) if failures else "No Telegram messages sent"
            self.telegram_settings_service.record_send_failure(telegram_row, error)
            return TelegramSendResult(sent=False, detail=error, recipient_count=0)

        detail = f"Sent to {sent_count} recipient(s)"
        if failures:
            detail += f"; {len(failures)} failed"
        self.telegram_settings_service.record_send_success(telegram_row)
        return TelegramSendResult(sent=True, detail=detail, recipient_count=sent_count)
