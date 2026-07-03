from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mealroulette.db.base import Base
from mealroulette.models.catalog import Ingredient, Unit
from mealroulette.models.enums import ShoppingListStatus


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_date: Mapped[date] = mapped_column(Date, index=True)
    to_date: Mapped[date] = mapped_column(Date)
    status: Mapped[ShoppingListStatus] = mapped_column(
        Enum(ShoppingListStatus, name="shopping_list_status"), default=ShoppingListStatus.active
    )
    exclude_pantry: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["ShoppingListItem"]] = relationship(
        back_populates="shopping_list",
        cascade="all, delete-orphan",
        order_by="ShoppingListItem.category, ShoppingListItem.display_name",
    )


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    shopping_list_id: Mapped[int] = mapped_column(
        ForeignKey("shopping_lists.id", ondelete="CASCADE"), index=True
    )
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    display_name: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="RESTRICT"))
    category: Mapped[str] = mapped_column(String(64))
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    approximate: Mapped[bool] = mapped_column(Boolean, default=False)
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    source_meal_plan_item_ids_json: Mapped[list] = mapped_column(JSONB)
    source_contributions_json: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    shopping_list: Mapped[ShoppingList] = relationship(back_populates="items")
    ingredient: Mapped[Ingredient] = relationship()
    unit: Mapped[Unit] = relationship()
