from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from mealroulette.models.catalog import Ingredient, IngredientAlias
from mealroulette.models.ingredient_proposals import (
    TERMINAL_PROPOSAL_STATUSES,
    IngredientProposal,
    IngredientProposalResolutionStatus,
    IngredientProposalResolutionType,
    IngredientProposalSourceType,
)
from mealroulette.models.taxonomy import FoodGroup, IngredientFamily
from mealroulette.models.user import User
from mealroulette.schemas.catalog import IngredientAliasCreateRequest, IngredientCreateRequest
from mealroulette.schemas.ingredient_proposals import (
    IngredientProposalAddAliasRequest,
    IngredientProposalApproveNewRequest,
    IngredientProposalCreateRequest,
    IngredientProposalCreateResponse,
    IngredientProposalMapExistingRequest,
    IngredientProposalMarkDuplicateRequest,
    IngredientProposalMatchKind,
    IngredientProposalMatchPublic,
    IngredientProposalProvideInformationRequest,
    IngredientProposalPublic,
    IngredientProposalReviewNoteRequest,
)
from mealroulette.services.catalog import CatalogService
from mealroulette.services.names import normalize_alias, normalize_name, to_canonical_slug


class IngredientProposalService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def to_public(proposal: IngredientProposal) -> IngredientProposalPublic:
        public = IngredientProposalPublic.model_validate(proposal)
        return public.model_copy(
            update={"suggested_canonical_name": to_canonical_slug(proposal.proposed_name)}
        )

    def find_matches(
        self,
        *,
        proposed_name: str,
        source_locale: str,
        exclude_proposal_id: UUID | None = None,
        include_terminal_proposals: bool = False,
        viewer_user_id: UUID | None = None,
        expose_foreign_proposal_ids: bool = False,
    ) -> list[IngredientProposalMatchPublic]:
        """Return possible catalog/proposal matches. Never blocks creation.

        Rejected/withdrawn proposals are not blockers. They are only included when
        ``include_terminal_proposals`` is true (platform review context).

        When ``expose_foreign_proposal_ids`` is false (member create), other users'
        pending proposals are summarized without UUIDs.
        """
        matches: list[IngredientProposalMatchPublic] = []
        seen_ingredient_ids: set[int] = set()
        normalized = normalize_name(proposed_name)
        slug = to_canonical_slug(proposed_name)
        alias_normalized = normalize_alias(proposed_name)

        ingredient_filters = [
            func.lower(Ingredient.canonical_name) == slug,
            func.lower(Ingredient.canonical_name) == normalized,
            func.replace(func.lower(Ingredient.canonical_name), "_", " ") == normalized,
        ]
        if alias_normalized and alias_normalized != normalized:
            ingredient_filters.append(
                func.replace(func.lower(Ingredient.canonical_name), "_", " ") == alias_normalized
            )
        ingredients = list(self.db.scalars(select(Ingredient).where(or_(*ingredient_filters)).limit(10)))
        for ingredient in ingredients:
            if ingredient.id in seen_ingredient_ids:
                continue
            seen_ingredient_ids.add(ingredient.id)
            matches.append(
                IngredientProposalMatchPublic(
                    kind=IngredientProposalMatchKind.ingredient,
                    label=ingredient.display_name,
                    ingredient_id=ingredient.id,
                )
            )

        alias_filters = [
            func.lower(IngredientAlias.alias) == normalized,
            func.lower(IngredientAlias.alias) == alias_normalized,
            func.lower(IngredientAlias.alias) == slug,
        ]
        aliases = list(self.db.scalars(select(IngredientAlias).where(or_(*alias_filters)).limit(10)))
        for alias in aliases:
            if alias.ingredient_id in seen_ingredient_ids:
                continue
            seen_ingredient_ids.add(alias.ingredient_id)
            matches.append(
                IngredientProposalMatchPublic(
                    kind=IngredientProposalMatchKind.alias,
                    label=alias.alias,
                    ingredient_id=alias.ingredient_id,
                    alias=alias.alias,
                )
            )

        statuses = [
            IngredientProposalResolutionStatus.pending.value,
            IngredientProposalResolutionStatus.needs_information.value,
        ]
        if include_terminal_proposals:
            statuses.extend(
                [
                    IngredientProposalResolutionStatus.rejected.value,
                    IngredientProposalResolutionStatus.withdrawn.value,
                    IngredientProposalResolutionStatus.duplicate.value,
                    IngredientProposalResolutionStatus.approved.value,
                ]
            )
        pending_query = select(IngredientProposal).where(
            IngredientProposal.normalized_name == normalized,
            IngredientProposal.source_locale == source_locale,
            IngredientProposal.resolution_status.in_(statuses),
        )
        if exclude_proposal_id is not None:
            pending_query = pending_query.where(IngredientProposal.id != exclude_proposal_id)
        related = list(self.db.scalars(pending_query.limit(10)))
        foreign_pending = 0
        for proposal in related:
            is_own = viewer_user_id is None or proposal.proposed_by_user_id == viewer_user_id
            if is_own or expose_foreign_proposal_ids:
                matches.append(
                    IngredientProposalMatchPublic(
                        kind=IngredientProposalMatchKind.pending_proposal,
                        label=proposal.proposed_name,
                        proposal_id=proposal.id,
                    )
                )
            else:
                foreign_pending += 1
        if foreign_pending:
            matches.append(
                IngredientProposalMatchPublic(
                    kind=IngredientProposalMatchKind.pending_proposal,
                    label="Similar pending proposal exists",
                    proposal_id=None,
                )
            )
        return matches

    def create_proposal(
        self,
        *,
        user: User,
        household_id: UUID,
        payload: IngredientProposalCreateRequest,
    ) -> IngredientProposalCreateResponse:
        proposed_name = payload.proposed_name.strip()
        if not proposed_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="proposed_name is required")
        normalized = normalize_name(proposed_name)
        if not normalized:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="proposed_name is invalid")

        self._validate_suggestions(
            food_group_id=payload.suggested_food_group_id,
            family_id=payload.suggested_family_id,
        )

        matches = self.find_matches(
            proposed_name=proposed_name,
            source_locale=payload.source_locale.strip().lower(),
            viewer_user_id=user.id,
            expose_foreign_proposal_ids=False,
        )

        proposal = IngredientProposal(
            proposed_name=proposed_name,
            normalized_name=normalized,
            source_locale=payload.source_locale.strip().lower(),
            description=payload.description,
            culinary_context=payload.culinary_context,
            suggested_food_group_id=payload.suggested_food_group_id,
            suggested_family_id=payload.suggested_family_id,
            suggested_storage_class=payload.suggested_storage_class,
            suggested_product_form=payload.suggested_product_form,
            suggested_preservation=payload.suggested_preservation,
            resolution_status=IngredientProposalResolutionStatus.pending.value,
            proposed_by_user_id=user.id,
            household_id=household_id,
            # Member endpoint provenance is always server-derived.
            source_type=IngredientProposalSourceType.manual.value,
            source_reference_type=None,
            source_reference_id=None,
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return IngredientProposalCreateResponse(
            proposal=self.to_public(proposal),
            matches=matches,
        )

    def list_mine(self, *, user_id: UUID) -> list[IngredientProposal]:
        return list(
            self.db.scalars(
                select(IngredientProposal)
                .where(IngredientProposal.proposed_by_user_id == user_id)
                .order_by(IngredientProposal.created_at.desc())
            )
        )

    def list_for_platform(
        self,
        *,
        resolution_status: str | None = None,
    ) -> list[IngredientProposal]:
        query = select(IngredientProposal).order_by(IngredientProposal.created_at.desc())
        if resolution_status is not None:
            query = query.where(IngredientProposal.resolution_status == resolution_status)
        return list(self.db.scalars(query))

    def get_proposal(self, proposal_id: UUID, *, for_update: bool = False) -> IngredientProposal:
        query = select(IngredientProposal).where(IngredientProposal.id == proposal_id)
        if for_update:
            query = query.with_for_update()
        proposal = self.db.scalar(query)
        if proposal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
        return proposal

    def get_own_proposal(self, *, proposal_id: UUID, user_id: UUID) -> IngredientProposal:
        proposal = self.get_proposal(proposal_id)
        if proposal.proposed_by_user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
        return proposal

    def withdraw(self, *, proposal_id: UUID, user_id: UUID) -> IngredientProposal:
        proposal = self.get_own_proposal(proposal_id=proposal_id, user_id=user_id)
        current = IngredientProposalResolutionStatus(proposal.resolution_status)
        if current in TERMINAL_PROPOSAL_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only non-terminal proposals can be withdrawn",
            )
        if current not in {
            IngredientProposalResolutionStatus.pending,
            IngredientProposalResolutionStatus.needs_information,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot withdraw proposal in status {proposal.resolution_status}",
            )
        proposal.resolution_status = IngredientProposalResolutionStatus.withdrawn.value
        proposal.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def provide_information(
        self,
        *,
        proposal_id: UUID,
        user_id: UUID,
        payload: IngredientProposalProvideInformationRequest,
    ) -> IngredientProposal:
        proposal = self.get_own_proposal(proposal_id=proposal_id, user_id=user_id)
        if proposal.resolution_status != IngredientProposalResolutionStatus.needs_information.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only proposals needing information can be updated this way",
            )
        if payload.description is not None:
            proposal.description = payload.description
        if payload.culinary_context is not None:
            proposal.culinary_context = payload.culinary_context
        if payload.review_response:
            note = proposal.review_note or ""
            suffix = f"\nSubmitter response: {payload.review_response.strip()}"
            proposal.review_note = (note + suffix).strip() or None
        proposal.resolution_status = IngredientProposalResolutionStatus.pending.value
        proposal.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def map_existing(
        self,
        *,
        proposal_id: UUID,
        reviewer: User,
        payload: IngredientProposalMapExistingRequest,
    ) -> IngredientProposal:
        proposal = self._require_reviewable(proposal_id)
        ingredient = self._require_ingredient(payload.ingredient_id)
        self._apply_review(
            proposal,
            reviewer=reviewer,
            status=IngredientProposalResolutionStatus.approved,
            resolution_type=IngredientProposalResolutionType.mapped_existing,
            resolved_ingredient_id=ingredient.id,
            review_note=payload.review_note,
        )
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def add_alias(
        self,
        *,
        proposal_id: UUID,
        reviewer: User,
        payload: IngredientProposalAddAliasRequest,
    ) -> IngredientProposal:
        proposal = self._require_reviewable(proposal_id)
        alias_text = (payload.alias or proposal.proposed_name).strip()
        catalog = CatalogService(self.db)
        # Flush only — commit with the proposal review row in one transaction.
        catalog.create_alias(
            payload.ingredient_id,
            IngredientAliasCreateRequest(alias=alias_text, language=payload.language),
            commit=False,
        )
        self._apply_review(
            proposal,
            reviewer=reviewer,
            status=IngredientProposalResolutionStatus.approved,
            resolution_type=IngredientProposalResolutionType.added_alias,
            resolved_ingredient_id=payload.ingredient_id,
            review_note=payload.review_note,
        )
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def approve_new(
        self,
        *,
        proposal_id: UUID,
        reviewer: User,
        payload: IngredientProposalApproveNewRequest,
    ) -> IngredientProposal:
        proposal = self._require_reviewable(proposal_id)
        display_name = (payload.display_name or proposal.proposed_name).strip()
        canonical_source = (payload.canonical_name or proposal.proposed_name).strip()
        canonical_name = to_canonical_slug(canonical_source)
        if not canonical_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="canonical_name is invalid",
            )

        existing = self.db.scalar(
            select(Ingredient).where(func.lower(Ingredient.canonical_name) == canonical_name)
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Canonical name '{canonical_name}' already exists "
                    f"(ingredient id {existing.id}). Use map-existing or add-alias instead of approve-new."
                ),
            )

        food_group = payload.food_group or proposal.suggested_food_group_id
        family = payload.family or proposal.suggested_family_id
        if not food_group or not family:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Approve-new requires an existing food_group and family. "
                    "If no suitable family exists, request information, reject, or leave pending "
                    "until taxonomy is extended."
                ),
            )
        self._validate_suggestions(food_group_id=food_group, family_id=family)

        note_parts = [
            part.strip()
            for part in (
                payload.notes,
                proposal.description,
                f"Conversion hints: {payload.conversion_notes}" if payload.conversion_notes else None,
            )
            if part and part.strip()
        ]
        create_payload = IngredientCreateRequest(
            canonical_name=canonical_name,
            display_name=display_name,
            category=payload.category,
            food_group=food_group,
            family=family,
            storage_class=payload.storage_class or proposal.suggested_storage_class,
            culinary_category=payload.culinary_category,
            product_form=payload.product_form or proposal.suggested_product_form,
            preservation=payload.preservation or proposal.suggested_preservation,
            default_unit_id=payload.default_unit_id,
            preferred_shopping_unit_id=payload.preferred_shopping_unit_id,
            notes="\n\n".join(note_parts) or None,
            aliases=[alias.strip() for alias in payload.aliases if alias.strip()],
        )
        catalog = CatalogService(self.db)
        # Flush only — commit with the proposal review row in one transaction.
        ingredient = catalog.create_ingredient(create_payload, commit=False)
        self._apply_review(
            proposal,
            reviewer=reviewer,
            status=IngredientProposalResolutionStatus.approved,
            resolution_type=IngredientProposalResolutionType.created_canonical,
            resolved_ingredient_id=ingredient.id,
            review_note=payload.review_note,
        )
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def reject(
        self,
        *,
        proposal_id: UUID,
        reviewer: User,
        payload: IngredientProposalReviewNoteRequest,
    ) -> IngredientProposal:
        proposal = self._require_reviewable(proposal_id)
        self._apply_review(
            proposal,
            reviewer=reviewer,
            status=IngredientProposalResolutionStatus.rejected,
            resolution_type=IngredientProposalResolutionType.rejected,
            resolved_ingredient_id=None,
            review_note=payload.review_note,
        )
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def request_information(
        self,
        *,
        proposal_id: UUID,
        reviewer: User,
        payload: IngredientProposalReviewNoteRequest,
    ) -> IngredientProposal:
        proposal = self._require_reviewable(proposal_id, allow_needs_information=False)
        if proposal.resolution_status != IngredientProposalResolutionStatus.pending.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending proposals can request information",
            )
        self._apply_review(
            proposal,
            reviewer=reviewer,
            status=IngredientProposalResolutionStatus.needs_information,
            resolution_type=None,
            resolved_ingredient_id=None,
            review_note=payload.review_note,
        )
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def mark_duplicate(
        self,
        *,
        proposal_id: UUID,
        reviewer: User,
        payload: IngredientProposalMarkDuplicateRequest,
    ) -> IngredientProposal:
        proposal = self._require_reviewable(proposal_id)
        ingredient_id = None
        if payload.ingredient_id is not None:
            ingredient_id = self._require_ingredient(payload.ingredient_id).id
        self._apply_review(
            proposal,
            reviewer=reviewer,
            status=IngredientProposalResolutionStatus.duplicate,
            resolution_type=None,
            resolved_ingredient_id=ingredient_id,
            review_note=payload.review_note,
        )
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def _require_ingredient(self, ingredient_id: int) -> Ingredient:
        ingredient = self.db.get(Ingredient, ingredient_id)
        if ingredient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
        return ingredient

    def _require_reviewable(
        self,
        proposal_id: UUID,
        *,
        allow_needs_information: bool = True,
    ) -> IngredientProposal:
        proposal = self.get_proposal(proposal_id, for_update=True)
        current = IngredientProposalResolutionStatus(proposal.resolution_status)
        if current in TERMINAL_PROPOSAL_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot review proposal in terminal status {proposal.resolution_status}",
            )
        allowed = {IngredientProposalResolutionStatus.pending}
        if allow_needs_information:
            allowed.add(IngredientProposalResolutionStatus.needs_information)
        if current not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot review proposal in status {proposal.resolution_status}",
            )
        return proposal

    def _apply_review(
        self,
        proposal: IngredientProposal,
        *,
        reviewer: User,
        status: IngredientProposalResolutionStatus,
        resolution_type: IngredientProposalResolutionType | None,
        resolved_ingredient_id: int | None,
        review_note: str | None,
    ) -> None:
        proposal.resolution_status = status.value
        proposal.resolution_type = resolution_type.value if resolution_type else None
        proposal.resolved_ingredient_id = resolved_ingredient_id
        proposal.reviewed_by_user_id = reviewer.id
        proposal.reviewed_at = datetime.now(UTC)
        proposal.review_note = review_note
        proposal.updated_at = datetime.now(UTC)

    def _validate_suggestions(self, *, food_group_id: str | None, family_id: str | None) -> None:
        if food_group_id is not None and self.db.get(FoodGroup, food_group_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown food group")
        if family_id is not None:
            family = self.db.get(IngredientFamily, family_id)
            if family is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown family")
            if food_group_id is not None and family.food_group_id != food_group_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Family does not belong to suggested food group",
                )
