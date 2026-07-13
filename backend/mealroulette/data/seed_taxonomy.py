"""Seed food groups and ingredient families from declarative YAML into the database."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mealroulette.data.taxonomy_loader import load_food_groups, load_ingredient_families
from mealroulette.models.catalog import Ingredient
from mealroulette.models.taxonomy import FoodGroup, IngredientFamily
from mealroulette.services.names import normalize_name

INGREDIENT_SEED_PATH = Path(__file__).resolve().parent / "fixtures" / "mealroulette_ingredients_seed.yaml"

# Pre-reconciliation family strings still present in some databases.
LEGACY_FAMILY_ALIASES: dict[str, str] = {
    "bean_vegetable_family": "green_bean_family",
    "cabbage_family": "brassica_family",
    "cheese_family": "hard_cheese_family",
    "olive_family": "olive_pickle_family",
    "seafood_family": "white_fish_family",
    "tofu_soy_family": "soy_family",
}

# Legacy canonical names that are not in the active seed file.
CANONICAL_FAMILY_OVERRIDES: dict[str, str] = {
    "hake fillet": "white_fish_family",
}


@dataclass(frozen=True)
class TaxonomySeedResult:
    food_groups_added: int
    families_added: int
    ingredients_family_id_backfilled: int


@lru_cache(maxsize=1)
def _seed_family_by_canonical_name() -> dict[str, str]:
    with INGREDIENT_SEED_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    families: dict[str, str] = {}
    for row in (data or {}).get("ingredients") or []:
        canonical_name = row.get("canonical_name")
        family = row.get("family")
        if not canonical_name or not family:
            continue
        families[normalize_name(str(canonical_name))] = str(family).strip().lower()
    return families


def _resolve_family_id(
    *,
    canonical_name: str,
    family: str | None,
    family_ids: set[str],
) -> str | None:
    seed_family = _seed_family_by_canonical_name().get(normalize_name(canonical_name))
    if seed_family and seed_family in family_ids:
        return seed_family

    override = CANONICAL_FAMILY_OVERRIDES.get(normalize_name(canonical_name))
    if override and override in family_ids:
        return override

    normalized = (family or "").strip().lower()
    if not normalized:
        return None
    if normalized in family_ids:
        return normalized

    alias_target = LEGACY_FAMILY_ALIASES.get(normalized)
    if alias_target and alias_target in family_ids:
        return alias_target
    return None


def backfill_ingredient_family_ids(db: Session, family_ids: set[str] | None = None) -> int:
    if family_ids is None:
        family_ids = set(db.scalars(select(IngredientFamily.id)))

    backfilled = 0
    for ingredient in db.scalars(select(Ingredient)):
        resolved = _resolve_family_id(
            canonical_name=ingredient.canonical_name,
            family=ingredient.family,
            family_ids=family_ids,
        )
        if resolved is None:
            continue
        if ingredient.family_id == resolved and ingredient.family == resolved:
            continue
        ingredient.family = resolved
        ingredient.family_id = resolved
        backfilled += 1
    db.flush()
    return backfilled


def seed_taxonomy_data(db: Session, *, commit: bool = True) -> TaxonomySeedResult:
    food_groups_added = 0
    for group in load_food_groups():
        existing = db.get(FoodGroup, group.id)
        if existing is None:
            db.add(
                FoodGroup(
                    id=group.id,
                    label=group.label,
                    description=group.description or None,
                )
            )
            food_groups_added += 1
        else:
            existing.label = group.label
            existing.description = group.description or None

    families_added = 0
    for family in load_ingredient_families():
        existing = db.get(IngredientFamily, family.id)
        if existing is None:
            db.add(
                IngredientFamily(
                    id=family.id,
                    food_group_id=family.food_group,
                    label=family.label,
                    description=family.description or None,
                )
            )
            families_added += 1
        else:
            existing.food_group_id = family.food_group
            existing.label = family.label
            existing.description = family.description or None

    db.flush()

    family_ids = set(db.scalars(select(IngredientFamily.id)))
    backfilled = backfill_ingredient_family_ids(db, family_ids)

    if commit:
        db.commit()
    return TaxonomySeedResult(
        food_groups_added=food_groups_added,
        families_added=families_added,
        ingredients_family_id_backfilled=backfilled,
    )


def family_id_exists(db: Session, family_id: str | None) -> bool:
    if not family_id:
        return False
    normalized = family_id.strip().lower()
    return db.get(IngredientFamily, normalized) is not None


def resolve_family_fields(
    db: Session,
    *,
    family: str | None,
    family_id: str | None,
) -> tuple[str | None, str | None]:
    resolved_id = (family_id or family or "").strip().lower() or None
    if resolved_id is None:
        return None, None
    row = db.get(IngredientFamily, resolved_id)
    if row is None:
        raise ValueError(f"Unknown ingredient family: {resolved_id}")
    return resolved_id, row.food_group_id


def count_ingredients_missing_family_id(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Ingredient)
            .where(Ingredient.family.is_not(None), Ingredient.family_id.is_(None))
        )
        or 0
    )
