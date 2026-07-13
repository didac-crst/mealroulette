from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mealroulette.models.catalog import Ingredient, IngredientUnitConversion, Recipe, RecipeIngredient, Unit
from mealroulette.models.enums import UnitDimension
from mealroulette.services.quantities import IngredientConversion, UnitInfo, UnitsNotCompatibleError, convert_quantity


@dataclass(frozen=True)
class VectorIngredientLine:
    family: str | None
    category: str | None
    canonical_name: str
    pantry_item: bool
    quantity: Decimal
    unit: UnitInfo
    conversions: tuple[IngredientConversion, ...] = ()


@dataclass(frozen=True)
class FamilyVectorResult:
    weights: dict[str, float]
    count_fallback_lines: int


def family_key_for_ingredient(*, family: str | None, category: str | None, canonical_name: str) -> str | None:
    if family:
        return family
    if category:
        return category
    if canonical_name:
        return canonical_name
    return None


def ingredient_line_to_reference_grams(
    quantity: Decimal,
    unit: UnitInfo,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    conversions: list[IngredientConversion] | None = None,
    default_grams_per_count: int = 100,
) -> tuple[Decimal, bool]:
    """Convert a recipe line to reference grams for family-vector similarity."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    conversions = conversions or []

    if unit.dimension == UnitDimension.mass:
        grams, _ = convert_quantity(quantity, unit, gram_unit, conversions)
        return grams, False

    if unit.dimension == UnitDimension.volume:
        try:
            ml_amount, _ = convert_quantity(quantity, unit, ml_unit, conversions)
        except UnitsNotCompatibleError:
            ml_amount = quantity
        return ml_amount, False

    if unit.dimension == UnitDimension.count:
        try:
            grams, _ = convert_quantity(quantity, unit, gram_unit, conversions)
            return grams, False
        except UnitsNotCompatibleError:
            return quantity * Decimal(default_grams_per_count), True

    raise ValueError(f"unsupported unit dimension: {unit.dimension.value}")


def build_family_vector(
    lines: list[VectorIngredientLine],
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    vector_min_grams: int = 5,
    default_grams_per_count: int = 100,
) -> FamilyVectorResult:
    family_grams: dict[str, Decimal] = {}
    count_fallback_lines = 0

    for line in lines:
        family_key = family_key_for_ingredient(
            family=line.family,
            category=line.category,
            canonical_name=line.canonical_name,
        )
        if family_key is None:
            continue

        try:
            grams, used_count_fallback = ingredient_line_to_reference_grams(
                line.quantity,
                line.unit,
                gram_unit=gram_unit,
                ml_unit=ml_unit,
                conversions=list(line.conversions),
                default_grams_per_count=default_grams_per_count,
            )
        except ValueError:
            continue

        if used_count_fallback:
            count_fallback_lines += 1

        min_grams = Decimal(vector_min_grams)
        if grams < min_grams:
            continue

        family_grams[family_key] = family_grams.get(family_key, Decimal("0")) + grams

    total_grams = sum(family_grams.values(), start=Decimal("0"))
    if total_grams <= 0:
        return FamilyVectorResult(weights={}, count_fallback_lines=count_fallback_lines)

    weights = {
        family: float((grams / total_grams) * Decimal("100"))
        for family, grams in family_grams.items()
    }
    return FamilyVectorResult(weights=weights, count_fallback_lines=count_fallback_lines)


def unit_info_from_model(unit: Unit) -> UnitInfo:
    return UnitInfo(
        id=unit.id,
        symbol=unit.symbol,
        dimension=unit.dimension,
        conversion_to_base=unit.conversion_to_base,
    )


def approved_conversions_for_ingredient(ingredient: Ingredient) -> list[IngredientConversion]:
    return [
        IngredientConversion(
            from_unit_id=conversion.from_unit_id,
            to_unit_id=conversion.to_unit_id,
            factor=conversion.factor,
        )
        for conversion in ingredient.unit_conversions
        if conversion.approved
    ]


def vector_line_from_recipe_ingredient(recipe_ingredient: RecipeIngredient) -> VectorIngredientLine | None:
    ingredient = recipe_ingredient.ingredient
    if ingredient is None or recipe_ingredient.quantity is None or recipe_ingredient.unit is None:
        return None

    return VectorIngredientLine(
        family=ingredient.family,
        category=ingredient.category,
        canonical_name=ingredient.canonical_name,
        pantry_item=ingredient.pantry_item,
        quantity=recipe_ingredient.quantity,
        unit=unit_info_from_model(recipe_ingredient.unit),
        conversions=tuple(approved_conversions_for_ingredient(ingredient)),
    )


def build_family_vector_for_recipe(
    recipe: Recipe,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    vector_min_grams: int = 5,
    default_grams_per_count: int = 100,
) -> FamilyVectorResult:
    lines: list[VectorIngredientLine] = []
    for recipe_ingredient in recipe.ingredients:
        line = vector_line_from_recipe_ingredient(recipe_ingredient)
        if line is not None:
            lines.append(line)
    return build_family_vector(
        lines,
        gram_unit=gram_unit,
        ml_unit=ml_unit,
        vector_min_grams=vector_min_grams,
        default_grams_per_count=default_grams_per_count,
    )


def build_family_vector_for_dish_main_recipe(
    dish_recipes: list[Recipe],
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    vector_min_grams: int = 5,
    default_grams_per_count: int = 100,
) -> FamilyVectorResult:
    main_recipe = next((recipe for recipe in dish_recipes if recipe.is_main), None)
    if main_recipe is None and dish_recipes:
        main_recipe = dish_recipes[0]
    if main_recipe is None:
        return FamilyVectorResult(weights={}, count_fallback_lines=0)
    return build_family_vector_for_recipe(
        main_recipe,
        gram_unit=gram_unit,
        ml_unit=ml_unit,
        vector_min_grams=vector_min_grams,
        default_grams_per_count=default_grams_per_count,
    )
