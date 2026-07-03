from __future__ import annotations

import logging

from collections.abc import Callable

from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_on_demand import (
    MAX_ON_DEMAND_DAYS,
    TelegramOnDemandService,
    parse_days_arg,
)
from mealroulette.services.telegram_recipe import parse_recipe_start_payload
from mealroulette.services.telegram_settings import TelegramSettingsService
from mealroulette.services.telegram_subscribers import TelegramSubscriberService

logger = logging.getLogger(__name__)

# v0.4 has a single distribution list; more lists can be added when new message types ship.
DISTRIBUTION_LISTS: dict[str, str] = {
    "shopping": "daily shopping reminders",
}
DEFAULT_LIST_KEY = "shopping"

SUBSCRIBE_COMMANDS = {"/subscribe", "/start"}
UNSUBSCRIBE_COMMANDS = {"/unsubscribe", "/stop"}
HELP_COMMANDS = {"/help"}
PLANNING_COMMANDS = {"/planning"}
REMINDER_COMMANDS = {"/reminder"}
SHOPPING_COMMANDS = {"/shopping"}
RECIPE_COMMANDS = {"/recipe"}


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


def _list_label(list_key: str) -> str:
    return DISTRIBUTION_LISTS.get(list_key, list_key)


def _available_lists_text() -> str:
    lines = [f"• {key} — {label}" for key, label in DISTRIBUTION_LISTS.items()]
    return "\n".join(lines)


class TelegramUpdateService:
    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.client = client or TelegramClient()
        self.settings_service = TelegramSettingsService(db)
        self.subscriber_service = TelegramSubscriberService(db)
        self.on_demand_service = TelegramOnDemandService(db)

    def poll_once(self) -> int:
        token = (get_settings().telegram_bot_token or "").strip()
        if not token:
            return 0

        row = self.settings_service.get_row()
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
                "MealRoulette bot\n\n"
                "Distribution lists:\n"
                f"{_available_lists_text()}\n\n"
                "Commands:\n"
                "• /subscribe [list] — join a list (default: shopping)\n"
                "• /unsubscribe [list] — leave a list\n"
                "• /planning [days] — planned meals (default: 3 days)\n"
                "• /reminder [days] — planning + ingredients (default: 3 days)\n"
                "• /shopping [days] — shopping totals only (default: 3 days)\n"
                "• Tap a dish name in planning to open its full recipe\n"
                "• /help — this message",
            )
            return True

        if command in SUBSCRIBE_COMMANDS:
            recipe_id = parse_recipe_start_payload(_start_payload(text) or "")
            if recipe_id is not None:
                return self._send_recipe_message(token, chat_id, recipe_id)

            list_key = self._resolve_list_key(_command_args(text), chat_id=chat_id, token=token)
            if list_key is None:
                return True
            _, created = self.subscriber_service.subscribe(
                chat_id=chat_id,
                telegram_user_id=telegram_user_id,
                username=username if isinstance(username, str) else None,
                display_name=display_name,
            )
            label = _list_label(list_key)
            if created:
                reply = (
                    f"You are now subscribed to MealRoulette {label}.\n"
                    "Send /unsubscribe to leave this list."
                )
            else:
                reply = (
                    f"You are already subscribed to MealRoulette {label}.\n"
                    "Send /unsubscribe to leave this list."
                )
            self.client.send_message(token, chat_id, reply)
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
            list_key = self._resolve_list_key(_command_args(text), chat_id=chat_id, token=token, required=False)
            if list_key is None:
                return True
            removed = self.subscriber_service.unsubscribe(chat_id)
            label = _list_label(list_key)
            if removed:
                self.client.send_message(token, chat_id, f"You have been unsubscribed from MealRoulette {label}.")
            else:
                self.client.send_message(
                    token,
                    chat_id,
                    f"You were not subscribed to MealRoulette {label}.\nSend /subscribe to join.",
                )
            return True

        return False

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

    def _resolve_list_key(
        self,
        args: list[str],
        *,
        chat_id: str,
        token: str,
        required: bool = True,
    ) -> str | None:
        if not args:
            return DEFAULT_LIST_KEY
        list_key = args[0]
        if list_key in DISTRIBUTION_LISTS:
            return list_key
        self.client.send_message(
            token,
            chat_id,
            "Unknown list. Available lists:\n"
            f"{_available_lists_text()}\n\n"
            f"Example: /subscribe {DEFAULT_LIST_KEY}",
        )
        return None if required else DEFAULT_LIST_KEY
