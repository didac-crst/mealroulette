from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base

if TYPE_CHECKING:
    from mealroulette.models.catalog import Dish, Recipe
    from mealroulette.models.household import Household
    from mealroulette.models.user import User


class PublicRecipeStatus(str, enum.Enum):
    submitted = "submitted"
    public = "public"
    rejected = "rejected"
    withdrawn = "withdrawn"
    delisted = "delisted"


class PublicRecipe(Base):
    __tablename__ = "public_recipes"
    __table_args__ = (
        UniqueConstraint("originating_recipe_id", name="uq_public_recipes_originating_recipe_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    originating_household_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    originating_dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    originating_recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_version_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            "public_recipe_versions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_public_recipes_current_version_id",
        ),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PublicRecipeStatus.submitted.value, index=True
    )
    submitted_by_user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list["PublicRecipeVersion"]] = relationship(
        back_populates="public_recipe",
        cascade="all, delete-orphan",
        foreign_keys="PublicRecipeVersion.public_recipe_id",
        order_by="PublicRecipeVersion.version_number",
    )
    originating_household: Mapped["Household"] = relationship(
        foreign_keys=[originating_household_id],
    )
    originating_dish: Mapped["Dish"] = relationship(
        foreign_keys=[originating_dish_id],
    )
    originating_recipe: Mapped["Recipe"] = relationship(
        foreign_keys=[originating_recipe_id],
    )
    submitted_by: Mapped["User"] = relationship(foreign_keys=[submitted_by_user_id])
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_user_id])


class PublicRecipeVersion(Base):
    __tablename__ = "public_recipe_versions"
    __table_args__ = (
        UniqueConstraint(
            "public_recipe_id",
            "version_number",
            name="uq_public_recipe_versions_recipe_version",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    public_recipe_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("public_recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    public_recipe: Mapped[PublicRecipe] = relationship(
        back_populates="versions",
        foreign_keys=[public_recipe_id],
    )
    created_by: Mapped["User | None"] = relationship()
