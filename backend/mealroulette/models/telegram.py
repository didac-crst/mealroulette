from datetime import datetime, time
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base

TELEGRAM_SETTINGS_ID = 1


class TelegramSettings(Base):
    __tablename__ = "telegram_settings"
    __table_args__ = (UniqueConstraint("household_id", name="uq_telegram_settings_household_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    daily_reminder_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    shopping_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    include_today: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_pantry_items: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    group_by_category: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Paris")
    last_update_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TelegramUserLink(Base):
    __tablename__ = "telegram_user_links"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_telegram_user_links_user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TelegramLinkToken(Base):
    __tablename__ = "telegram_link_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_telegram_link_tokens_token_hash"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TelegramLoginOtp(Base):
    __tablename__ = "telegram_login_otps"
    __table_args__ = (UniqueConstraint("user_id", name="uq_telegram_login_otps_user_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TelegramSubscriber(Base):
    __tablename__ = "telegram_subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
