from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mealroulette.db.base import Base


class FoodGroup(Base):
    __tablename__ = "food_groups"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    families: Mapped[list["IngredientFamily"]] = relationship(back_populates="food_group")


class IngredientFamily(Base):
    __tablename__ = "ingredient_families"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    food_group_id: Mapped[str] = mapped_column(ForeignKey("food_groups.id"), index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    food_group: Mapped[FoodGroup] = relationship(back_populates="families")
    ingredients: Mapped[list["Ingredient"]] = relationship(
        "Ingredient", back_populates="ingredient_family", foreign_keys="Ingredient.family_id"
    )
