"""Load and apply reference catalog data (units, tags) from YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealroulette.data.conversion_approval import resolve_conversion_approved
from mealroulette.models.catalog import Ingredient, IngredientUnitConversion, Tag, Unit
from mealroulette.models.enums import ConversionConfidence, ConversionSource, UnitDimension
from mealroulette.services.catalog import normalize_name

REFERENCE_DIR = Path(__file__).parent / "reference"


@dataclass(frozen=True)
class SeedResult:
    units_added: int
    tags_added: int
    conversions_added: int

    @property
    def total_added(self) -> int:
        return self.units_added + self.tags_added + self.conversions_added


def _load_yaml(filename: str) -> dict:
    path = REFERENCE_DIR / filename
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_reference_units() -> list[dict]:
    return _load_yaml("units.yaml")["units"]


def load_reference_tags() -> list[dict]:
    return _load_yaml("tags.yaml")["tags"]


def load_reference_ingredient_conversions() -> list[dict]:
    """Flatten approved conversions from the canonical ingredient seed file."""
    from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH, load_ingredient_seed

    data = load_ingredient_seed(DEFAULT_INGREDIENT_SEED_PATH)
    rows: list[dict] = []
    for ingredient_row in data["ingredients"]:
        canonical = normalize_name(ingredient_row["canonical_name"])
        for conversion_row in ingredient_row.get("unit_conversions") or []:
            if not resolve_conversion_approved(conversion_row, ingredient_row, bootstrap_approve=True):
                continue
            rows.append(
                {
                    "ingredient": canonical,
                    "from_unit": conversion_row["from_unit"],
                    "to_unit": conversion_row["to_unit"],
                    "factor": str(conversion_row["factor"]),
                    "notes": conversion_row.get("basis"),
                }
            )
    return rows


def seed_reference_units(db: Session, rows: list[dict] | None = None) -> int:
    """Insert reference units idempotently (matches on symbol or name)."""
    units_by_symbol = {unit.symbol: unit for unit in db.scalars(select(Unit))}
    units_by_name = {unit.name: unit for unit in db.scalars(select(Unit))}
    units_added = 0

    for row in rows or load_reference_units():
        symbol = row["symbol"]
        name = row["name"]
        if symbol in units_by_symbol or name in units_by_name:
            continue

        unit = Unit(
            name=name,
            symbol=symbol,
            dimension=UnitDimension(row["dimension"]),
            conversion_to_base=Decimal(str(row["conversion_to_base"])),
        )
        db.add(unit)
        try:
            with db.begin_nested():
                db.flush()
        except IntegrityError:
            continue

        units_by_symbol[symbol] = unit
        units_by_name[name] = unit
        units_added += 1

    return units_added


def seed_ingredient_conversions(db: Session) -> int:
    """Insert approximate unit conversions for ingredients that already exist."""
    units_by_symbol = {unit.symbol: unit for unit in db.scalars(select(Unit))}
    ingredients_by_canonical = {
        ingredient.canonical_name: ingredient for ingredient in db.scalars(select(Ingredient))
    }
    existing = {
        (conversion.ingredient_id, conversion.from_unit_id, conversion.to_unit_id)
        for conversion in db.scalars(select(IngredientUnitConversion))
    }

    conversions_added = 0
    for row in load_reference_ingredient_conversions():
        ingredient = ingredients_by_canonical.get(normalize_name(row["ingredient"]))
        if ingredient is None:
            continue
        from_unit = units_by_symbol.get(row["from_unit"])
        to_unit = units_by_symbol.get(row["to_unit"])
        if from_unit is None or to_unit is None:
            continue
        key = (ingredient.id, from_unit.id, to_unit.id)
        if key in existing:
            continue
        db.add(
            IngredientUnitConversion(
                ingredient_id=ingredient.id,
                from_unit_id=from_unit.id,
                to_unit_id=to_unit.id,
                factor=Decimal(row["factor"]),
                confidence=ConversionConfidence.approximate,
                notes=row.get("notes"),
                approved=True,
                source=ConversionSource.seed,
            )
        )
        conversions_added += 1

    return conversions_added


def seed_catalog_data(db: Session) -> SeedResult:
    """Insert reference units and tags that are not already present."""
    units_added = seed_reference_units(db)
    tags_added = 0

    existing_tags = {(tag.family, tag.name) for tag in db.scalars(select(Tag))}
    for row in load_reference_tags():
        key = (row["family"], row["name"])
        if key in existing_tags:
            continue
        db.add(Tag(family=row["family"], name=row["name"], description=row.get("description")))
        tags_added += 1

    conversions_added = seed_ingredient_conversions(db)

    if units_added or tags_added or conversions_added:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return SeedResult(units_added=0, tags_added=0, conversions_added=0)

    return SeedResult(
        units_added=units_added,
        tags_added=tags_added,
        conversions_added=conversions_added,
    )
