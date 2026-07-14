import random
from datetime import date, timedelta

import pytest

from mealroulette.models.catalog import Dish, Recipe
from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key
from mealroulette.models.enums import (
    MealComposition,
    MealPlanDishLineRole,
    MealPlanDishLineSource,
    SimpleDishPart,
)
from mealroulette.models.planning import MealPlanItem, MealPlanItemDish
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler.composition import assignment_from_main, assignment_from_pair

pytestmark = pytest.mark.unit


def _future_week_start(planning: PlanningService) -> date:
    reference = date.today()
    week_start = planning.week_start_for(reference)
    if week_start <= reference:
        week_start = week_start + timedelta(days=7)
    return week_start


def _make_dish(name: str, **kwargs) -> Dish:
    return Dish(name=name, public_key=generate_dish_public_key(name), **kwargs)


def _add_recipe(db_session, dish: Dish, *, variant: str = "default") -> Recipe:
    recipe = Recipe(
        dish_id=dish.id,
        variant_name=variant,
        is_main=True,
        public_key=generate_recipe_public_key(dish.public_key, 1),
        sequence_number=1,
    )
    db_session.add(recipe)
    db_session.flush()
    return recipe


def _apply_package(db_session, item: MealPlanItem, assignment) -> None:
    planning = PlanningService(db_session)
    planning.apply_roulette_package(item.id, assignment)


def test_swap_exchanges_composed_and_main_packages(db_session, catalog_seed):
    planning = PlanningService(db_session)
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)
    items = sorted(
        [item for item in plan.items if item.date >= week_start],
        key=lambda row: (row.date, row.meal_slot.value),
    )
    source = items[0]
    target = items[1]

    main_dish = _make_dish("Lasagna", meal_composition=MealComposition.main_dish)
    cp_dish = _make_dish(
        "Pasta",
        meal_composition=MealComposition.simple_dish,
        simple_dish_part=SimpleDishPart.centerpiece,
    )
    side_dish = _make_dish(
        "Salad",
        meal_composition=MealComposition.simple_dish,
        simple_dish_part=SimpleDishPart.sidedish,
    )
    db_session.add_all([main_dish, cp_dish, side_dish])
    db_session.flush()
    main_recipe = _add_recipe(db_session, main_dish)
    cp_recipe = _add_recipe(db_session, cp_dish)
    side_recipe = _add_recipe(db_session, side_dish)

    from mealroulette.models.enums import SeasonalityMode
    from mealroulette.services.scheduler.types import DishCandidate

    main_assignment = assignment_from_main(
        item_id=source.id,
        candidate=DishCandidate(
            dish_id=main_dish.id,
            dish_name=main_dish.name,
            recipe_id=main_recipe.id,
            meal_composition=MealComposition.main_dish,
            simple_dish_part=None,
            tag_names=frozenset(),
            protein_tags=frozenset(),
            carb_tags=frozenset(),
            style_tags=frozenset(),
            vector={},
            average_rating=None,
            seasonality_mode=SeasonalityMode.all_year,
            preferred_months=frozenset(),
            suitable_for_lunch=True,
            suitable_for_dinner=True,
        ),
        score=1.0,
        payload={"reasons": ["Main reason"], "score": 1.0},
    )
    pair_assignment = assignment_from_pair(
        item_id=target.id,
        centerpiece=DishCandidate(
            dish_id=cp_dish.id,
            dish_name=cp_dish.name,
            recipe_id=cp_recipe.id,
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.centerpiece,
            tag_names=frozenset(),
            protein_tags=frozenset(),
            carb_tags=frozenset(),
            style_tags=frozenset(),
            vector={},
            average_rating=None,
            seasonality_mode=SeasonalityMode.all_year,
            preferred_months=frozenset(),
            suitable_for_lunch=True,
            suitable_for_dinner=True,
        ),
        side=DishCandidate(
            dish_id=side_dish.id,
            dish_name=side_dish.name,
            recipe_id=side_recipe.id,
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.sidedish,
            tag_names=frozenset(),
            protein_tags=frozenset(),
            carb_tags=frozenset(),
            style_tags=frozenset(),
            vector={},
            average_rating=None,
            seasonality_mode=SeasonalityMode.all_year,
            preferred_months=frozenset(),
            suitable_for_lunch=True,
            suitable_for_dinner=True,
        ),
        score=2.0,
        payload={"reasons": ["Pair reason"], "score": 2.0},
    )
    _apply_package(db_session, source, main_assignment)
    _apply_package(db_session, target, pair_assignment)
    db_session.commit()

    swapped_source, swapped_target = planning.swap_items(source.id, target.id)

    assert swapped_source.title == "Pasta with Salad"
    assert swapped_target.title == "Lasagna"
    assert len(swapped_source.lines) == 2
    assert {line.role for line in swapped_source.lines} == {"centerpiece", "side"}
    assert len(swapped_target.lines) == 1
    assert swapped_target.lines[0].role == "main"


def test_swap_moves_manual_extras_with_package(db_session, catalog_seed):
    planning = PlanningService(db_session)
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)
    items = sorted(
        [item for item in plan.items if item.date >= week_start],
        key=lambda row: (row.date, row.meal_slot.value),
    )
    source = items[0]
    target = items[1]

    cp_dish = _make_dish("Steak", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.centerpiece)
    side_dish = _make_dish("Potatoes", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.sidedish)
    dessert = _make_dish("Ice cream", meal_composition=MealComposition.dessert)
    main_dish = _make_dish("Soup", meal_composition=MealComposition.main_dish)
    db_session.add_all([cp_dish, side_dish, dessert, main_dish])
    db_session.flush()
    cp_recipe = _add_recipe(db_session, cp_dish)
    side_recipe = _add_recipe(db_session, side_dish)
    dessert_recipe = _add_recipe(db_session, dessert)
    main_recipe = _add_recipe(db_session, main_dish)

    from mealroulette.models.enums import SeasonalityMode
    from mealroulette.services.scheduler.types import DishCandidate

    def _candidate(dish, recipe, *, part=None):
        return DishCandidate(
            dish_id=dish.id,
            dish_name=dish.name,
            recipe_id=recipe.id,
            meal_composition=dish.meal_composition,
            simple_dish_part=part,
            tag_names=frozenset(),
            protein_tags=frozenset(),
            carb_tags=frozenset(),
            style_tags=frozenset(),
            vector={},
            average_rating=None,
            seasonality_mode=SeasonalityMode.all_year,
            preferred_months=frozenset(),
            suitable_for_lunch=True,
            suitable_for_dinner=True,
        )

    pair_assignment = assignment_from_pair(
        item_id=source.id,
        centerpiece=_candidate(cp_dish, cp_recipe, part=SimpleDishPart.centerpiece),
        side=_candidate(side_dish, side_recipe, part=SimpleDishPart.sidedish),
        score=1.0,
        payload={"reasons": [], "score": 1.0},
    )
    _apply_package(db_session, source, pair_assignment)
    source_item = planning._load_item(source.id)
    source_item.lines.append(
        MealPlanItemDish(
            meal_plan_item_id=source_item.id,
            dish_id=dessert.id,
            recipe_id=dessert_recipe.id,
            position=2,
            role=MealPlanDishLineRole.dessert,
            source=MealPlanDishLineSource.manual,
        )
    )
    from mealroulette.services.meal_plan_lines import sync_legacy_mirror

    sync_legacy_mirror(source_item)

    main_assignment = assignment_from_main(
        item_id=target.id,
        candidate=_candidate(main_dish, main_recipe),
        score=1.0,
        payload={"reasons": [], "score": 1.0},
    )
    _apply_package(db_session, target, main_assignment)
    db_session.commit()

    swapped_source, swapped_target = planning.swap_items(source.id, target.id)

    assert swapped_source.title == "Soup"
    assert swapped_target.title == "Steak + Potatoes + Ice cream"
    assert any(line.role == "dessert" and line.source == "manual" for line in swapped_target.lines)


def test_swap_composed_to_composed_preserves_roles(db_session, catalog_seed):
    planning = PlanningService(db_session)
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)
    items = sorted(
        [item for item in plan.items if item.date >= week_start],
        key=lambda row: (row.date, row.meal_slot.value),
    )
    left = items[0]
    right = items[1]

    dishes = {
        "cp1": _make_dish("Fish", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.centerpiece),
        "side1": _make_dish("Rice", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.sidedish),
        "cp2": _make_dish("Chicken", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.centerpiece),
        "side2": _make_dish("Salad", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.sidedish),
    }
    db_session.add_all(dishes.values())
    db_session.flush()
    recipes = {key: _add_recipe(db_session, dish) for key, dish in dishes.items()}

    from mealroulette.models.enums import SeasonalityMode
    from mealroulette.services.scheduler.types import DishCandidate

    def _candidate(dish, recipe, part):
        return DishCandidate(
            dish_id=dish.id,
            dish_name=dish.name,
            recipe_id=recipe.id,
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=part,
            tag_names=frozenset(),
            protein_tags=frozenset(),
            carb_tags=frozenset(),
            style_tags=frozenset(),
            vector={},
            average_rating=None,
            seasonality_mode=SeasonalityMode.all_year,
            preferred_months=frozenset(),
            suitable_for_lunch=True,
            suitable_for_dinner=True,
        )

    left_assignment = assignment_from_pair(
        item_id=left.id,
        centerpiece=_candidate(dishes["cp1"], recipes["cp1"], SimpleDishPart.centerpiece),
        side=_candidate(dishes["side1"], recipes["side1"], SimpleDishPart.sidedish),
        score=1.0,
        payload={"reasons": ["Left"], "score": 1.0},
    )
    right_assignment = assignment_from_pair(
        item_id=right.id,
        centerpiece=_candidate(dishes["cp2"], recipes["cp2"], SimpleDishPart.centerpiece),
        side=_candidate(dishes["side2"], recipes["side2"], SimpleDishPart.sidedish),
        score=1.0,
        payload={"reasons": ["Right"], "score": 1.0},
    )
    _apply_package(db_session, left, left_assignment)
    _apply_package(db_session, right, right_assignment)
    db_session.commit()

    swapped_left, swapped_right = planning.swap_items(left.id, right.id)

    assert swapped_left.title == "Chicken with Salad"
    assert swapped_right.title == "Fish with Rice"
    assert swapped_left.lines[0].role == "centerpiece"
    assert swapped_left.lines[0].dish_name == "Chicken"
    assert swapped_right.lines[1].dish_name == "Rice"
