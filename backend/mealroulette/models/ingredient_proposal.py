from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base


class IngredientProposalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class IngredientProposal(Base):
    __tablename__ = "ingredient_proposals"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
    )
    proposed_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    proposed_name: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IngredientProposalStatus] = mapped_column(
        Enum(IngredientProposalStatus, name="ingredient_proposal_status"),
        default=IngredientProposalStatus.pending,
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
