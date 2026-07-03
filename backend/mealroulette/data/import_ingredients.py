"""Import canonical ingredients from YAML seed into the catalog."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.data.conversion_approval import resolve_conversion_approved
from mealroulette.data.seed_catalog import seed_reference_units
from mealroulette.models.catalog import Ingredient, IngredientAlias, IngredientUnitConversion, Unit
from mealroulette.models.enums import (
    AggregationStrategy,
    ConversionConfidence,
    ConversionSource,
)
from mealroulette.services.catalog import normalize_name

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


def import_ingredient_seed(
    db: Session,
    path: Path | str = DEFAULT_INGREDIENT_SEED_PATH,
    *,
    bootstrap_approve: bool = True,
) -> IngredientImportResult:
    """Import ingredients, aliases, and conversions from the YAML seed file."""
    data = load_ingredient_seed(path)

    units_added = seed_reference_units(db, data.get("units", []))
    if units_added:
        db.flush()

    units_by_symbol = {unit.symbol: unit for unit in db.scalars(select(Unit))}
    ingredients_by_canonical = {
        ingredient.canonical_name: ingredient for ingredient in db.scalars(select(Ingredient))
    }
    existing_aliases = {
        alias.alias.lower()
        for alias in db.scalars(select(IngredientAlias))
    }
    existing_conversions = {
        (conversion.ingredient_id, conversion.from_unit_id, conversion.to_unit_id)
        for conversion in db.scalars(select(IngredientUnitConversion))
    }

    ingredients_added = 0
    ingredients_skipped = 0
    aliases_added = 0
    conversions_added = 0
    unknown_unit_skips = 0

    for row in data["ingredients"]:
        canonical = normalize_name(row["canonical_name"])
        ingredient = ingredients_by_canonical.get(canonical)
        default_unit_id = _unit_id(units_by_symbol, row.get("default_recipe_unit"))
        preferred_shopping_unit_id = _unit_id(units_by_symbol, row.get("preferred_shopping_unit"))
        aggregation_unit_id = _unit_id(units_by_symbol, row.get("aggregation_unit"))
        season_start, season_end = _season_months(row.get("seasonality"))

        if ingredient is None:
            ingredient = Ingredient(
                canonical_name=canonical,
                display_name=row["display_name"],
                category=row.get("category"),
                family=row.get("family"),
                default_unit_id=default_unit_id,
                preferred_shopping_unit_id=preferred_shopping_unit_id,
                aggregation_unit_id=aggregation_unit_id,
                aggregation_strategy=_parse_strategy(row.get("aggregation_strategy")),
                pantry_item=bool(row.get("pantry_item", False)),
                season_start_month=season_start,
                season_end_month=season_end,
                notes=row.get("description"),
            )
            db.add(ingredient)
            db.flush()
            ingredients_by_canonical[canonical] = ingredient
            ingredients_added += 1
            alias_candidates = {canonical, *(normalize_name(alias) for alias in row.get("aliases", []))}
            for alias in alias_candidates:
                if alias in existing_aliases:
                    continue
                db.add(IngredientAlias(ingredient_id=ingredient.id, alias=alias))
                existing_aliases.add(alias)
                aliases_added += 1
        else:
            ingredients_skipped += 1
            alias_candidates = {normalize_name(alias) for alias in row.get("aliases", [])}
            for alias in alias_candidates:
                if alias in existing_aliases:
                    continue
                db.add(IngredientAlias(ingredient_id=ingredient.id, alias=alias))
                existing_aliases.add(alias)
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

    db.commit()
    return IngredientImportResult(
        units_added=units_added,
        ingredients_added=ingredients_added,
        ingredients_skipped=ingredients_skipped,
        aliases_added=aliases_added,
        conversions_added=conversions_added,
        unknown_unit_skips=unknown_unit_skips,
    )
