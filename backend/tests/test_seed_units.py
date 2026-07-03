import pytest
from sqlalchemy import select

from mealroulette.data.seed_catalog import load_reference_units, seed_reference_units
from mealroulette.models.catalog import Unit


@pytest.mark.integration
def test_seed_reference_units_skips_existing_name_or_symbol(db_session, catalog_seed):
    existing = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    assert existing is not None

    duplicate_rows = [
        {"name": existing.name, "symbol": "brand_new_symbol", "dimension": "mass", "conversion_to_base": "1"},
        {"name": "brand_new_name", "symbol": existing.symbol, "dimension": "mass", "conversion_to_base": "1"},
    ]
    added = seed_reference_units(db_session, duplicate_rows)
    assert added == 0


@pytest.mark.integration
def test_seed_reference_units_idempotent_with_extended_yaml(db_session, catalog_seed):
    first = seed_reference_units(db_session, load_reference_units())
    second = seed_reference_units(db_session, load_reference_units())
    assert second == 0
    assert first >= 0
