from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.ingredient_proposal import IngredientProposal, IngredientProposalStatus
from mealroulette.models.user import User

class IngredientProposalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_proposal(
        self,
        *,
        household_id: UUID,
        user: User,
        proposed_name: str,
        reason: str | None,
    ) -> IngredientProposal:
        name = proposed_name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Proposed name required")
        proposal = IngredientProposal(
            id=uuid4(),
            household_id=household_id,
            proposed_by_user_id=user.id,
            proposed_name=name,
            reason=reason.strip() if reason else None,
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def list_for_household(self, household_id: UUID) -> list[IngredientProposal]:
        return list(
            self.db.scalars(
                select(IngredientProposal)
                .where(IngredientProposal.household_id == household_id)
                .order_by(IngredientProposal.created_at.desc())
            )
        )

    def list_pending(self) -> list[IngredientProposal]:
        return list(
            self.db.scalars(
                select(IngredientProposal)
                .where(IngredientProposal.status == IngredientProposalStatus.pending)
                .order_by(IngredientProposal.created_at)
            )
        )

    def review(
        self,
        proposal_id: UUID,
        *,
        reviewer: User,
        approve: bool,
        review_note: str | None = None,
    ) -> IngredientProposal:
        proposal = self.db.get(IngredientProposal, proposal_id)
        if proposal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
        if proposal.status != IngredientProposalStatus.pending:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Proposal already reviewed")
        proposal.status = IngredientProposalStatus.approved if approve else IngredientProposalStatus.rejected
        proposal.reviewed_by_user_id = reviewer.id
        proposal.reviewed_at = datetime.now(UTC)
        proposal.review_note = review_note
        self.db.commit()
        self.db.refresh(proposal)
        return proposal
