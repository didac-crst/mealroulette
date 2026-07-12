"""Import canonical ingredients from YAML seed into the catalog."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.data.conversion_approval import resolve_conversion_approved
from mealroulette.data.seed_catalog import seed_reference_units
from mealroulette.data.taxonomy_loader import validate_ingredient_taxonomy_rows
from mealroulette.models.catalog import Ingredient, IngredientAlias, IngredientUnitConversion, Unit
from mealroulette.models.enums import (
    AggregationStrategy,
    ConversionConfidence,
    ConversionSource,
)
from mealroulette.services.names import normalize_name
from mealroulette.services.food_groups import food_group_for_ingredient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DEFAULT_INGREDIENT_SEED_PATH = FIXTURES_DIR / "mealroulette_ingredients_seed.yaml"

_CONFIDENCE_MAP = {
    "exact": ConversionConfidence.exact,
    "high": ConversionConfidence.high,
    "medium": ConversionConfidence.medium,
    "low": ConversionConfidence.low,
    "not_recommended": ConversionConfidence.not_recommended,
    "approximate": ConversionConfidence.approximate,
    "measured": ConversionConfidence.measured,
}

_SOURCE_MAP = {
    "manual": ConversionSource.manual,
    "seed": ConversionSource.seed,
    "seed_suggestion": ConversionSource.seed,
    "llm_suggested": ConversionSource.llm_suggested,
}


@dataclass(frozen=True)
class IngredientImportResult:
    units_added: int
    ingredients_added: int
    ingredients_updated: int
    ingredients_skipped: int
    aliases_added: int
    conversions_added: int
    unknown_unit_skips: int


def load_ingredient_seed(path: Path | str = DEFAULT_INGREDIENT_SEED_PATH) -> dict:
    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or "ingredients" not in data:
        raise ValueError(f"Invalid ingredient seed file: {fixture_path}")
    return data


def _parse_confidence(raw: str | None) -> ConversionConfidence:
    if raw is None:
        return ConversionConfidence.medium
    return _CONFIDENCE_MAP.get(raw, ConversionConfidence.approximate)


def _parse_source(raw: str | None) -> ConversionSource:
    if raw is None:
        return ConversionSource.seed
    return _SOURCE_MAP.get(raw, ConversionSource.seed)


def _parse_strategy(raw: str | None) -> AggregationStrategy | None:
    if not raw:
        return None
    return AggregationStrategy(raw)


def _season_months(seasonality: dict | None) -> tuple[int | None, int | None]:
    if not seasonality:
        return None, None
    months = seasonality.get("preferred_months") or []
    if not months or len(months) >= 12:
        return None, None
    return min(months), max(months)


def _resolve_approved(
    conversion_row: dict,
    ingredient_row: dict,
    *,
    bootstrap_approve: bool,
) -> bool:
    return resolve_conversion_approved(
        conversion_row,
        ingredient_row,
        bootstrap_approve=bootstrap_approve,
    )


def _unit_id(units_by_symbol: dict[str, Unit], symbol: str | None) -> int | None:
    if not symbol:
        return None
    unit = units_by_symbol.get(symbol)
    return unit.id if unit else None


def _row_lookup_keys(row: dict) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    canonical = normalize_name(row["canonical_name"])
    for candidate in (
        canonical.replace("_", " "),
        normalize_name(row["display_name"]),
        *(normalize_name(alias) for alias in row.get("aliases", [])),
        canonical,
    ):
        if candidate and candidate not in seen:
            seen.add(candidate)
            keys.append(candidate)
    return keys


def _find_ingredient_for_row(
    row: dict,
    *,
    ingredients_by_canonical: dict[str, Ingredient],
    alias_to_ingredient: dict[str, Ingredient],
) -> Ingredient | None:
    for key in _row_lookup_keys(row):
        ingredient = ingredients_by_canonical.get(key)
        if ingredient is not None:
            return ingredient
        ingredient = alias_to_ingredient.get(key)
        if ingredient is not None:
            return ingredient
    return None


def _apply_seed_row_to_ingredient(
    ingredient: Ingredient,
    row: dict,
    *,
    canonical: str,
    units_by_symbol: dict[str, Unit],
) -> None:
    season_start, season_end = _season_months(row.get("seasonality"))
    ingredient.canonical_name = canonical
    ingredient.display_name = row["display_name"]
    ingredient.category = row.get("category")
    ingredient.family = row.get("family")
    ingredient.food_group = food_group_for_ingredient(
        food_group=row.get("food_group"),
        category=row.get("category"),
        family=row.get("family"),
    )
    ingredient.storage_class = row.get("storage_class")
    ingredient.storage_after_opening = row.get("storage_after_opening")
    ingredient.culinary_category = row.get("culinary_category")
    ingredient.product_form = row.get("product_form")
    ingredient.preservation = row.get("preservation")
    traits = row.get("traits")
    ingredient.traits_json = traits if isinstance(traits, dict) else None
    ingredient.default_unit_id = _unit_id(units_by_symbol, row.get("default_recipe_unit"))
    ingredient.preferred_shopping_unit_id = _unit_id(units_by_symbol, row.get("preferred_shopping_unit"))
    ingredient.aggregation_unit_id = _unit_id(units_by_symbol, row.get("aggregation_unit"))
    ingredient.aggregation_strategy = _parse_strategy(row.get("aggregation_strategy"))
    ingredient.pantry_item = bool(row.get("pantry_item", False))
    ingredient.season_start_month = season_start
    ingredient.season_end_month = season_end
    ingredient.notes = row.get("description")


def _register_ingredient_lookup(
    ingredient: Ingredient,
    row: dict,
    *,
    ingredients_by_canonical: dict[str, Ingredient],
    alias_to_ingredient: dict[str, Ingredient],
) -> None:
    ingredients_by_canonical[normalize_name(ingredient.canonical_name)] = ingredient
    for key in _row_lookup_keys(row):
        alias_to_ingredient[key] = ingredient


def _resolve_canonical(
    ingredient: Ingredient,
    canonical: str,
    ingredients_by_canonical: dict[str, Ingredient],
) -> str:
    previous_canonical = normalize_name(ingredient.canonical_name)
    rename_conflict = (
        canonical != previous_canonical
        and canonical in ingredients_by_canonical
        and ingredients_by_canonical[canonical].id != ingredient.id
    )
    return previous_canonical if rename_conflict else canonical


def _needs_category(ingredient: Ingredient) -> bool:
    return not ingredient.category or not ingredient.category.strip()


def _ingredient_matches_row(ingredient: Ingredient, row: dict) -> bool:
    return normalize_name(ingredient.canonical_name) in _row_lookup_keys(row)


def _backfill_uncategorized_ingredients(
    db: Session,
    rows: list[dict],
    *,
    units_by_symbol: dict[str, Unit],
    ingredients_by_canonical: dict[str, Ingredient],
    alias_to_ingredient: dict[str, Ingredient],
) -> int:
    updated = 0
    for ingredient in db.scalars(select(Ingredient)):
        if not _needs_category(ingredient):
            continue
        for row in rows:
            if not _ingredient_matches_row(ingredient, row):
                continue
            if not row.get("category"):
                break
            canonical = normalize_name(row["canonical_name"])
            previous_canonical = normalize_name(ingredient.canonical_name)
            apply_canonical = _resolve_canonical(ingredient, canonical, ingredients_by_canonical)
            _apply_seed_row_to_ingredient(
                ingredient,
                row,
                canonical=apply_canonical,
                units_by_symbol=units_by_symbol,
            )
            if apply_canonical != previous_canonical:
                ingredients_by_canonical.pop(previous_canonical, None)
            _register_ingredient_lookup(
                ingredient,
                row,
                ingredients_by_canonical=ingredients_by_canonical,
                alias_to_ingredient=alias_to_ingredient,
            )
            if not _needs_category(ingredient):
                updated += 1
            break
    return updated


def import_ingredient_seed(
    db: Session,
    path: Path | str = DEFAULT_INGREDIENT_SEED_PATH,
    *,
    bootstrap_approve: bool = True,
) -> IngredientImportResult:
    """Import ingredients, aliases, and conversions from the YAML seed file."""
    data = load_ingredient_seed(path)
    rows = data["ingredients"]
    validation_errors = validate_ingredient_taxonomy_rows(rows)
    if validation_errors:
        raise ValueError("Ingredient seed failed taxonomy validation:\n" + "\n".join(validation_errors))

    units_added = seed_reference_units(db, data.get("units", []))
    if units_added:
        db.flush()

    units_by_symbol = {unit.symbol: unit for unit in db.scalars(select(Unit))}
    ingredients_by_canonical = {
        normalize_name(ingredient.canonical_name): ingredient
        for ingredient in db.scalars(select(Ingredient))
    }
    alias_to_ingredient: dict[str, Ingredient] = {}
    for alias in db.scalars(select(IngredientAlias).options(selectinload(IngredientAlias.ingredient))):
        alias_to_ingredient[alias.alias.lower()] = alias.ingredient
    existing_aliases = set(alias_to_ingredient)
    existing_conversions = {
        (conversion.ingredient_id, conversion.from_unit_id, conversion.to_unit_id)
        for conversion in db.scalars(select(IngredientUnitConversion))
    }

    ingredients_added = 0
    ingredients_updated = 0
    ingredients_skipped = 0
    aliases_added = 0
    conversions_added = 0
    unknown_unit_skips = 0

    for row in data["ingredients"]:
        canonical = normalize_name(row["canonical_name"])
        ingredient = _find_ingredient_for_row(
            row,
            ingredients_by_canonical=ingredients_by_canonical,
            alias_to_ingredient=alias_to_ingredient,
        )

        if ingredient is None:
            ingredient = Ingredient(
                canonical_name=canonical,
                display_name=row["display_name"],
            )
            db.add(ingredient)
            db.flush()
            _apply_seed_row_to_ingredient(
                ingredient,
                row,
                canonical=canonical,
                units_by_symbol=units_by_symbol,
            )
            ingredients_added += 1
        else:
            previous_canonical = normalize_name(ingredient.canonical_name)
            previous_category = ingredient.category
            apply_canonical = _resolve_canonical(ingredient, canonical, ingredients_by_canonical)
            _apply_seed_row_to_ingredient(
                ingredient,
                row,
                canonical=apply_canonical,
                units_by_symbol=units_by_symbol,
            )
            if previous_category == row.get("category") and apply_canonical == previous_canonical:
                ingredients_skipped += 1
            else:
                ingredients_updated += 1
            if apply_canonical != previous_canonical:
                ingredients_by_canonical.pop(previous_canonical, None)

        _register_ingredient_lookup(
            ingredient,
            row,
            ingredients_by_canonical=ingredients_by_canonical,
            alias_to_ingredient=alias_to_ingredient,
        )

        alias_candidates = {canonical, *(normalize_name(alias) for alias in row.get("aliases", []))}
        for alias in alias_candidates:
            if alias in existing_aliases:
                continue
            db.add(IngredientAlias(ingredient_id=ingredient.id, alias=alias))
            existing_aliases.add(alias)
            alias_to_ingredient[alias] = ingredient
            aliases_added += 1

        for conversion_row in row.get("unit_conversions") or []:
            from_unit = units_by_symbol.get(conversion_row["from_unit"])
            to_unit = units_by_symbol.get(conversion_row["to_unit"])
            if from_unit is None or to_unit is None:
                unknown_unit_skips += 1
                continue
            key = (ingredient.id, from_unit.id, to_unit.id)
            if key in existing_conversions:
                continue
            db.add(
                IngredientUnitConversion(
                    ingredient_id=ingredient.id,
                    from_unit_id=from_unit.id,
                    to_unit_id=to_unit.id,
                    factor=Decimal(str(conversion_row["factor"])),
                    confidence=_parse_confidence(conversion_row.get("confidence")),
                    notes=conversion_row.get("basis"),
                    approved=_resolve_approved(conversion_row, row, bootstrap_approve=bootstrap_approve),
                    source=_parse_source(conversion_row.get("source")),
                )
            )
            existing_conversions.add(key)
            conversions_added += 1

    ingredients_updated += _backfill_uncategorized_ingredients(
        db,
        data["ingredients"],
        units_by_symbol=units_by_symbol,
        ingredients_by_canonical=ingredients_by_canonical,
        alias_to_ingredient=alias_to_ingredient,
    )

    db.commit()
    return IngredientImportResult(
        units_added=units_added,
        ingredients_added=ingredients_added,
        ingredients_updated=ingredients_updated,
        ingredients_skipped=ingredients_skipped,
        aliases_added=aliases_added,
        conversions_added=conversions_added,
        unknown_unit_skips=unknown_unit_skips,
    )
