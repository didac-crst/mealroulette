from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mealroulette.db.base import Base
from mealroulette.models.catalog import Dish, Recipe
from mealroulette.models.enums import MealPlanItemStatus, MealPlanStatus, MealSlot


class MealPlan(Base):
    __tablename__ = "meal_plans"
    __table_args__ = (UniqueConstraint("week_start_date", name="uq_meal_plans_week_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[MealPlanStatus] = mapped_column(
        Enum(MealPlanStatus, name="meal_plan_status"), default=MealPlanStatus.active
    )
    last_roulette_undo_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["MealPlanItem"]] = relationship(
        back_populates="meal_plan", cascade="all, delete-orphan", order_by="MealPlanItem.date, MealPlanItem.meal_slot"
    )


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"
    __table_args__ = (
        UniqueConstraint("meal_plan_id", "date", "meal_slot", name="uq_meal_plan_items_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(ForeignKey("meal_plans.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    meal_slot: Mapped[MealSlot] = mapped_column(Enum(MealSlot, name="meal_slot"))
    dish_id: Mapped[int | None] = mapped_column(ForeignKey("dishes.id", ondelete="SET NULL"), nullable=True)
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[MealPlanItemStatus] = mapped_column(
        Enum(MealPlanItemStatus, name="meal_plan_item_status"), default=MealPlanItemStatus.planned
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    manually_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    skip_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    skip_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    leftover_source_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("meal_plan_items.id", ondelete="SET NULL"), nullable=True
    )
    selection_reasons_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    review_saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    meal_plan: Mapped[MealPlan] = relationship(back_populates="items")
    dish: Mapped[Dish | None] = relationship(foreign_keys=[dish_id])
    recipe: Mapped[Recipe | None] = relationship()
    meal_rating: Mapped["MealRating | None"] = relationship(back_populates="meal_plan_item", uselist=False)


class MealRating(Base):
    __tablename__ = "meal_ratings"
    __table_args__ = (UniqueConstraint("meal_plan_item_id", name="uq_meal_ratings_meal_plan_item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_plan_item_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plan_items.id", ondelete="CASCADE"), index=True
    )
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    meal_plan_item: Mapped[MealPlanItem] = relationship(back_populates="meal_rating")
    dish: Mapped[Dish] = relationship()
    recipe: Mapped[Recipe | None] = relationship()
