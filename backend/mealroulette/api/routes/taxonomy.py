from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.catalog import IngredientResolveRequest
from mealroulette.schemas.taxonomy import (
    ClassifyCandidateRequest,
    ClassifyCandidateResponse,
    FoodGroupPublic,
    IngredientFamilyPublic,
    IngredientResolveResponseV2,
    IngredientTaxonomyOverview,
    IngredientTaxonomySummary,
)
from mealroulette.services.ingredient_resolver import IngredientResolverService
from mealroulette.services.taxonomy_service import TaxonomyService

router = APIRouter(tags=["taxonomy"])


@router.get("/food-groups", response_model=list[FoodGroupPublic])
def list_food_groups(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FoodGroupPublic]:
    return TaxonomyService(db).list_food_groups()


@router.get("/food-groups/{food_group_id}/families", response_model=list[IngredientFamilyPublic])
def list_food_group_families(
    food_group_id: str,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngredientFamilyPublic]:
    service = TaxonomyService(db)
    families = service.list_families(food_group_id=food_group_id)
    if not families:
        valid = {group.id for group in service.list_food_groups()}
        if food_group_id.strip().lower() not in valid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food group not found")
    return families


@router.get("/ingredient-families/{family_id}/ingredients", response_model=list[IngredientTaxonomySummary])
def list_family_ingredients(
    family_id: str,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngredientTaxonomySummary]:
    service = TaxonomyService(db)
    valid_families = {family.id for family in service.list_families()}
    if family_id.strip().lower() not in valid_families:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient family not found")
    return service.list_ingredients_for_family(family_id)


@router.get("/ingredient-taxonomy/overview", response_model=IngredientTaxonomyOverview)
def ingredient_taxonomy_overview(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngredientTaxonomyOverview:
    return TaxonomyService(db).overview()


@router.post("/ingredients/resolve-v2", response_model=IngredientResolveResponseV2)
def resolve_ingredient_v2(
    payload: IngredientResolveRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngredientResolveResponseV2:
    return IngredientResolveResponseV2.model_validate(
        IngredientResolverService(db).resolve(payload.proposed_name)
    )


@router.post("/ingredients/classify-candidate", response_model=ClassifyCandidateResponse)
def classify_ingredient_candidate(
    payload: ClassifyCandidateRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClassifyCandidateResponse:
    return ClassifyCandidateResponse.model_validate(
        IngredientResolverService(db).classify_candidate(
            name=payload.name,
            context=payload.context,
            language=payload.language,
        )
    )
