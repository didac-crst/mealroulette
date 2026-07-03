from datetime import datetime, time

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from mealroulette.db.base import Base

TELEGRAM_SETTINGS_ID = 1


class TelegramSettings(Base):
    __tablename__ = "telegram_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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


class TelegramSubscriber(Base):
    __tablename__ = "telegram_subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
