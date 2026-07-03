from decimal import Decimal

import pytest
from sqlalchemy import select

from mealroulette.data.seed_catalog import seed_ingredient_conversions
from mealroulette.models.catalog import Ingredient, IngredientUnitConversion, Unit
from mealroulette.services.catalog import normalize_name


@pytest.mark.integration
def test_seed_ingredient_conversions_links_existing_ingredients(db_session, catalog_seed):
    db_session.add(
        Ingredient(
            canonical_name=normalize_name("carrot"),
            display_name="Carrot",
        )
    )
    db_session.commit()

    added = seed_ingredient_conversions(db_session)
    db_session.commit()

    assert added >= 1
    carrot = db_session.scalar(select(Ingredient).where(Ingredient.canonical_name == "carrot"))
    unit = db_session.scalar(select(Unit).where(Unit.symbol == "unit"))
    gram = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    conversion = db_session.scalar(
        select(IngredientUnitConversion).where(
            IngredientUnitConversion.ingredient_id == carrot.id,
            IngredientUnitConversion.from_unit_id == unit.id,
            IngredientUnitConversion.to_unit_id == gram.id,
        )
    )
    assert conversion is not None
    assert conversion.factor == Decimal("80")
    assert conversion.approved is True

    second_run = seed_ingredient_conversions(db_session)
    db_session.commit()
    assert second_run == 0
