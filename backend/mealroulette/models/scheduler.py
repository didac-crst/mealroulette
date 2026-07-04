from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Time, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mealroulette.db.base import Base

SCHEDULER_SETTINGS_ID = 1
DEFAULT_PLANNING_RULE_ID = 1


class PlanningRule(Base):
    __tablename__ = "planning_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rules_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SchedulerSettings(Base):
    __tablename__ = "scheduler_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    run_weekday: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    run_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(18, 0))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Paris")
    target_week_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notify_telegram: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_planning_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    last_roulette_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
