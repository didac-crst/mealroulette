from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base

if TYPE_CHECKING:
    from mealroulette.models.catalog import Ingredient
    from mealroulette.models.household import Household
    from mealroulette.models.taxonomy import FoodGroup, IngredientFamily
    from mealroulette.models.user import User


class IngredientProposalSourceType(str, enum.Enum):
    manual = "manual"
    recipe_editor = "recipe_editor"
    recipe_import = "recipe_import"
    llm_recipe_import = "llm_recipe_import"
    bulk_import = "bulk_import"
    platform_admin = "platform_admin"


class IngredientProposalResolutionStatus(str, enum.Enum):
    pending = "pending"
    needs_information = "needs_information"
    duplicate = "duplicate"
    approved = "approved"
    rejected = "rejected"
    withdrawn = "withdrawn"


class IngredientProposalResolutionType(str, enum.Enum):
    created_canonical = "created_canonical"
    mapped_existing = "mapped_existing"
    added_alias = "added_alias"
    rejected = "rejected"


TERMINAL_PROPOSAL_STATUSES = frozenset(
    {
        IngredientProposalResolutionStatus.duplicate,
        IngredientProposalResolutionStatus.approved,
        IngredientProposalResolutionStatus.rejected,
        IngredientProposalResolutionStatus.withdrawn,
    }
)


class IngredientProposal(Base):
    __tablename__ = "ingredient_proposals"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    proposed_name: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_locale: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    culinary_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_food_group_id: Mapped[str | None] = mapped_column(
        ForeignKey("food_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    suggested_family_id: Mapped[str | None] = mapped_column(
        ForeignKey("ingredient_families.id", ondelete="SET NULL"),
        nullable=True,
    )
    suggested_storage_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_product_form: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_preservation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolution_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=IngredientProposalResolutionStatus.pending.value,
        index=True,
    )
    resolution_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolved_ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    proposed_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    household_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("households.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=IngredientProposalSourceType.manual.value,
    )
    source_reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    model_reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    proposed_by: Mapped["User"] = relationship(foreign_keys=[proposed_by_user_id])
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_user_id])
    household: Mapped["Household | None"] = relationship()
    resolved_ingredient: Mapped["Ingredient | None"] = relationship()
    suggested_food_group: Mapped["FoodGroup | None"] = relationship()
    suggested_family: Mapped["IngredientFamily | None"] = relationship()
