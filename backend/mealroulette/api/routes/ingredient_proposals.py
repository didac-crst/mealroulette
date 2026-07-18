from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import (
    HouseholdScope,
    get_current_household_scope,
    get_current_platform_admin,
    get_current_user,
)
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.ingredient_proposals import (
    IngredientProposalAddAliasRequest,
    IngredientProposalApproveNewRequest,
    IngredientProposalCreateRequest,
    IngredientProposalCreateResponse,
    IngredientProposalMapExistingRequest,
    IngredientProposalMarkDuplicateRequest,
    IngredientProposalProvideInformationRequest,
    IngredientProposalPublic,
    IngredientProposalReviewNoteRequest,
)
from mealroulette.services.ingredient_proposals import IngredientProposalService

router = APIRouter(tags=["ingredient-proposals"])


@router.post("/ingredient-proposals", response_model=IngredientProposalCreateResponse, status_code=201)
def create_ingredient_proposal(
    payload: IngredientProposalCreateRequest,
    current_user: User = Depends(get_current_user),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> IngredientProposalCreateResponse:
    return IngredientProposalService(db).create_proposal(
        user=current_user,
        household_id=scope.household_id,
        payload=payload,
    )


@router.get("/ingredient-proposals/mine", response_model=list[IngredientProposalPublic])
def list_my_ingredient_proposals(
    current_user: User = Depends(get_current_user),
    _scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> list[IngredientProposalPublic]:
    service = IngredientProposalService(db)
    return [service.to_public(item) for item in service.list_mine(user_id=current_user.id)]


@router.post("/ingredient-proposals/{proposal_id}/withdraw", response_model=IngredientProposalPublic)
def withdraw_ingredient_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    _scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(service.withdraw(proposal_id=proposal_id, user_id=current_user.id))


@router.post(
    "/ingredient-proposals/{proposal_id}/provide-information",
    response_model=IngredientProposalPublic,
)
def provide_ingredient_proposal_information(
    proposal_id: UUID,
    payload: IngredientProposalProvideInformationRequest,
    current_user: User = Depends(get_current_user),
    _scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.provide_information(
            proposal_id=proposal_id,
            user_id=current_user.id,
            payload=payload,
        )
    )


@router.get("/platform/ingredient-proposals", response_model=list[IngredientProposalPublic])
def list_platform_ingredient_proposals(
    resolution_status: str | None = Query(default=None),
    _admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> list[IngredientProposalPublic]:
    service = IngredientProposalService(db)
    return [
        service.to_public(item)
        for item in service.list_for_platform(resolution_status=resolution_status)
    ]


@router.get(
    "/platform/ingredient-proposals/{proposal_id}",
    response_model=IngredientProposalPublic,
)
def get_platform_ingredient_proposal(
    proposal_id: UUID,
    _admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(service.get_proposal(proposal_id))


@router.post(
    "/platform/ingredient-proposals/{proposal_id}/map-existing",
    response_model=IngredientProposalPublic,
)
def map_existing_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalMapExistingRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.map_existing(proposal_id=proposal_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/ingredient-proposals/{proposal_id}/add-alias",
    response_model=IngredientProposalPublic,
)
def add_alias_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalAddAliasRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.add_alias(proposal_id=proposal_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/ingredient-proposals/{proposal_id}/approve-new",
    response_model=IngredientProposalPublic,
)
def approve_new_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalApproveNewRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.approve_new(proposal_id=proposal_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/ingredient-proposals/{proposal_id}/reject",
    response_model=IngredientProposalPublic,
)
def reject_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalReviewNoteRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.reject(proposal_id=proposal_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/ingredient-proposals/{proposal_id}/request-information",
    response_model=IngredientProposalPublic,
)
def request_information_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalReviewNoteRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.request_information(proposal_id=proposal_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/ingredient-proposals/{proposal_id}/mark-duplicate",
    response_model=IngredientProposalPublic,
)
def mark_duplicate_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalMarkDuplicateRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    service = IngredientProposalService(db)
    return service.to_public(
        service.mark_duplicate(proposal_id=proposal_id, reviewer=admin, payload=payload)
    )
