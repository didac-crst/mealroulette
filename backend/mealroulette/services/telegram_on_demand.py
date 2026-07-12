from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.core.config import get_settings
from mealroulette.models.planning import MealPlanItem
from mealroulette.models.telegram import TelegramSettings
from mealroulette.services.planning import PlanningService
from mealroulette.services.planning_rules import meal_slot_sort_key
from mealroulette.services.shopping import ShoppingListService
from mealroulette.services.telegram_bot_info import resolve_bot_username
from mealroulette.services.telegram_client import TelegramClient
from mealroulette.services.telegram_format_html import (
    format_planning_message_html,
    format_reminder_message_html,
    format_shopping_message_html,
)
from mealroulette.services.telegram_recipe import format_recipe_message_html, load_recipe_detail
from mealroulette.services.telegram_settings import TelegramSettingsService

DEFAULT_ON_DEMAND_DAYS = 3
MAX_ON_DEMAND_DAYS = 14


def parse_days_arg(args: list[str], *, default: int = DEFAULT_ON_DEMAND_DAYS) -> int | None:
    if not args:
        return default
    try:
        days = int(args[0])
    except ValueError:
        return None
    if days < 1 or days > MAX_ON_DEMAND_DAYS:
        return None
    return days


def local_today(settings_row: TelegramSettings) -> date:
    try:
        zone = ZoneInfo(settings_row.timezone)
    except Exception:
        zone = ZoneInfo("UTC")
    return datetime.now(UTC).astimezone(zone).date()


class TelegramOnDemandService:
    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.client = client or TelegramClient()
        self.settings_service = TelegramSettingsService(db)
        self.shopping_service = ShoppingListService(db)

    def bot_username(self) -> str | None:
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            return None
        return resolve_bot_username(token, self.client)

    def _window(self, days: int) -> tuple[date, date]:
        settings_row = self.settings_service.get_row()
        from_date = local_today(settings_row)
        to_date = from_date + timedelta(days=days - 1)
        return from_date, to_date

    def list_planning_items(self, from_date: date, to_date: date):
        items = list(
            self.db.scalars(
                select(MealPlanItem)
                .where(
                    MealPlanItem.date >= from_date,
                    MealPlanItem.date <= to_date,
                )
                .options(
                    selectinload(MealPlanItem.dish),
                    selectinload(MealPlanItem.recipe),
                )
            )
        )
        items.sort(key=lambda item: (item.date, meal_slot_sort_key(item.meal_slot)))
        return [PlanningService.to_item_public(item) for item in items]

    def build_planning_message(self, days: int) -> str:
        from_date, to_date = self._window(days)
        items = self.list_planning_items(from_date, to_date)
        return format_planning_message_html(
            items,
            from_date=from_date,
            to_date=to_date,
            days=days,
            bot_username=self.bot_username(),
        )

    def build_reminder_message(self, days: int) -> str:
        from_date, to_date = self._window(days)
        planning_items = self.list_planning_items(from_date, to_date)
        preview = self.shopping_service.generate_preview(from_date, days, exclude_pantry=False)
        return format_reminder_message_html(
            preview,
            planning_items,
            from_date=from_date,
            to_date=to_date,
            days=days,
            bot_username=self.bot_username(),
        )

    def build_recipe_message(self, recipe_id: int) -> str | None:
        detail = load_recipe_detail(self.db, recipe_id)
        if detail is None:
            return None
        return format_recipe_message_html(detail)

    def build_shopping_message(self, days: int) -> str:
        from_date, to_date = self._window(days)
        preview = self.shopping_service.generate_preview(from_date, days, exclude_pantry=False)
        return format_shopping_message_html(
            preview,
            from_date=from_date,
            to_date=to_date,
            days=days,
        )
