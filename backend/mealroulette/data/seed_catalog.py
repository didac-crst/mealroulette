"""Load and apply reference catalog data (units, tags) from YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.catalog import Tag, Unit
from mealroulette.models.enums import UnitDimension

REFERENCE_DIR = Path(__file__).parent / "reference"


@dataclass(frozen=True)
class SeedResult:
    units_added: int
    tags_added: int

    @property
    def total_added(self) -> int:
        return self.units_added + self.tags_added


def _load_yaml(filename: str) -> dict:
    path = REFERENCE_DIR / filename
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_reference_units() -> list[dict]:
    return _load_yaml("units.yaml")["units"]


def load_reference_tags() -> list[dict]:
    return _load_yaml("tags.yaml")["tags"]


def seed_catalog_data(db: Session) -> SeedResult:
    """Insert reference units and tags that are not already present."""
    units_added = 0
    tags_added = 0

    existing_symbols = set(db.scalars(select(Unit.symbol)))
    for row in load_reference_units():
        symbol = row["symbol"]
        if symbol in existing_symbols:
            continue
        db.add(
            Unit(
                name=row["name"],
                symbol=symbol,
                dimension=UnitDimension(row["dimension"]),
                conversion_to_base=Decimal(row["conversion_to_base"]),
            )
        )
        units_added += 1

    existing_tags = {(tag.family, tag.name) for tag in db.scalars(select(Tag))}
    for row in load_reference_tags():
        key = (row["family"], row["name"])
        if key in existing_tags:
            continue
        db.add(Tag(family=row["family"], name=row["name"], description=row.get("description")))
        tags_added += 1

    if units_added or tags_added:
        db.commit()

    return SeedResult(units_added=units_added, tags_added=tags_added)
