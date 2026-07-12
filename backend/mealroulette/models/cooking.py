import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mealroulette.db.base import Base


class CookingTimerAlertStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    cancelled = "cancelled"
    failed = "failed"


class CookingTimerAlert(Base):
    __tablename__ = "cooking_timer_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    recipe_step_id: Mapped[int] = mapped_column(ForeignKey("recipe_steps.id", ondelete="CASCADE"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    dish_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipe_name: Mapped[str] = mapped_column(String(255), nullable=False)
    fire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=CookingTimerAlertStatus.pending.value)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
