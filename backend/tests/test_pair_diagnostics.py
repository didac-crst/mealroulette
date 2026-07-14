from decimal import Decimal

import pytest
from sqlalchemy import select

from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, Unit
from mealroulette.models.enums import DishCourse, DishStatus, RecipeType, SimpleDishPart
from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key
from mealroulette.services.recipe_traits import build_recipe_traits
from mealroulette.services.scheduler.catalog import load_reference_units
from mealroulette.services.scheduler.pair_diagnostics import (
    SimpleDishSemanticRole,
    build_recipe_pair_diagnostics,
    derive_primary_ingredients,
    derive_simple_dish_semantic_role,
)


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
    return ingredient


def _recipe(db_session, name: str) -> Recipe:
    dish = Dish(
        public_key=generate_dish_public_key(name),
        name=name,
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
    return recipe


@pytest.mark.unit
def test_derive_simple_dish_semantic_role_for_protein_centerpiece_traits():
    traits = {
        "food_group_weights": {"fish": 70.0, "vegetable": 20.0, "pantry": 10.0},
        "dominant_protein": "salmon_family",
        "total_trait_grams": 400.0,
    }
    role = derive_simple_dish_semantic_role(traits, simple_dish_part=SimpleDishPart.centerpiece)
    assert role == SimpleDishSemanticRole.protein_centerpiece


@pytest.mark.unit
def test_derive_simple_dish_semantic_roles_for_sides_and_centerpieces():
    fish_centerpiece = {
        "food_group_weights": {"fish": 70.0, "vegetable": 20.0},
        "dominant_protein": "salmon_family",
        "total_trait_grams": 400.0,
    }
    potato_side = {
        "food_group_weights": {"carbohydrate": 80.0, "dairy": 10.0},
        "dominant_carb": "potato_family",
        "carb_heavy": True,
        "total_trait_grams": 350.0,
    }
    legume_centerpiece = {
        "food_group_weights": {"legume": 55.0, "vegetable": 30.0},
        "dominant_protein": "legume_family",
        "total_trait_grams": 420.0,
    }

    assert derive_simple_dish_semantic_role(fish_centerpiece, simple_dish_part=SimpleDishPart.centerpiece) == (
        SimpleDishSemanticRole.protein_centerpiece
    )
    assert derive_simple_dish_semantic_role(potato_side, simple_dish_part=SimpleDishPart.sidedish) == (
        SimpleDishSemanticRole.carb_side
    )
    assert derive_simple_dish_semantic_role(legume_centerpiece, simple_dish_part=SimpleDishPart.centerpiece) == (
        SimpleDishSemanticRole.legume_centerpiece
    )
    assert derive_simple_dish_semantic_role(
        {"food_group_weights": {"vegetable": 90.0}, "total_trait_grams": 250.0},
        simple_dish_part=SimpleDishPart.sidedish,
        tag_names={"salad"},
    ) == SimpleDishSemanticRole.salad_side
    assert derive_simple_dish_semantic_role(
        {"food_group_weights": {"condiment": 100.0}, "total_trait_grams": 40.0},
        simple_dish_part=SimpleDishPart.sidedish,
    ) == SimpleDishSemanticRole.sauce_or_condiment


@pytest.mark.integration
def test_derive_primary_ingredients_from_recipe_lines(db_session, catalog_seed):
    gram_unit, ml_unit = load_reference_units(db_session)
    recipe = _recipe(db_session, "Primary Ingredient Bowl")
    rice = _add_line(
        db_session,
        recipe,
        canonical_name="diag_rice",
        category="grain",
        family="rice_family",
        food_group="carbohydrate",
        quantity=300,
    )
    chicken = _add_line(
        db_session,
        recipe,
        canonical_name="diag_chicken",
        category="meat",
        family="chicken_family",
        food_group="meat",
        quantity=200,
    )
    _add_line(
        db_session,
        recipe,
        canonical_name="diag_salt",
        category="pantry",
        family="salt",
        food_group="pantry",
        quantity=5,
        pantry_item=True,
    )
    db_session.refresh(recipe)

    primary = derive_primary_ingredients(recipe, gram_unit=gram_unit, ml_unit=ml_unit)
    names = {entry.canonical_name for entry in primary}
    families = {entry.family_key for entry in primary}

    assert names == {"diag_rice", "diag_chicken"}
    assert families == {"rice_family", "chicken_family"}
    assert primary[0].ingredient_id == rice.id
    assert primary[1].ingredient_id == chicken.id
    assert primary[0].share_pct == pytest.approx(59.41, rel=0.01)
    assert primary[1].share_pct == pytest.approx(39.60, rel=0.01)


@pytest.mark.integration
def test_derive_primary_ingredients_aggregates_duplicate_lines(db_session, catalog_seed):
    gram_unit, ml_unit = load_reference_units(db_session)
    recipe = _recipe(db_session, "Split Oil Dressing")
    oil = _add_line(
        db_session,
        recipe,
        canonical_name="diag_oil_split",
        category="pantry",
        family="olive_oil",
        food_group="pantry",
        quantity=120,
    )
    unit = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    db_session.add(
        RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=oil.id,
            quantity=Decimal("80"),
            unit_id=unit.id,
        )
    )
    db_session.flush()
    _add_line(
        db_session,
        recipe,
        canonical_name="diag_lettuce",
        category="vegetable",
        family="lettuce_family",
        food_group="vegetable",
        quantity=300,
    )
    db_session.refresh(recipe)

    primary = derive_primary_ingredients(recipe, gram_unit=gram_unit, ml_unit=ml_unit)
    oil_entry = next(entry for entry in primary if entry.ingredient_id == oil.id)

    assert len(primary) == 2
    assert oil_entry.grams == pytest.approx(200.0)
    assert oil_entry.share_pct == pytest.approx(40.0, rel=0.01)


@pytest.mark.integration
def test_derive_primary_ingredients_keeps_top_two_when_shares_are_balanced(db_session, catalog_seed):
    gram_unit, ml_unit = load_reference_units(db_session)
    recipe = _recipe(db_session, "Balanced Trio")
    first = _add_line(
        db_session,
        recipe,
        canonical_name="diag_a",
        category="vegetable",
        family="tomato_family",
        food_group="vegetable",
        quantity=110,
    )
    second = _add_line(
        db_session,
        recipe,
        canonical_name="diag_b",
        category="vegetable",
        family="cucumber_family",
        food_group="vegetable",
        quantity=100,
    )
    _add_line(
        db_session,
        recipe,
        canonical_name="diag_c",
        category="vegetable",
        family="pepper_family",
        food_group="vegetable",
        quantity=40,
    )
    db_session.refresh(recipe)

    primary = derive_primary_ingredients(recipe, gram_unit=gram_unit, ml_unit=ml_unit)
    assert len(primary) == 2
    assert {entry.ingredient_id for entry in primary} == {first.id, second.id}


@pytest.mark.integration
def test_build_recipe_pair_diagnostics_combines_traits_and_primary_ingredients(db_session, catalog_seed):
    gram_unit, ml_unit = load_reference_units(db_session)
    recipe = _recipe(db_session, "Pair Diagnostics Fish")
    _add_line(
        db_session,
        recipe,
        canonical_name="diag_sardines",
        category="fish",
        family="sardine_family",
        food_group="fish",
        quantity=250,
    )
    _add_line(
        db_session,
        recipe,
        canonical_name="diag_lemon",
        category="fruit",
        family="citrus_family",
        food_group="fruit",
        quantity=20,
    )
    db_session.refresh(recipe)
    traits = build_recipe_traits(recipe, gram_unit=gram_unit, ml_unit=ml_unit)

    diagnostics = build_recipe_pair_diagnostics(
        recipe,
        gram_unit=gram_unit,
        ml_unit=ml_unit,
        traits=traits,
        simple_dish_part=SimpleDishPart.centerpiece,
    )

    assert diagnostics.semantic_role == SimpleDishSemanticRole.protein_centerpiece
    assert diagnostics.primary_ingredient_ids
    assert "sardine_family" in diagnostics.primary_family_keys
    assert diagnostics.primary_ingredients[0].canonical_name == "diag_sardines"
