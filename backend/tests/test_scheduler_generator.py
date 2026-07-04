import random
from datetime import date

from mealroulette.models.enums import MealSlot, SeasonalityMode
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.scheduler.generator import generate_week_assignments
from mealroulette.services.scheduler.types import DishCandidate, GenerationSlot


def _candidate(dish_id: int, vector: dict[str, float]) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        dish_name=f"Dish {dish_id}",
        recipe_id=dish_id * 10,
        tag_names=frozenset(),
        protein_tags=frozenset(),
        carb_tags=frozenset(),
        style_tags=frozenset(),
        vector=vector,
        average_rating=None,
        seasonality_mode=SeasonalityMode.all_year,
        preferred_months=frozenset(),
        suitable_for_lunch=True,
        suitable_for_dinner=True,
    )


def _rules(**overrides) -> PlanningRulesConfig:
    defaults = {
        "weekly_targets": {},
        "weekly_target_tolerance": 1,
        "avoid_same_dish_within_days": 1,
        "avoid_similar_meals_within_days": 1,
        "similarity_threshold": 0.75,
        "prefer_seasonal": False,
        "prefer_high_rated": False,
        "plan_attempts": 10,
        "history_window_days": 14,
    }
    defaults.update(overrides)
    return PlanningRulesConfig(**defaults)


def test_generate_week_assigns_unique_dishes_per_slot():
    candidates = [
        _candidate(1, {"a": 1.0}),
        _candidate(2, {"b": 1.0}),
        _candidate(3, {"c": 1.0}),
    ]
    slots = [
        GenerationSlot(item_id=101, meal_date=date(2026, 7, 7), meal_slot=MealSlot.lunch),
        GenerationSlot(item_id=102, meal_date=date(2026, 7, 7), meal_slot=MealSlot.dinner),
        GenerationSlot(item_id=103, meal_date=date(2026, 7, 8), meal_slot=MealSlot.lunch),
    ]
    result = generate_week_assignments(
        slots,
        candidates,
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=_rules(),
        today=date(2026, 7, 1),
        rng=random.Random(0),
    )

    assert len(result.assignments) == 3
    assert len({assignment.dish_id for assignment in result.assignments}) == 3
    assert all(assignment.selection_reasons_json["score"] is not None for assignment in result.assignments)


def test_generate_week_respects_fixed_assignment_dish_ids():
    candidates = [
        _candidate(1, {"a": 1.0}),
        _candidate(2, {"b": 1.0}),
        _candidate(3, {"c": 1.0}),
    ]
    slots = [
        GenerationSlot(item_id=102, meal_date=date(2026, 7, 7), meal_slot=MealSlot.dinner),
        GenerationSlot(item_id=103, meal_date=date(2026, 7, 8), meal_slot=MealSlot.lunch),
    ]
    result = generate_week_assignments(
        slots,
        candidates,
        fixed_assignments={101: 1},
        fixed_dates_by_item={101: date(2026, 7, 7)},
        eaten_meals=[],
        rules=_rules(),
        today=date(2026, 7, 1),
        rng=random.Random(1),
    )

    assigned = {assignment.dish_id for assignment in result.assignments}
    assert 1 not in assigned


def test_generate_week_returns_warning_when_impossible():
    candidates = [_candidate(1, {"a": 1.0})]
    slots = [
        GenerationSlot(item_id=101, meal_date=date(2026, 7, 7), meal_slot=MealSlot.lunch),
        GenerationSlot(item_id=102, meal_date=date(2026, 7, 7), meal_slot=MealSlot.dinner),
    ]
    result = generate_week_assignments(
        slots,
        candidates,
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=_rules(plan_attempts=3),
        today=date(2026, 7, 1),
        rng=random.Random(2),
    )

    assert result.assignments == []
    assert result.warnings
