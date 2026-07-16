from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.household import HouseholdMembership, HouseholdNotificationSubscription
from mealroulette.models.telegram import TelegramLinkToken, TelegramUserLink
from mealroulette.services.telegram_bot_info import resolve_bot_username


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
        now = datetime.now(UTC)
        # Atomically claim the token (same pattern as household invitation claim).
        row = self.db.scalars(
            update(TelegramLinkToken)
            .where(
                TelegramLinkToken.token_hash == token_hash,
                TelegramLinkToken.used_at.is_(None),
                TelegramLinkToken.expires_at >= now,
            )
            .values(used_at=now)
            .returning(TelegramLinkToken)
        ).first()
        if row is None:
            raise ValueError("Invalid or expired link token")

        # One MealRoulette user → one Telegram link. Same Telegram chat may link many users.
        existing_user = self.db.scalar(select(TelegramUserLink).where(TelegramUserLink.user_id == row.user_id))
        if existing_user is not None:
            self.db.delete(existing_user)
            self.db.flush()

        # One Telegram identity must not map to multiple MealRoulette users.
        if telegram_user_id:
            for stale in self.db.scalars(
                select(TelegramUserLink).where(
                    TelegramUserLink.telegram_user_id == telegram_user_id,
                    TelegramUserLink.user_id != row.user_id,
                )
            ):
                self.db.delete(stale)
            self.db.flush()

        link = TelegramUserLink(
            id=uuid4(),
            user_id=row.user_id,
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            username=username,
            display_name=display_name,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def get_link_for_user(self, user_id: UUID) -> TelegramUserLink | None:
        return self.db.scalar(select(TelegramUserLink).where(TelegramUserLink.user_id == user_id))

    def resolve_link_for_sender(self, chat_id: str, telegram_user_id: str | None) -> TelegramUserLink | None:
        """Fail closed unless exactly one link matches chat + Telegram identity."""
        if not telegram_user_id:
            return None
        links = list(
            self.db.scalars(
                select(TelegramUserLink).where(
                    TelegramUserLink.chat_id == chat_id,
                    TelegramUserLink.telegram_user_id == telegram_user_id,
                )
            )
        )
        if len(links) != 1:
            return None
        return links[0]

    def unlink_user(self, user_id: UUID) -> bool:
        link = self.get_link_for_user(user_id)
        if link is None:
            return False
        self.db.delete(link)
        self.db.commit()
        return True

    def _list_chat_ids(self, household_id: UUID, *, notify_column) -> list[str]:
        rows = self.db.execute(
            select(TelegramUserLink.chat_id)
            .join(
                HouseholdNotificationSubscription,
                HouseholdNotificationSubscription.user_id == TelegramUserLink.user_id,
            )
            .join(
                HouseholdMembership,
                (HouseholdMembership.user_id == TelegramUserLink.user_id)
                & (HouseholdMembership.household_id == HouseholdNotificationSubscription.household_id),
            )
            .where(
                HouseholdNotificationSubscription.household_id == household_id,
                HouseholdMembership.active.is_(True),
                notify_column.is_(True),
            )
        )
        return list(dict.fromkeys(chat_id for chat_id, in rows.all()))

    def list_subscribed_chat_ids(self, household_id: UUID) -> list[str]:
        return self._list_chat_ids(
            household_id,
            notify_column=HouseholdNotificationSubscription.notify_daily_reminder,
        )

    def list_shopping_chat_ids(self, household_id: UUID) -> list[str]:
        return self._list_chat_ids(
            household_id,
            notify_column=HouseholdNotificationSubscription.notify_shopping,
        )

    def list_roulette_chat_ids(self, household_id: UUID) -> list[str]:
        return self._list_chat_ids(
            household_id,
            notify_column=HouseholdNotificationSubscription.notify_roulette,
        )

    def list_linked_recipients(self, household_id: UUID) -> list[TelegramUserLink]:
        rows = self.db.scalars(
            select(TelegramUserLink)
            .join(
                HouseholdNotificationSubscription,
                HouseholdNotificationSubscription.user_id == TelegramUserLink.user_id,
            )
            .join(
                HouseholdMembership,
                (HouseholdMembership.user_id == TelegramUserLink.user_id)
                & (HouseholdMembership.household_id == HouseholdNotificationSubscription.household_id),
            )
            .where(
                HouseholdNotificationSubscription.household_id == household_id,
                HouseholdMembership.active.is_(True),
            )
            .order_by(TelegramUserLink.linked_at)
        )
        seen: set[UUID] = set()
        result: list[TelegramUserLink] = []
        for link in rows:
            if link.user_id in seen:
                continue
            seen.add(link.user_id)
            result.append(link)
        return result
