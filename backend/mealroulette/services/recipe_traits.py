from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Ingredient, Recipe, RecipeIngredient
from mealroulette.services.food_groups import (
    CARB_FOOD_GROUP,
    NON_VEGAN_FOOD_GROUPS,
    PROTEIN_FOOD_GROUPS,
    food_group_for_ingredient,
)
from mealroulette.services.scheduler.family_vector import (
    build_family_vector_for_recipe,
    family_key_for_ingredient,
    ingredient_line_to_reference_grams,
    vector_line_from_recipe_ingredient,
)
from mealroulette.services.quantities import UnitInfo

CARB_HEAVY_THRESHOLD_PCT = 33.0

RECIPE_TRAIT_INGREDIENT_LOAD = (
    selectinload(Recipe.ingredients)
    .selectinload(RecipeIngredient.ingredient)
    .selectinload(Ingredient.unit_conversions),
    selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
)


def _normalize_weights(totals: dict[str, Decimal]) -> dict[str, float]:
    total = sum(totals.values(), start=Decimal("0"))
    if total <= 0:
        return {}
    return {key: float((amount / total) * Decimal("100")) for key, amount in totals.items()}


def build_recipe_traits(
    recipe: Recipe,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    vector_min_grams: int = 5,
    default_grams_per_count: int = 100,
) -> dict:
    family_vector_result = build_family_vector_for_recipe(
        recipe,
        gram_unit=gram_unit,
        ml_unit=ml_unit,
        vector_min_grams=vector_min_grams,
        default_grams_per_count=default_grams_per_count,
    )

    food_group_grams: dict[str, Decimal] = {}
    family_grams_by_food_group: dict[str, dict[str, Decimal]] = {}
    contains_meat = False
    has_non_vegan = False

    for recipe_ingredient in recipe.ingredients:
        line = vector_line_from_recipe_ingredient(recipe_ingredient)
        ingredient = recipe_ingredient.ingredient
        if line is None or ingredient is None:
            continue

        group = food_group_for_ingredient(
            food_group=ingredient.food_group,
            category=ingredient.category,
            family=ingredient.family,
        )

        if group == "meat":
            contains_meat = True
        if group in NON_VEGAN_FOOD_GROUPS:
            has_non_vegan = True

        try:
            grams, _ = ingredient_line_to_reference_grams(
                line.quantity,
                line.unit,
                gram_unit=gram_unit,
                ml_unit=ml_unit,
                conversions=list(line.conversions),
                default_grams_per_count=default_grams_per_count,
            )
        except ValueError:
            continue

        min_grams = Decimal(vector_min_grams)
        if grams < min_grams:
            continue

        food_group_grams[group] = food_group_grams.get(group, Decimal("0")) + grams

        family_key = family_key_for_ingredient(
            family=ingredient.family,
            category=ingredient.category,
            canonical_name=ingredient.canonical_name,
        )
        if family_key is None:
            continue

        group_families = family_grams_by_food_group.setdefault(group, {})
        group_families[family_key] = group_families.get(family_key, Decimal("0")) + grams

    food_group_weights = _normalize_weights(food_group_grams)
    carb_pct = food_group_weights.get(CARB_FOOD_GROUP, 0.0)

    dominant_carb = _dominant_family(family_grams_by_food_group.get(CARB_FOOD_GROUP, {}))
    dominant_protein = _dominant_family(
        {
            family: grams
            for group, families in family_grams_by_food_group.items()
            if group in PROTEIN_FOOD_GROUPS
            for family, grams in families.items()
        }
    )

    return {
        "family_vector": family_vector_result.weights,
        "food_group_weights": food_group_weights,
        "contains_food_groups": sorted(food_group_weights.keys()),
        "contains_meat": contains_meat,
        "vegan": not has_non_vegan,
        "carb_heavy": carb_pct >= CARB_HEAVY_THRESHOLD_PCT,
        "dominant_carb": dominant_carb,
        "dominant_protein": dominant_protein,
    }


def _dominant_family(family_grams: dict[str, Decimal]) -> str | None:
    if not family_grams:
        return None
    return max(family_grams.items(), key=lambda item: item[1])[0]


def _recipe_has_trait_inputs(recipe: Recipe) -> bool:
    if not recipe.ingredients:
        return False
    return all(line.ingredient is not None and line.unit is not None for line in recipe.ingredients)


def compute_recipe_traits_now(
    db: Session,
    recipe: Recipe,
    *,
    gram_unit: UnitInfo | None = None,
    ml_unit: UnitInfo | None = None,
) -> dict:
    if gram_unit is None or ml_unit is None:
        from mealroulette.services.scheduler.catalog import load_reference_units

        loaded_gram, loaded_ml = load_reference_units(db)
        gram_unit = gram_unit or loaded_gram
        ml_unit = ml_unit or loaded_ml
    loaded = recipe if _recipe_has_trait_inputs(recipe) else load_recipe_for_traits(db, recipe.id) or recipe
    return build_recipe_traits(loaded, gram_unit=gram_unit, ml_unit=ml_unit)


def load_recipe_for_traits(db: Session, recipe_id: int) -> Recipe | None:
    return db.scalar(
        select(Recipe)
        .options(*RECIPE_TRAIT_INGREDIENT_LOAD)
        .where(Recipe.id == recipe_id)
    )


def refresh_recipe_traits(
    db: Session,
    recipe: Recipe,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
) -> dict:
    loaded = load_recipe_for_traits(db, recipe.id) or recipe
    traits = build_recipe_traits(loaded, gram_unit=gram_unit, ml_unit=ml_unit)
    loaded.computed_traits_json = traits
    return traits


def refresh_recipes_for_ingredient(
    db: Session,
    ingredient_id: int,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
) -> None:
    recipe_ids = db.scalars(
        select(RecipeIngredient.recipe_id)
        .where(RecipeIngredient.ingredient_id == ingredient_id)
        .distinct()
    ).all()
    for recipe_id in recipe_ids:
        recipe = load_recipe_for_traits(db, recipe_id)
        if recipe is not None:
            refresh_recipe_traits(db, recipe, gram_unit=gram_unit, ml_unit=ml_unit)


def effective_traits_for_meal_plan_item(
    *,
    db: Session,
    recipe: Recipe | None,
    dish_recipes: list[Recipe] | None,
    gram_unit: UnitInfo | None = None,
    ml_unit: UnitInfo | None = None,
) -> dict | None:
    target = recipe
    if target is None and dish_recipes:
        main = next((item for item in dish_recipes if item.is_main), None)
        if main is None and dish_recipes:
            main = min(dish_recipes, key=lambda item: item.id)
        target = main
    if target is None:
        return None
    return compute_recipe_traits_now(db, target, gram_unit=gram_unit, ml_unit=ml_unit)
