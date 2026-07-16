from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.catalog import Dish, Recipe, RecipeStep
from mealroulette.models.cooking import CookingTimerAlert, CookingTimerAlertStatus
from mealroulette.models.user import User
from mealroulette.schemas.cooking import CookingTimerAlertCreateRequest, CookingTimerAlertPublic
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_subscribers import TelegramSubscriberService


class CookingTimerAlertService:
    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.client = client or TelegramClient()
        self.subscribers = TelegramSubscriberService(db)

    @staticmethod
    def telegram_delivery_available() -> bool:
        token = (get_settings().telegram_bot_token or "").strip()
        return bool(token)

    def _delivery_targets(self) -> tuple[str, list[str]] | None:
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            return None
        chat_ids = self.subscribers.list_chat_ids()
        if not chat_ids:
            return None
        return token, chat_ids

    def _load_recipe_context(self, recipe_id: int, recipe_step_id: int) -> tuple[Dish, Recipe, RecipeStep]:
        step = self.db.get(RecipeStep, recipe_step_id)
        if step is None or step.recipe_id != recipe_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe step not found")
        recipe = self.db.get(Recipe, recipe_id)
        if recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
        dish = self.db.get(Dish, recipe.dish_id)
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        return dish, recipe, step

    def _cancel_pending_for_step(self, user_id: UUID, recipe_step_id: int) -> None:
        rows = self.db.scalars(
            select(CookingTimerAlert).where(
                CookingTimerAlert.user_id == user_id,
                CookingTimerAlert.recipe_step_id == recipe_step_id,
                CookingTimerAlert.status == CookingTimerAlertStatus.pending.value,
            )
        ).all()
        for row in rows:
            row.status = CookingTimerAlertStatus.cancelled.value
            row.updated_at = datetime.now(UTC)

    def schedule(self, user: User, payload: CookingTimerAlertCreateRequest) -> CookingTimerAlertPublic:
        dish, recipe, step = self._load_recipe_context(payload.recipe_id, payload.recipe_step_id)
        if step.step_number != payload.step_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Step number mismatch")

        self._cancel_pending_for_step(user.id, payload.recipe_step_id)
        now = datetime.now(UTC)
        row = CookingTimerAlert(
            user_id=user.id,
            recipe_id=recipe.id,
            recipe_step_id=step.id,
            step_number=step.step_number,
            dish_name=dish.name,
            recipe_name=recipe.variant_name,
            fire_at=now + timedelta(seconds=payload.remaining_seconds),
            status=CookingTimerAlertStatus.pending.value,
            created_at=now,
            updated_at=now,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_public(row)

    def cancel(self, user: User, alert_id: int) -> bool:
        row = self.db.get(CookingTimerAlert, alert_id)
        if row is None or row.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cooking timer alert not found")
        if row.status != CookingTimerAlertStatus.pending.value:
            return False
        row.status = CookingTimerAlertStatus.cancelled.value
        row.updated_at = datetime.now(UTC)
        self.db.commit()
        return True

    def cancel_for_step(self, user: User, recipe_step_id: int) -> int:
        rows = self.db.scalars(
            select(CookingTimerAlert).where(
                CookingTimerAlert.user_id == user.id,
                CookingTimerAlert.recipe_step_id == recipe_step_id,
                CookingTimerAlert.status == CookingTimerAlertStatus.pending.value,
            )
        ).all()
        if not rows:
            return 0
        now = datetime.now(UTC)
        for row in rows:
            row.status = CookingTimerAlertStatus.cancelled.value
            row.updated_at = now
        self.db.commit()
        return len(rows)

    @staticmethod
    def _format_message(row: CookingTimerAlert) -> str:
        return (
            "MealRoulette timer\n\n"
            f"Step {row.step_number} done — {row.dish_name} ({row.recipe_name})"
        )

    def _send_alert(self, row: CookingTimerAlert) -> None:
        targets = self._delivery_targets()
        if targets is None:
            raise RuntimeError("Telegram is not configured or has no subscribers")
        token, chat_ids = targets
        message = self._format_message(row)
        failures: list[str] = []
        sent_count = 0
        for chat_id in chat_ids:
            try:
                self.client.send_message(token, chat_id, message)
                sent_count += 1
            except TelegramApiError as exc:
                failures.append(f"{chat_id}: {exc}")
        if sent_count == 0:
            raise RuntimeError("; ".join(failures) if failures else "No messages sent")

    def process_due(self, now: datetime | None = None) -> int:
        current = now or datetime.now(UTC)
        due_rows = self.db.scalars(
            select(CookingTimerAlert)
            .where(
                CookingTimerAlert.status == CookingTimerAlertStatus.pending.value,
                CookingTimerAlert.fire_at <= current,
            )
            .order_by(CookingTimerAlert.fire_at)
        ).all()
        processed = 0
        for row in due_rows:
            try:
                self._send_alert(row)
            except Exception as exc:
                row.status = CookingTimerAlertStatus.failed.value
                row.last_error = str(exc)[:2000]
            else:
                row.status = CookingTimerAlertStatus.sent.value
                row.last_error = None
            row.updated_at = datetime.now(UTC)
            processed += 1
        if processed:
            self.db.commit()
        return processed

    def _to_public(self, row: CookingTimerAlert) -> CookingTimerAlertPublic:
        delivery = self._delivery_targets()
        return CookingTimerAlertPublic(
            id=row.id,
            recipe_id=row.recipe_id,
            recipe_step_id=row.recipe_step_id,
            step_number=row.step_number,
            dish_name=row.dish_name,
            recipe_name=row.recipe_name,
            fire_at=row.fire_at,
            status=row.status,
            telegram_scheduled=delivery is not None and row.status == CookingTimerAlertStatus.pending.value,
        )
