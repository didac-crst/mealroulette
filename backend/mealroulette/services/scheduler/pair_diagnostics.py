from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mealroulette.models.catalog import Recipe
from mealroulette.models.enums import SimpleDishPart
from mealroulette.services.food_groups import CARB_FOOD_GROUP, PROTEIN_FOOD_GROUPS, food_group_for_ingredient
from mealroulette.services.quantities import UnitInfo
from mealroulette.services.scheduler.family_vector import (
    family_key_for_ingredient,
    ingredient_line_to_reference_grams,
    vector_line_from_recipe_ingredient,
)

PRIMARY_INGREDIENT_MIN_SHARE_PCT = 20.0
TOP_PRIMARY_INGREDIENT_COUNT = 2
UNUSUALLY_DOMINANT_PANTRY_SHARE_PCT = 25.0

TRIVIAL_FOOD_GROUPS = frozenset({"pantry", "condiment", "herb", "spice"})
TRIVIAL_CATEGORIES = frozenset({"pantry", "condiment", "herb", "spice"})

CENTERPIECE_PROTEIN_MIN_SHARE_PCT = 25.0
CENTERPIECE_CARB_MIN_SHARE_PCT = 33.0
CENTERPIECE_VEGETABLE_MIN_SHARE_PCT = 40.0
CENTERPIECE_LEGUME_MIN_SHARE_PCT = 25.0

SIDE_PROTEIN_MIN_SHARE_PCT = 20.0
SIDE_CARB_MIN_SHARE_PCT = 30.0
SIDE_VEGETABLE_MIN_SHARE_PCT = 35.0
SAUCE_OR_CONDIMENT_MAX_GRAMS = 80.0


class SimpleDishSemanticRole(StrEnum):
    protein_centerpiece = "protein_centerpiece"
    carb_centerpiece = "carb_centerpiece"
    vegetable_centerpiece = "vegetable_centerpiece"
    legume_centerpiece = "legume_centerpiece"
    mixed_centerpiece = "mixed_centerpiece"
    protein_side = "protein_side"
    carb_side = "carb_side"
    vegetable_side = "vegetable_side"
    salad_side = "salad_side"
    soup_side = "soup_side"
    bread_side = "bread_side"
    sauce_or_condiment = "sauce_or_condiment"


@dataclass(frozen=True)
class PrimaryIngredient:
    ingredient_id: int
    canonical_name: str
    family_key: str | None
    grams: float
    share_pct: float


@dataclass(frozen=True)
class RecipePairDiagnostics:
    primary_ingredients: tuple[PrimaryIngredient, ...]
    primary_ingredient_ids: frozenset[int]
    primary_family_keys: frozenset[str]
    semantic_role: SimpleDishSemanticRole | None


@dataclass(frozen=True)
class CandidatePairSummary:
    primary_ingredient_ids: frozenset[int]
    primary_family_keys: frozenset[str]
    semantic_role: SimpleDishSemanticRole | None


def _is_trivial_ingredient(*, pantry_item: bool, food_group: str, category: str | None, share_pct: float) -> bool:
    if not pantry_item and food_group not in TRIVIAL_FOOD_GROUPS and (category or "").lower() not in TRIVIAL_CATEGORIES:
        return False
    return share_pct < UNUSUALLY_DOMINANT_PANTRY_SHARE_PCT


def derive_primary_ingredients(
    recipe: Recipe,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    vector_min_grams: int = 5,
    default_grams_per_count: int = 100,
) -> tuple[PrimaryIngredient, ...]:
    scored_lines: list[PrimaryIngredient] = []
    ingredient_meta: dict[int, tuple[bool, str, str | None]] = {}
    total_grams = Decimal("0")

    for recipe_ingredient in recipe.ingredients:
        line = vector_line_from_recipe_ingredient(recipe_ingredient)
        ingredient = recipe_ingredient.ingredient
        if line is None or ingredient is None:
            continue

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

        if grams < Decimal(vector_min_grams):
            continue

        total_grams += grams
        family_key = family_key_for_ingredient(
            family=ingredient.family,
            category=ingredient.category,
            canonical_name=ingredient.canonical_name,
        )
        food_group = food_group_for_ingredient(
            food_group=ingredient.food_group,
            category=ingredient.category,
            family=ingredient.family,
        )
        ingredient_meta[ingredient.id] = (ingredient.pantry_item, food_group, ingredient.category)
        scored_lines.append(
            PrimaryIngredient(
                ingredient_id=ingredient.id,
                canonical_name=ingredient.canonical_name,
                family_key=family_key,
                grams=float(grams),
                share_pct=0.0,
            )
        )

    if total_grams <= 0 or not scored_lines:
        return ()

    with_shares = [
        PrimaryIngredient(
            ingredient_id=entry.ingredient_id,
            canonical_name=entry.canonical_name,
            family_key=entry.family_key,
            grams=entry.grams,
            share_pct=float((Decimal(str(entry.grams)) / total_grams) * Decimal("100")),
        )
        for entry in scored_lines
    ]
    ranked = sorted(with_shares, key=lambda entry: entry.grams, reverse=True)

    non_trivial: list[PrimaryIngredient] = []
    for entry in ranked:
        pantry_item, food_group, category = ingredient_meta[entry.ingredient_id]
        if _is_trivial_ingredient(
            pantry_item=pantry_item,
            food_group=food_group,
            category=category,
            share_pct=entry.share_pct,
        ):
            continue
        non_trivial.append(entry)

    selected: dict[int, PrimaryIngredient] = {}
    for entry in non_trivial:
        if entry.share_pct >= PRIMARY_INGREDIENT_MIN_SHARE_PCT:
            selected[entry.ingredient_id] = entry
    for entry in non_trivial[:TOP_PRIMARY_INGREDIENT_COUNT]:
        selected[entry.ingredient_id] = entry

    return tuple(sorted(selected.values(), key=lambda entry: entry.grams, reverse=True))


def primary_ingredient_ids(primary_ingredients: tuple[PrimaryIngredient, ...]) -> frozenset[int]:
    return frozenset(entry.ingredient_id for entry in primary_ingredients)


def primary_family_keys(primary_ingredients: tuple[PrimaryIngredient, ...]) -> frozenset[str]:
    return frozenset(key for entry in primary_ingredients if (key := entry.family_key))


def _normalized_tags(tag_names: frozenset[str] | set[str] | None) -> frozenset[str]:
    if not tag_names:
        return frozenset()
    return frozenset(tag.strip().lower() for tag in tag_names)


def _weight(traits: dict, group: str) -> float:
    weights = traits.get("food_group_weights")
    if not isinstance(weights, dict):
        return 0.0
    value = weights.get(group, 0.0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _protein_share(traits: dict) -> float:
    return sum(_weight(traits, group) for group in PROTEIN_FOOD_GROUPS)


def derive_simple_dish_semantic_role(
    traits: dict | None,
    *,
    simple_dish_part: SimpleDishPart | None,
    tag_names: frozenset[str] | set[str] | None = None,
) -> SimpleDishSemanticRole | None:
    if simple_dish_part is None or traits is None:
        return None

    tags = _normalized_tags(tag_names)
    total_trait_grams = float(traits.get("total_trait_grams") or 0.0)
    dominant_protein = traits.get("dominant_protein")
    dominant_carb = traits.get("dominant_carb")

    if simple_dish_part == SimpleDishPart.sidedish:
        if tags.intersection({"salad", "fresh", "raw"}):
            return SimpleDishSemanticRole.salad_side
        if tags.intersection({"soup", "broth"}):
            return SimpleDishSemanticRole.soup_side
        if dominant_carb == "bread_family" or "bread" in tags:
            return SimpleDishSemanticRole.bread_side
        if traits.get("carb_heavy") or _weight(traits, CARB_FOOD_GROUP) >= SIDE_CARB_MIN_SHARE_PCT:
            return SimpleDishSemanticRole.carb_side
        if _protein_share(traits) >= SIDE_PROTEIN_MIN_SHARE_PCT or dominant_protein:
            return SimpleDishSemanticRole.protein_side
        if _weight(traits, "vegetable") >= SIDE_VEGETABLE_MIN_SHARE_PCT:
            return SimpleDishSemanticRole.vegetable_side
        if total_trait_grams <= SAUCE_OR_CONDIMENT_MAX_GRAMS:
            return SimpleDishSemanticRole.sauce_or_condiment
        return SimpleDishSemanticRole.vegetable_side

    legume_share = _weight(traits, "legume")
    if legume_share >= CENTERPIECE_LEGUME_MIN_SHARE_PCT or (
        isinstance(dominant_protein, str) and "legume" in dominant_protein
    ):
        return SimpleDishSemanticRole.legume_centerpiece
    if traits.get("carb_heavy") or _weight(traits, CARB_FOOD_GROUP) >= CENTERPIECE_CARB_MIN_SHARE_PCT:
        return SimpleDishSemanticRole.carb_centerpiece
    if _weight(traits, "vegetable") >= CENTERPIECE_VEGETABLE_MIN_SHARE_PCT:
        return SimpleDishSemanticRole.vegetable_centerpiece
    if _protein_share(traits) >= CENTERPIECE_PROTEIN_MIN_SHARE_PCT or dominant_protein:
        return SimpleDishSemanticRole.protein_centerpiece
    return SimpleDishSemanticRole.mixed_centerpiece


def build_recipe_pair_diagnostics(
    recipe: Recipe,
    *,
    gram_unit: UnitInfo,
    ml_unit: UnitInfo,
    traits: dict | None,
    simple_dish_part: SimpleDishPart | None = None,
    tag_names: frozenset[str] | set[str] | None = None,
    vector_min_grams: int = 5,
    default_grams_per_count: int = 100,
) -> RecipePairDiagnostics:
    primary_ingredients = derive_primary_ingredients(
        recipe,
        gram_unit=gram_unit,
        ml_unit=ml_unit,
        vector_min_grams=vector_min_grams,
        default_grams_per_count=default_grams_per_count,
    )
    return RecipePairDiagnostics(
        primary_ingredients=primary_ingredients,
        primary_ingredient_ids=primary_ingredient_ids(primary_ingredients),
        primary_family_keys=primary_family_keys(primary_ingredients),
        semantic_role=derive_simple_dish_semantic_role(
            traits,
            simple_dish_part=simple_dish_part,
            tag_names=tag_names,
        ),
    )
