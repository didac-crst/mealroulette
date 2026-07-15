from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID


class RecipeRating(Base):
    __tablename__ = "recipe_ratings"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "user_id",
            "dish_id",
            "recipe_id",
            name="uq_recipe_ratings_household_user_dish_recipe",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
        default=DEFAULT_HOUSEHOLD_ID,
    )
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
