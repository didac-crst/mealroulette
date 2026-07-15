from __future__ import annotations

import logging

from collections.abc import Callable

from sqlalchemy.orm import Session

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, Household
from mealroulette.models.user import User
from mealroulette.core.config import get_settings
from mealroulette.services.household import HouseholdService
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_html_utils import esc
from mealroulette.services.telegram_link import TelegramLinkService
from mealroulette.services.telegram_on_demand import (
    MAX_ON_DEMAND_DAYS,
    TelegramOnDemandService,
    parse_days_arg,
)
from mealroulette.services.telegram_recipe import parse_recipe_start_payload
from mealroulette.services.telegram_settings import TelegramSettingsService

logger = logging.getLogger(__name__)

HELP_COMMANDS = {"/help"}
START_COMMANDS = {"/start"}
SUBSCRIBE_COMMANDS = {"/subscribe"}
UNSUBSCRIBE_COMMANDS = {"/unsubscribe", "/stop"}
PLANNING_COMMANDS = {"/planning"}
REMINDER_COMMANDS = {"/reminder"}
SHOPPING_COMMANDS = {"/shopping"}
RECIPE_COMMANDS = {"/recipe"}

_LINK_MIGRATE_MESSAGE = (
    "MealRoulette no longer uses /subscribe.\n"
    "Open Settings → Telegram in the app and scan the QR code (or open the link) to connect your account."
)


def _normalize_command(text: str) -> str:
    parts = text.strip().split()
    if not parts:
        return ""
    command = parts[0].lower()
    if "@" in command:
        command = command.split("@", 1)[0]
    return command


def _command_args(text: str) -> list[str]:
    parts = text.strip().split()
    return [part.lower() for part in parts[1:]]


def _command_raw_args(text: str) -> list[str]:
    parts = text.strip().split()
    return parts[1:]


def _start_payload(text: str) -> str | None:
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[1].strip()


class TelegramUpdateService:
    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.client = client or TelegramClient()
        self.settings_service = TelegramSettingsService(db)
        self.link_service = TelegramLinkService(db)
        self.on_demand_service = TelegramOnDemandService(db)

    def poll_once(self) -> int:
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            return 0

        row = self.settings_service.get_row(DEFAULT_HOUSEHOLD_ID)
        offset = row.last_update_id + 1 if row.last_update_id is not None else None
        try:
            updates = self.client.get_updates(token, offset=offset)
        except TelegramApiError:
            logger.exception("Telegram getUpdates failed")
            return 0

        processed = 0
        for update in updates:
            update_id = update.get("update_id")
            try:
                if self._handle_update(token, update):
                    processed += 1
            except Exception:
                logger.exception("Failed to handle Telegram update %s", update_id)
            finally:
                if isinstance(update_id, int):
                    self.settings_service.save_update_offset(row, update_id)
        return processed

    def _handle_update(self, token: str, update: dict) -> bool:
        message = update.get("message") or update.get("edited_message")
        if not isinstance(message, dict):
            return False
        text = message.get("text")
        if not isinstance(text, str):
            return False

        command = _normalize_command(text)
        chat = message.get("chat")
        if not isinstance(chat, dict) or "id" not in chat:
            return False
        chat_id = str(chat["id"])

        from_user = message.get("from") if isinstance(message.get("from"), dict) else {}
        username = from_user.get("username")
        telegram_user_id = str(from_user["id"]) if "id" in from_user else None
        display_name = " ".join(
            part
            for part in [from_user.get("first_name"), from_user.get("last_name")]
            if isinstance(part, str) and part.strip()
        ) or None

        if command in HELP_COMMANDS:
            self.client.send_message(
                token,
                chat_id,
                "<b>MealRoulette</b>\n\n"
                "Link from Settings → Telegram in the app, then:\n"
                "• /planning [days] — planned meals\n"
                "• /reminder [days] — planning + ingredients\n"
                "• /shopping [days] — shopping totals\n"
                "• Tap a dish in planning for the full recipe\n"
                "• /help — this message\n\n"
                "<i>Days default to 3.</i>",
                parse_mode="HTML",
            )
            return True

        if command in START_COMMANDS:
            start_payload = _start_payload(text) or ""
            if start_payload.startswith("link_"):
                return self._handle_link_token(
                    token,
                    chat_id,
                    start_payload.removeprefix("link_"),
                    telegram_user_id=telegram_user_id,
                    username=username if isinstance(username, str) else None,
                    display_name=display_name,
                )

            recipe_id = parse_recipe_start_payload(start_payload)
            if recipe_id is not None:
                return self._send_recipe_message(token, chat_id, recipe_id)

            self.client.send_message(token, chat_id, _LINK_MIGRATE_MESSAGE)
            return True

        if command in SUBSCRIBE_COMMANDS:
            self.client.send_message(token, chat_id, _LINK_MIGRATE_MESSAGE)
            return True

        if command in PLANNING_COMMANDS:
            return self._handle_days_command(
                token,
                chat_id,
                text,
                command_name="planning",
                builder=self.on_demand_service.build_planning_message,
            )

        if command in REMINDER_COMMANDS:
            return self._handle_days_command(
                token,
                chat_id,
                text,
                command_name="reminder",
                builder=self.on_demand_service.build_reminder_message,
            )

        if command in SHOPPING_COMMANDS:
            return self._handle_days_command(
                token,
                chat_id,
                text,
                command_name="shopping",
                builder=self.on_demand_service.build_shopping_message,
            )

        if command in RECIPE_COMMANDS:
            raw_args = _command_raw_args(text)
            if not raw_args or not raw_args[0].isdigit():
                self.client.send_message(token, chat_id, "Usage: /recipe <recipe id>")
                return True
            return self._send_recipe_message(token, chat_id, int(raw_args[0]))

        if command in UNSUBSCRIBE_COMMANDS:
            self.client.send_message(
                token,
                chat_id,
                "MealRoulette no longer uses /unsubscribe.\n"
                "Unlink Telegram from Settings → Telegram in the app to stop account notifications.",
            )
            return True

        return False

    def _handle_link_token(
        self,
        token: str,
        chat_id: str,
        link_token: str,
        *,
        telegram_user_id: str | None,
        username: str | None,
        display_name: str | None,
    ) -> bool:
        try:
            link = self.link_service.link_chat(
                link_token,
                chat_id=chat_id,
                telegram_user_id=telegram_user_id,
                username=username,
                display_name=display_name,
            )
        except ValueError:
            self.client.send_message(
                token,
                chat_id,
                "This link token is invalid or expired. Generate a new one from MealRoulette settings.",
            )
            return True

        user = self.db.get(User, link.user_id)
        membership = HouseholdService(self.db).active_household_membership(link.user_id)
        username = esc(user.username if user else "unknown")
        lines = [
            "<b>Welcome to MealRoulette</b>",
            "",
            "You're linked.",
            f"Signed in as <b>{username}</b>",
        ]
        if membership is not None:
            household = self.db.get(Household, membership.household_id)
            household_name = household.name if household is not None else "your household"
            lines.append(f"Household <b>{esc(household_name)}</b>")
        lines.extend(
            [
                "",
                "Notifications follow Settings → Telegram.",
            ]
        )
        self.client.send_message(token, chat_id, "\n".join(lines), parse_mode="HTML")
        return True

    def _handle_days_command(
        self,
        token: str,
        chat_id: str,
        text: str,
        *,
        command_name: str,
        builder: Callable[[int], str],
    ) -> bool:
        days = parse_days_arg(_command_args(text))
        if days is None:
            self.client.send_message(
                token,
                chat_id,
                f"Days must be a number between 1 and {MAX_ON_DEMAND_DAYS}. Example: /{command_name} 3",
            )
            return True
        message = builder(days)
        self.client.send_message(token, chat_id, message, parse_mode="HTML")
        return True

    def _send_recipe_message(self, token: str, chat_id: str, recipe_id: int) -> bool:
        message = self.on_demand_service.build_recipe_message(recipe_id)
        if message is None:
            self.client.send_message(token, chat_id, "Recipe not found.")
            return True
        self.client.send_message(token, chat_id, message, parse_mode="HTML")
        return True
