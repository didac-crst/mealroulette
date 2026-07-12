from __future__ import annotations

from mealroulette.data.taxonomy_loader import family_to_food_group, food_group_ids

FOOD_GROUPS: frozenset[str] = food_group_ids()

FAMILY_TO_FOOD_GROUP: dict[str, str] = family_to_food_group()

CATEGORY_TO_FOOD_GROUP: dict[str, str] = {
    "vegetable": "vegetable",
    "grain": "carbohydrate",
    "pasta": "carbohydrate",
    "bread": "carbohydrate",
    "pastry": "carbohydrate",
    "potato": "carbohydrate",
    "meat": "meat",
    "fish": "fish",
    "seafood": "seafood",
    "egg": "egg",
    "dairy": "dairy",
    "cheese": "cheese",
    "legume": "legume",
    "plant_protein": "plant_protein",
    "fruit": "fruit",
    "fungus": "fungus",
    "condiment": "condiment",
    "herb": "herb",
    "spice": "spice",
    "stock": "stock",
    "alcohol": "alcohol",
    "pantry": "pantry",
    "canned": "other",
    "preserved": "other",
    "frozen": "other",
}

NON_VEGAN_FOOD_GROUPS: frozenset[str] = frozenset(
    {"meat", "fish", "seafood", "egg", "dairy", "cheese"}
)

PROTEIN_FOOD_GROUPS: frozenset[str] = frozenset(
    {"meat", "fish", "seafood", "egg", "dairy", "cheese", "legume", "plant_protein"}
)

CARB_FOOD_GROUP = "carbohydrate"


def food_group_for_ingredient(
    *,
    food_group: str | None,
    category: str | None,
    family: str | None = None,
) -> str:
    if food_group:
        normalized = food_group.strip().lower()
        if normalized in FOOD_GROUPS:
            return normalized
        return "other"
    if family:
        mapped = FAMILY_TO_FOOD_GROUP.get(family.strip().lower())
        if mapped is not None:
            return mapped
    if category:
        mapped = CATEGORY_TO_FOOD_GROUP.get(category.strip().lower())
        if mapped is not None:
            return mapped
    return "other"
