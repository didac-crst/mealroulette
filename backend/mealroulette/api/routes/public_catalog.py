from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import (
    HouseholdScope,
    get_current_household_admin,
    get_current_household_scope,
    get_current_platform_admin,
)
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.public_catalog import (
    PublicRecipeAdoptResponse,
    PublicRecipeApproveRequest,
    PublicRecipeHouseholdPublic,
    PublicRecipeMemberPublic,
    PublicRecipePlatformPublic,
    PublicRecipeReviewNoteRequest,
)
from mealroulette.services.public_catalog import PublicCatalogService

router = APIRouter(tags=["public-catalog"])


@router.get("/public-recipes", response_model=list[PublicRecipeMemberPublic])
def list_public_recipes(
    _scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> list[PublicRecipeMemberPublic]:
    service = PublicCatalogService(db)
    return [service.to_member_public(item) for item in service.list_public()]


@router.get("/public-recipes/{public_recipe_id}", response_model=PublicRecipeMemberPublic)
def get_public_recipe(
    public_recipe_id: UUID,
    _scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> PublicRecipeMemberPublic:
    service = PublicCatalogService(db)
    return service.to_member_public(service.get_public_for_members(public_recipe_id))


@router.post(
    "/public-recipes/{public_recipe_id}/adopt",
    response_model=PublicRecipeAdoptResponse,
    status_code=201,
)
def adopt_public_recipe(
    public_recipe_id: UUID,
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> PublicRecipeAdoptResponse:
    return PublicCatalogService(db).adopt(
        public_recipe_id=public_recipe_id,
        household_id=scope.household_id,
    )


@router.post(
    "/recipes/{recipe_id}/publish-request",
    response_model=PublicRecipeHouseholdPublic,
    status_code=201,
)
def submit_publish_request(
    recipe_id: int,
    current_user: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> PublicRecipeHouseholdPublic:
    service = PublicCatalogService(db)
    public_recipe = service.submit_publish_request(
        user=current_user,
        household_id=scope.household_id,
        recipe_id=recipe_id,
    )
    return service.to_household_public(public_recipe)


@router.get("/household/publication-requests", response_model=list[PublicRecipeHouseholdPublic])
def list_household_publication_requests(
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> list[PublicRecipeHouseholdPublic]:
    service = PublicCatalogService(db)
    return [
        service.to_household_public(item)
        for item in service.list_household_requests(household_id=scope.household_id)
    ]


@router.post(
    "/household/publication-requests/{public_recipe_id}/withdraw",
    response_model=PublicRecipeHouseholdPublic,
)
def withdraw_publication_request(
    public_recipe_id: UUID,
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> PublicRecipeHouseholdPublic:
    service = PublicCatalogService(db)
    return service.to_household_public(
        service.withdraw(public_recipe_id=public_recipe_id, household_id=scope.household_id)
    )


@router.get("/platform/public-recipes", response_model=list[PublicRecipePlatformPublic])
def list_platform_public_recipes(
    status_filter: str | None = Query(default=None, alias="status"),
    _admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> list[PublicRecipePlatformPublic]:
    service = PublicCatalogService(db)
    return [
        service.to_platform_public(item)
        for item in service.list_for_platform(status_filter=status_filter)
    ]


@router.get("/platform/public-recipes/{public_recipe_id}", response_model=PublicRecipePlatformPublic)
def get_platform_public_recipe(
    public_recipe_id: UUID,
    _admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> PublicRecipePlatformPublic:
    service = PublicCatalogService(db)
    return service.to_platform_public(service.get_public_recipe(public_recipe_id))


@router.post(
    "/platform/public-recipes/{public_recipe_id}/approve",
    response_model=PublicRecipePlatformPublic,
)
def approve_public_recipe(
    public_recipe_id: UUID,
    payload: PublicRecipeApproveRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> PublicRecipePlatformPublic:
    service = PublicCatalogService(db)
    return service.to_platform_public(
        service.approve(public_recipe_id=public_recipe_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/public-recipes/{public_recipe_id}/reject",
    response_model=PublicRecipePlatformPublic,
)
def reject_public_recipe(
    public_recipe_id: UUID,
    payload: PublicRecipeReviewNoteRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> PublicRecipePlatformPublic:
    service = PublicCatalogService(db)
    return service.to_platform_public(
        service.reject(public_recipe_id=public_recipe_id, reviewer=admin, payload=payload)
    )


@router.post(
    "/platform/public-recipes/{public_recipe_id}/delist",
    response_model=PublicRecipePlatformPublic,
)
def delist_public_recipe(
    public_recipe_id: UUID,
    payload: PublicRecipeReviewNoteRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> PublicRecipePlatformPublic:
    service = PublicCatalogService(db)
    return service.to_platform_public(
        service.delist(public_recipe_id=public_recipe_id, reviewer=admin, payload=payload)
    )
