import pytest

from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH, import_ingredient_seed
from mealroulette.models.catalog import Ingredient, IngredientUnitConversion
from sqlalchemy import select


@pytest.mark.integration
def test_import_ingredient_seed_creates_carrot_with_approved_conversion(db_session, catalog_seed):
    result = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    assert result.ingredients_added >= 1

    carrot = db_session.scalar(select(Ingredient).where(Ingredient.canonical_name == "carrot"))
    assert carrot is not None
    assert carrot.aggregation_strategy.value == "allow_approximate_conversion"
    assert carrot.preferred_shopping_unit_id is not None

    conversions = list(
        db_session.scalars(select(IngredientUnitConversion).where(IngredientUnitConversion.ingredient_id == carrot.id))
    )
    unit_to_gram = next(
        (conversion for conversion in conversions if conversion.to_unit.symbol == "g"),
        None,
    )
    assert unit_to_gram is not None
    assert unit_to_gram.approved is True
    assert unit_to_gram.factor == 80


@pytest.mark.integration
def test_import_ingredient_seed_is_idempotent(db_session, catalog_seed):
    first = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    second = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    assert first.ingredients_added > 0
    assert second.ingredients_added == 0
    assert second.aliases_added == 0
    assert second.conversions_added == 0
