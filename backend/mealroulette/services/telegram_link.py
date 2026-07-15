from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.household import HouseholdNotificationSubscription
from mealroulette.models.telegram import TelegramLinkToken, TelegramUserLink
from mealroulette.services.telegram_bot_info import resolve_bot_username
from mealroulette.core.config import get_settings


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_telegram_link_deep_url(token: str) -> str | None:
    bot_token = (get_settings().telegram_bot_token or "").strip()
    username = resolve_bot_username(bot_token) if bot_token else None
    if not username:
        configured = (get_settings().telegram_bot_username or "").strip().lstrip("@")
        username = configured or None
    if not username:
        return None
    return f"https://t.me/{username}?start=link_{token}"


class TelegramLinkService:
    TOKEN_TTL_MINUTES = 15

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_link_token(self, user_id: UUID) -> tuple[TelegramLinkToken, str]:
        token = secrets.token_urlsafe(24)
        row = TelegramLinkToken(
            id=uuid4(),
            user_id=user_id,
            token_hash=_hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(minutes=self.TOKEN_TTL_MINUTES),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row, token

    def link_chat(
        self,
        token: str,
        *,
        chat_id: str,
        telegram_user_id: str | None,
        username: str | None,
        display_name: str | None,
    ) -> TelegramUserLink:
        token_hash = _hash_token(token)
        row = self.db.scalar(select(TelegramLinkToken).where(TelegramLinkToken.token_hash == token_hash))
        if row is None or row.used_at is not None or row.expires_at < datetime.now(UTC):
            raise ValueError("Invalid or expired link token")
        # One MealRoulette user → one Telegram link. Same Telegram chat may link many users.
        existing_user = self.db.scalar(select(TelegramUserLink).where(TelegramUserLink.user_id == row.user_id))
        if existing_user is not None:
            self.db.delete(existing_user)
            self.db.flush()
        link = TelegramUserLink(
            id=uuid4(),
            user_id=row.user_id,
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            username=username,
            display_name=display_name,
        )
        row.used_at = datetime.now(UTC)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def get_link_for_user(self, user_id: UUID) -> TelegramUserLink | None:
        return self.db.scalar(select(TelegramUserLink).where(TelegramUserLink.user_id == user_id))

    def unlink_user(self, user_id: UUID) -> bool:
        link = self.get_link_for_user(user_id)
        if link is None:
            return False
        self.db.delete(link)
        self.db.commit()
        return True

    def list_subscribed_chat_ids(self, household_id: UUID) -> list[str]:
        rows = self.db.execute(
            select(TelegramUserLink.chat_id)
            .join(
                HouseholdNotificationSubscription,
                HouseholdNotificationSubscription.user_id == TelegramUserLink.user_id,
            )
            .where(
                HouseholdNotificationSubscription.household_id == household_id,
                HouseholdNotificationSubscription.notify_daily_reminder.is_(True),
            )
        )
        return list(dict.fromkeys(chat_id for chat_id, in rows.all()))

    def list_roulette_chat_ids(self, household_id: UUID) -> list[str]:
        rows = self.db.execute(
            select(TelegramUserLink.chat_id)
            .join(
                HouseholdNotificationSubscription,
                HouseholdNotificationSubscription.user_id == TelegramUserLink.user_id,
            )
            .where(
                HouseholdNotificationSubscription.household_id == household_id,
                HouseholdNotificationSubscription.notify_roulette.is_(True),
            )
        )
        return list(dict.fromkeys(chat_id for chat_id, in rows.all()))
