from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_admin, get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.catalog import (
    DishCreateRequest,
    DishPublic,
    DishUpdateRequest,
    IngredientAliasCreateRequest,
    IngredientAliasPublic,
    IngredientConfirmRequest,
    IngredientCreateRequest,
    IngredientDetailPublic,
    IngredientPublic,
    IngredientResolveRequest,
    IngredientResolveResponse,
    IngredientUnitConversionCreateRequest,
    IngredientUnitConversionPublic,
    IngredientUnitConversionUpdateRequest,
    IngredientUpdateRequest,
    RecipeCreateRequest,
    RecipeIngredientCreateRequest,
    RecipeIngredientPublic,
    RecipeIngredientUpdateRequest,
    RecipePublic,
    RecipeStepCreateRequest,
    RecipeStepPublic,
    RecipeStepUpdateRequest,
    RecipeUpdateRequest,
    TagCreateRequest,
    TagPublic,
    TagUpdateRequest,
    UnitPublic,
)
from mealroulette.services.catalog import CatalogService

router = APIRouter(tags=["catalog"])


@router.get("/units", response_model=list[UnitPublic])
def list_units(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UnitPublic]:
    return [UnitPublic.model_validate(unit) for unit in CatalogService(db).list_units()]


@router.get("/tags", response_model=list[TagPublic])
def list_tags(
    family: str | None = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TagPublic]:
    return [TagPublic.model_validate(tag) for tag in CatalogService(db).list_tags(family)]

@router.post("/tags", response_model=TagPublic, status_code=201)
def create_tag(
    payload: TagCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TagPublic:
    return TagPublic.model_validate(CatalogService(db).create_tag(payload))


@router.get("/tags/{tag_id}", response_model=TagPublic)
def get_tag(
    tag_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagPublic:
    return TagPublic.model_validate(CatalogService(db).get_tag(tag_id))


@router.put("/tags/{tag_id}", response_model=TagPublic)
def update_tag(
    tag_id: int,
    payload: TagUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TagPublic:
    return TagPublic.model_validate(CatalogService(db).update_tag(tag_id, payload))


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_tag(tag_id)


@router.get("/ingredients", response_model=list[IngredientPublic])
def list_ingredients(
    search: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngredientPublic]:
    service = CatalogService(db)
    return [service.to_ingredient_public(item) for item in service.list_ingredients(search)]


@router.post("/ingredients/resolve", response_model=IngredientResolveResponse)
def resolve_ingredient(
    payload: IngredientResolveRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngredientResolveResponse:
    return CatalogService(db).resolve_ingredient(payload.proposed_name)


@router.post("/ingredients/confirm", response_model=IngredientPublic, status_code=201)
def confirm_ingredient(
    payload: IngredientConfirmRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> IngredientPublic:
    service = CatalogService(db)
    ingredient = service.confirm_ingredient(
        action=payload.action,
        proposed_name=payload.proposed_name,
        ingredient_id=payload.ingredient_id,
        display_name=payload.display_name,
        category=payload.category,
        default_unit_id=payload.default_unit_id,
        language=payload.language,
    )
    return service.to_ingredient_public(ingredient)


@router.post("/ingredients", response_model=IngredientPublic, status_code=201)
def create_ingredient(
    payload: IngredientCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> IngredientPublic:
    service = CatalogService(db)
    return service.to_ingredient_public(service.create_ingredient(payload))


@router.get("/ingredients/{ingredient_id}", response_model=IngredientDetailPublic)
def get_ingredient(
    ingredient_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngredientDetailPublic:
    service = CatalogService(db)
    return service.to_ingredient_detail(service.get_ingredient(ingredient_id))


@router.put("/ingredients/{ingredient_id}", response_model=IngredientPublic)
def update_ingredient(
    ingredient_id: int,
    payload: IngredientUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> IngredientPublic:
    service = CatalogService(db)
    return service.to_ingredient_public(service.update_ingredient(ingredient_id, payload))


@router.delete("/ingredients/{ingredient_id}", status_code=204)
def delete_ingredient(
    ingredient_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_ingredient(ingredient_id)


@router.get("/ingredients/{ingredient_id}/aliases", response_model=list[IngredientAliasPublic])
def list_ingredient_aliases(
    ingredient_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngredientAliasPublic]:
    return [
        IngredientAliasPublic.model_validate(alias)
        for alias in CatalogService(db).list_aliases(ingredient_id)
    ]


@router.post("/ingredients/{ingredient_id}/aliases", response_model=IngredientAliasPublic, status_code=201)
def create_ingredient_alias(
    ingredient_id: int,
    payload: IngredientAliasCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> IngredientAliasPublic:
    return IngredientAliasPublic.model_validate(
        CatalogService(db).create_alias(ingredient_id, payload)
    )


@router.delete("/ingredient-aliases/{alias_id}", status_code=204)
def delete_ingredient_alias(
    alias_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_alias(alias_id)


@router.get(
    "/ingredients/{ingredient_id}/conversions",
    response_model=list[IngredientUnitConversionPublic],
)
def list_ingredient_conversions(
    ingredient_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngredientUnitConversionPublic]:
    service = CatalogService(db)
    return [service.to_conversion_public(conversion) for conversion in service.list_conversions(ingredient_id)]


@router.post(
    "/ingredients/{ingredient_id}/conversions",
    response_model=IngredientUnitConversionPublic,
    status_code=201,
)
def create_ingredient_conversion(
    ingredient_id: int,
    payload: IngredientUnitConversionCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> IngredientUnitConversionPublic:
    service = CatalogService(db)
    return service.to_conversion_public(service.create_conversion(ingredient_id, payload))


@router.put(
    "/ingredient-conversions/{conversion_id}",
    response_model=IngredientUnitConversionPublic,
)
def update_ingredient_conversion(
    conversion_id: int,
    payload: IngredientUnitConversionUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> IngredientUnitConversionPublic:
    service = CatalogService(db)
    return service.to_conversion_public(service.update_conversion(conversion_id, payload))


@router.delete("/ingredient-conversions/{conversion_id}", status_code=204)
def delete_ingredient_conversion(
    conversion_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_conversion(conversion_id)


@router.get("/dishes", response_model=list[DishPublic])
def list_dishes(
    active_only: bool = False,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DishPublic]:
    service = CatalogService(db)
    return [service.to_dish_public(dish) for dish in service.list_dishes(active_only)]


@router.post("/dishes", response_model=DishPublic, status_code=201)
def create_dish(
    payload: DishCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> DishPublic:
    return CatalogService(db).to_dish_public(CatalogService(db).create_dish(payload))


@router.get("/dishes/{dish_id}", response_model=DishPublic)
def get_dish(
    dish_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DishPublic:
    return CatalogService(db).to_dish_public(CatalogService(db).get_dish(dish_id))


@router.put("/dishes/{dish_id}", response_model=DishPublic)
def update_dish(
    dish_id: int,
    payload: DishUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> DishPublic:
    return CatalogService(db).to_dish_public(CatalogService(db).update_dish(dish_id, payload))


@router.delete("/dishes/{dish_id}", status_code=204)
def delete_dish(
    dish_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_dish(dish_id)


@router.get("/dishes/{dish_id}/recipes", response_model=list[RecipePublic])
def list_recipes(
    dish_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecipePublic]:
    return [RecipePublic.model_validate(recipe) for recipe in CatalogService(db).list_recipes(dish_id)]


@router.post("/dishes/{dish_id}/recipes", response_model=RecipePublic, status_code=201)
def create_recipe(
    dish_id: int,
    payload: RecipeCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RecipePublic:
    return RecipePublic.model_validate(CatalogService(db).create_recipe(dish_id, payload))


@router.get("/recipes/{recipe_id}", response_model=RecipePublic)
def get_recipe(
    recipe_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecipePublic:
    return RecipePublic.model_validate(CatalogService(db).get_recipe(recipe_id))


@router.put("/recipes/{recipe_id}", response_model=RecipePublic)
def update_recipe(
    recipe_id: int,
    payload: RecipeUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RecipePublic:
    return RecipePublic.model_validate(CatalogService(db).update_recipe(recipe_id, payload))


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(
    recipe_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_recipe(recipe_id)


@router.get("/recipes/{recipe_id}/steps", response_model=list[RecipeStepPublic])
def list_recipe_steps(
    recipe_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecipeStepPublic]:
    return [RecipeStepPublic.model_validate(step) for step in CatalogService(db).list_steps(recipe_id)]


@router.post("/recipes/{recipe_id}/steps", response_model=RecipeStepPublic, status_code=201)
def create_recipe_step(
    recipe_id: int,
    payload: RecipeStepCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RecipeStepPublic:
    return RecipeStepPublic.model_validate(CatalogService(db).create_step(recipe_id, payload))


@router.put("/recipe-steps/{step_id}", response_model=RecipeStepPublic)
def update_recipe_step(
    step_id: int,
    payload: RecipeStepUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RecipeStepPublic:
    return RecipeStepPublic.model_validate(CatalogService(db).update_step(step_id, payload))


@router.delete("/recipe-steps/{step_id}", status_code=204)
def delete_recipe_step(
    step_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_step(step_id)


@router.get("/recipes/{recipe_id}/ingredients", response_model=list[RecipeIngredientPublic])
def list_recipe_ingredients(
    recipe_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecipeIngredientPublic]:
    return [
        RecipeIngredientPublic.model_validate(item)
        for item in CatalogService(db).list_recipe_ingredients(recipe_id)
    ]


@router.post("/recipes/{recipe_id}/ingredients", response_model=RecipeIngredientPublic, status_code=201)
def add_recipe_ingredient(
    recipe_id: int,
    payload: RecipeIngredientCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RecipeIngredientPublic:
    return RecipeIngredientPublic.model_validate(
        CatalogService(db).add_recipe_ingredient(recipe_id, payload)
    )


@router.put("/recipe-ingredients/{item_id}", response_model=RecipeIngredientPublic)
def update_recipe_ingredient(
    item_id: int,
    payload: RecipeIngredientUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RecipeIngredientPublic:
    return RecipeIngredientPublic.model_validate(
        CatalogService(db).update_recipe_ingredient(item_id, payload)
    )


@router.delete("/recipe-ingredients/{item_id}", status_code=204)
def delete_recipe_ingredient(
    item_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    CatalogService(db).delete_recipe_ingredient(item_id)
