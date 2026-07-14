from decimal import Decimal

import pytest
from sqlalchemy import select

from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, Unit
from mealroulette.models.enums import DishCourse, DishStatus, RecipeType
from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key
from mealroulette.services.recipe_traits import build_recipe_traits
from mealroulette.services.scheduler.catalog import load_reference_units


def _add_line(db_session, recipe, *, canonical_name, category, family, food_group, quantity, pantry_item=False):
    unit = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    ingredient = Ingredient(
        canonical_name=canonical_name,
        display_name=canonical_name,
        category=category,
        food_group=food_group,
        family=family,
        pantry_item=pantry_item,
    )
    db_session.add(ingredient)
    db_session.flush()
    db_session.add(
        RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=Decimal(str(quantity)),
            unit_id=unit.id,
        )
    )


@pytest.mark.integration
def test_build_recipe_traits_meat_and_carb_heavy(db_session, catalog_seed):
    gram_unit, ml_unit = load_reference_units(db_session)
    dish = Dish(
        public_key=generate_dish_public_key("Trait Bowl"),
        name="Trait Bowl",
        course=DishCourse.main,
        status=DishStatus.active,
    )
    db_session.add(dish)
    db_session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        public_key=generate_recipe_public_key(dish.public_key, 1),
        sequence_number=1,
        variant_name="main",
        recipe_type=RecipeType.standard,
        is_main=True,
        computed_traits_json={},
    )
    db_session.add(recipe)
    db_session.flush()

    _add_line(
        db_session,
        recipe,
        canonical_name="trait_rice",
        category="grain",
        family="rice_family",
        food_group="carbohydrate",
        quantity=300,
    )
    _add_line(
        db_session,
        recipe,
        canonical_name="trait_chicken",
        category="meat",
        family="chicken_family",
        food_group="meat",
        quantity=200,
    )
    _add_line(
        db_session,
        recipe,
        canonical_name="trait_salt",
        category="pantry",
        family="salt",
        food_group="pantry",
        quantity=5,
        pantry_item=True,
    )
    db_session.refresh(recipe)
    traits = build_recipe_traits(recipe, gram_unit=gram_unit, ml_unit=ml_unit)

    assert traits["contains_meat"] is True
    assert traits["vegan"] is False
    assert traits["carb_heavy"] is True
    assert traits["dominant_carb"] == "rice_family"
    assert traits["dominant_protein"] == "chicken_family"
    assert "carbohydrate" in traits["contains_food_groups"]
    assert "meat" in traits["contains_food_groups"]
    assert traits["food_group_grams"]["carbohydrate"] == 300.0
    assert traits["food_group_grams"]["meat"] == 200.0
    assert traits["total_trait_grams"] >= 500.0


@pytest.mark.integration
def test_build_recipe_traits_vegan(db_session, catalog_seed):
    gram_unit, ml_unit = load_reference_units(db_session)
    dish = Dish(
        public_key=generate_dish_public_key("Vegan Bowl"),
        name="Vegan Bowl",
        course=DishCourse.main,
        status=DishStatus.active,
    )
    db_session.add(dish)
    db_session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        public_key=generate_recipe_public_key(dish.public_key, 1),
        sequence_number=1,
        variant_name="main",
        recipe_type=RecipeType.standard,
        is_main=True,
        computed_traits_json={},
    )
    db_session.add(recipe)
    db_session.flush()
    _add_line(
        db_session,
        recipe,
        canonical_name="trait_lentils",
        category="legume",
        family="legume_family",
        food_group="legume",
        quantity=250,
    )
    db_session.refresh(recipe)
    traits = build_recipe_traits(recipe, gram_unit=gram_unit, ml_unit=ml_unit)

    assert traits["vegan"] is True
    assert traits["contains_meat"] is False
    assert traits["dominant_protein"] == "legume_family"
