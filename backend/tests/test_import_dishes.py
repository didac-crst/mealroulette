from pathlib import Path

import pytest
from sqlalchemy import func, select

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, RecipeStep


@pytest.mark.integration
def test_import_sample_dishes_fixture(db_session, catalog_seed):
    result = import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    assert result.dishes_added == 8
    assert result.dishes_skipped == 0
    assert result.recipes_added == 8
    assert result.steps_added > 0
    assert result.ingredients_added > 0
    assert result.ingredients_created > 0

    dish_count = db_session.scalar(select(func.count()).select_from(Dish))
    assert dish_count == 8

    risotto = db_session.scalar(select(Dish).where(Dish.name == "Mushroom Risotto"))
    assert risotto is not None
    assert risotto.suitable_for_lunch is True
    assert len(risotto.tags) == 4

    recipes = db_session.scalars(select(Recipe).where(Recipe.dish_id == risotto.id)).all()
    assert len(recipes) == 1
    assert recipes[0].is_main is True
    assert recipes[0].variant_name == "Classic"

    steps = db_session.scalars(select(RecipeStep).where(RecipeStep.recipe_id == recipes[0].id)).all()
    assert len(steps) == 5

    ingredients = db_session.scalars(
        select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipes[0].id)
    ).all()
    assert len(ingredients) == 9


@pytest.mark.integration
def test_import_sample_dishes_is_idempotent(db_session, catalog_seed):
    first = import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)
    second = import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    assert first.dishes_added == 8
    assert second.dishes_added == 0
    assert second.dishes_skipped == 8

    dish_count = db_session.scalar(select(func.count()).select_from(Dish))
    assert dish_count == 8

    ingredient_count = db_session.scalar(select(func.count()).select_from(Ingredient))
    assert ingredient_count == first.ingredients_created


def test_load_fixture_rejects_invalid_file(tmp_path: Path):
    from mealroulette.data.import_dishes import load_fixture

    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("version: 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid fixture"):
        load_fixture(bad_file)
