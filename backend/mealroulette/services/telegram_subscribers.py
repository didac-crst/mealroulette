from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.telegram import TelegramSubscriber
from mealroulette.schemas.telegram import TelegramSubscriberPublic


class TelegramSubscriberService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_subscribers(self) -> list[TelegramSubscriber]:
        return list(self.db.scalars(select(TelegramSubscriber).order_by(TelegramSubscriber.subscribed_at)))

    def list_public(self) -> list[TelegramSubscriberPublic]:
        return [TelegramSubscriberPublic.model_validate(row) for row in self.list_subscribers()]

    def list_chat_ids(self) -> list[str]:
        return [row.chat_id for row in self.list_subscribers()]

    def subscribe(
        self,
        *,
        chat_id: str,
        telegram_user_id: str | None = None,
        username: str | None = None,
        display_name: str | None = None,
    ) -> tuple[TelegramSubscriber, bool]:
        existing = self.db.scalar(select(TelegramSubscriber).where(TelegramSubscriber.chat_id == chat_id))
        if existing is not None:
            existing.telegram_user_id = telegram_user_id
            existing.username = username
            existing.display_name = display_name
            self.db.commit()
            self.db.refresh(existing)
            return existing, False
        row = TelegramSubscriber(
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            username=username,
            display_name=display_name,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row, True

    def unsubscribe(self, chat_id: str) -> bool:
        row = self.db.scalar(select(TelegramSubscriber).where(TelegramSubscriber.chat_id == chat_id))
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True
