from pathlib import Path

import pytest
from sqlalchemy import func, select

from mealroulette.data.import_dishes import (
    DEFAULT_FIXTURE_PATH,
    SIMPLE_DISH_FIXTURE_PATH,
    import_dish_fixtures,
    load_fixture,
)
from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH, import_ingredient_seed
from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, RecipeStep
from mealroulette.models.enums import MealComposition, SimpleDishPart


def _expected_dish_count(path: Path = DEFAULT_FIXTURE_PATH) -> int:
    return len(load_fixture(path)["dishes"])


def _seed_ingredients(db_session) -> int:
    import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    return db_session.scalar(select(func.count()).select_from(Ingredient)) or 0


@pytest.mark.integration
def test_import_sample_dishes_fixture(db_session, catalog_seed):
    ingredient_count_before = _seed_ingredients(db_session)
    expected_dishes = _expected_dish_count()
    result = import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    assert result.dishes_added == expected_dishes
    assert result.dishes_skipped == 0
    assert result.recipes_added == expected_dishes
    assert result.steps_added > 0
    assert result.ingredients_added > 0
    assert result.ingredients_created == 0

    dish_count = db_session.scalar(select(func.count()).select_from(Dish))
    assert dish_count == expected_dishes
    ingredient_count_after = db_session.scalar(select(func.count()).select_from(Ingredient))
    assert ingredient_count_after == ingredient_count_before

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
    ingredient_count_before = _seed_ingredients(db_session)
    expected_dishes = _expected_dish_count()
    first = import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)
    second = import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    assert first.dishes_added == expected_dishes
    assert second.dishes_added == 0
    assert second.dishes_skipped == expected_dishes

    dish_count = db_session.scalar(select(func.count()).select_from(Dish))
    assert dish_count == expected_dishes

    ingredient_count = db_session.scalar(select(func.count()).select_from(Ingredient))
    assert ingredient_count == ingredient_count_before


@pytest.mark.integration
def test_import_simple_dishes_fixture_uses_simple_meal_parts(db_session, catalog_seed):
    _seed_ingredients(db_session)
    expected_dishes = _expected_dish_count(SIMPLE_DISH_FIXTURE_PATH)

    result = import_dish_fixtures(db_session, SIMPLE_DISH_FIXTURE_PATH)

    assert result.dishes_added == expected_dishes
    assert result.ingredients_created == 0

    simple_counts = dict(
        db_session.execute(
            select(Dish.simple_dish_part, func.count())
            .where(Dish.meal_composition == MealComposition.simple_dish)
            .group_by(Dish.simple_dish_part)
        ).all()
    )
    assert simple_counts[SimpleDishPart.centerpiece] > 0
    assert simple_counts[SimpleDishPart.sidedish] > 0


@pytest.mark.integration
def test_import_dishes_rejects_non_canonical_recipe_ingredient(
    db_session,
    catalog_seed,
    tmp_path: Path,
):
    _seed_ingredients(db_session)
    fixture = tmp_path / "bad_dishes.yaml"
    fixture.write_text(
        """
version: 1
dishes:
  - name: Bad Fixture Dish
    course: main
    recipes:
      - variant_name: Standard
        difficulty: easy
        ingredients:
          - name: not a canonical ingredient
            quantity: 1
            unit: g
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-canonical ingredient"):
        import_dish_fixtures(db_session, fixture)


def test_load_fixture_rejects_invalid_file(tmp_path: Path):
    from mealroulette.data.import_dishes import load_fixture

    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("version: 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid fixture"):
        load_fixture(bad_file)
