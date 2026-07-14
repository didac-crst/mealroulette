import pytest

from mealroulette.data.import_ingredients import (
    DEFAULT_INGREDIENT_SEED_PATH,
    import_ingredient_seed,
    load_ingredient_seed,
)
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
def test_import_ingredient_seed_updates_dish_created_ingredient(db_session, catalog_seed):
    dish_style = Ingredient(
        canonical_name="arborio rice",
        display_name="arborio rice",
        category=None,
    )
    db_session.add(dish_style)
    db_session.commit()

    result = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)

    assert result.ingredients_updated >= 1
    refreshed = db_session.scalar(
        select(Ingredient).where(Ingredient.canonical_name.in_(["arborio_rice", "arborio rice"]))
    )
    assert refreshed is not None
    assert refreshed.category in {"grain", "carbohydrate"}


@pytest.mark.integration
def test_import_ingredient_seed_backfills_uncategorized_alias_name(db_session, catalog_seed):
    dish_style = Ingredient(
        canonical_name="dried tomatoes",
        display_name="dried tomatoes",
        category=None,
    )
    db_session.add(dish_style)
    db_session.commit()
    ingredient_id = dish_style.id

    result = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)

    assert result.ingredients_updated >= 1
    refreshed = db_session.get(Ingredient, ingredient_id)
    assert refreshed is not None
    assert refreshed.category == "preserved"


@pytest.mark.integration
def test_import_ingredient_seed_is_idempotent(db_session, catalog_seed):
    first = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    second = import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    assert first.ingredients_added > 0
    assert second.ingredients_added == 0
    assert second.ingredients_updated == 0
    assert second.aliases_added == 0
    assert second.conversions_added == 0


def test_load_ingredient_seed_rejects_duplicate_canonical_names(tmp_path):
    seed = tmp_path / "ingredients.yaml"
    seed.write_text(
        """
ingredients:
  - canonical_name: carrot
    display_name: Carrot
  - canonical_name: carrot
    display_name: Carrot duplicate
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate canonical_name"):
        load_ingredient_seed(seed)


def test_load_ingredient_seed_rejects_alias_collision(tmp_path):
    seed = tmp_path / "ingredients.yaml"
    seed.write_text(
        """
ingredients:
  - canonical_name: carrot
    display_name: Carrot
    aliases:
      - orange vegetable
  - canonical_name: pumpkin
    display_name: Pumpkin
    aliases:
      - orange vegetable
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="clashing identities"):
        load_ingredient_seed(seed)
