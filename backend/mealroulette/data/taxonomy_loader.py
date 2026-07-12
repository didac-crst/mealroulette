"""Load Phase 9 ingredient taxonomy from declarative YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

TAXONOMY_DIR = Path(__file__).parent / "taxonomy"


@dataclass(frozen=True)
class FoodGroupDefinition:
    id: str
    label: str
    description: str


@dataclass(frozen=True)
class IngredientFamilyDefinition:
    id: str
    food_group: str
    label: str
    description: str


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid taxonomy file: {path}")
    return data


@lru_cache
def load_food_groups() -> list[FoodGroupDefinition]:
    data = _load_yaml(TAXONOMY_DIR / "food_groups.yaml")
    rows = data.get("food_groups")
    if not isinstance(rows, list):
        raise ValueError("food_groups.yaml must contain a food_groups list")
    groups: list[FoodGroupDefinition] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"Invalid food group row: {row!r}")
        group_id = str(row["id"]).strip().lower()
        if group_id in seen:
            raise ValueError(f"Duplicate food group id: {group_id}")
        seen.add(group_id)
        groups.append(
            FoodGroupDefinition(
                id=group_id,
                label=str(row["label"]),
                description=str(row.get("description") or "").strip(),
            )
        )
    return groups


@lru_cache
def load_ingredient_families() -> list[IngredientFamilyDefinition]:
    data = _load_yaml(TAXONOMY_DIR / "ingredient_families.yaml")
    rows = data.get("ingredient_families")
    if not isinstance(rows, list):
        raise ValueError("ingredient_families.yaml must contain an ingredient_families list")
    food_group_ids = {group.id for group in load_food_groups()}
    families: list[IngredientFamilyDefinition] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"Invalid ingredient family row: {row!r}")
        family_id = str(row["id"]).strip().lower()
        if family_id in seen:
            raise ValueError(f"Duplicate ingredient family id: {family_id}")
        seen.add(family_id)
        food_group = str(row["food_group"]).strip().lower()
        if food_group not in food_group_ids:
            raise ValueError(f"Family {family_id} references unknown food group: {food_group}")
        families.append(
            IngredientFamilyDefinition(
                id=family_id,
                food_group=food_group,
                label=str(row["label"]),
                description=str(row.get("description") or "").strip(),
            )
        )
    return families


@lru_cache
def food_group_ids() -> frozenset[str]:
    return frozenset(group.id for group in load_food_groups())


@lru_cache
def family_ids() -> frozenset[str]:
    return frozenset(family.id for family in load_ingredient_families())


@lru_cache
def family_to_food_group() -> dict[str, str]:
    return {family.id: family.food_group for family in load_ingredient_families()}


def validate_ingredient_taxonomy_rows(rows: list[dict]) -> list[str]:
    """Return validation errors for ingredient seed rows against loaded taxonomy."""
    errors: list[str] = []
    food_groups = food_group_ids()
    families = family_ids()
    family_groups = family_to_food_group()
    canonical_names: set[str] = set()
    aliases: dict[str, str] = {}

    for index, row in enumerate(rows):
        prefix = f"ingredients[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected mapping")
            continue
        canonical = str(row.get("canonical_name", "")).strip().lower()
        if not canonical:
            errors.append(f"{prefix}: missing canonical_name")
            continue
        if canonical in canonical_names:
            errors.append(f"{prefix}: duplicate canonical_name {canonical}")
        canonical_names.add(canonical)

        food_group = row.get("food_group")
        if food_group is not None:
            normalized_group = str(food_group).strip().lower()
            if normalized_group not in food_groups:
                errors.append(f"{prefix}: unknown food_group {normalized_group}")

        family = row.get("family")
        if family is not None:
            normalized_family = str(family).strip().lower()
            if normalized_family not in families:
                errors.append(f"{prefix}: unknown family {normalized_family}")
            elif food_group is not None:
                expected = family_groups.get(normalized_family)
                normalized_group = str(food_group).strip().lower()
                culinary = row.get("culinary_category")
                if expected and normalized_group != expected and not culinary:
                    errors.append(
                        f"{prefix}: food_group {normalized_group} does not match "
                        f"family default {expected} for {normalized_family} "
                        "(set culinary_category if intentional)"
                    )

        for alias in row.get("aliases") or []:
            normalized_alias = str(alias).strip().lower()
            if not normalized_alias:
                continue
            owner = aliases.get(normalized_alias)
            if owner is not None and owner != canonical:
                errors.append(f"{prefix}: duplicate alias {normalized_alias!r} (also on {owner})")
            aliases[normalized_alias] = canonical

    return errors
