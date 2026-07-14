import random
from datetime import date, timedelta

import pytest

from mealroulette.models.enums import MealComposition, MealSlot, SimpleDishPart
from mealroulette.schemas.scheduler import ComposedMealsPerWeekSpec, PlanningRulesConfig, StructureNeutralShare
from mealroulette.services.scheduler.generator import generate_week_assignments
from mealroulette.services.scheduler.meal_structure import MealStructure, assignment_structure
from mealroulette.services.scheduler.types import DishCandidate, GenerationSlot

pytestmark = pytest.mark.unit


def _candidate(
    dish_id: int,
    vector: dict[str, float],
    *,
    meal_composition: MealComposition = MealComposition.main_dish,
    simple_dish_part: SimpleDishPart | None = None,
) -> DishCandidate:
    from mealroulette.models.enums import SeasonalityMode

    return DishCandidate(
        dish_id=dish_id,
        dish_name=f"Dish {dish_id}",
        recipe_id=dish_id * 10,
        meal_composition=meal_composition,
        simple_dish_part=simple_dish_part,
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


def _large_catalog_candidates() -> list[DishCandidate]:
    candidates = [_candidate(dish_id, {f"main-{dish_id % 20}": 1.0}) for dish_id in range(1, 32)]
    candidates.extend(
        _candidate(
            100 + dish_id,
            {f"cp-{dish_id % 25}": 1.0},
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.centerpiece,
        )
        for dish_id in range(94)
    )
    candidates.extend(
        _candidate(
            300 + dish_id,
            {f"side-{dish_id % 25}": 1.0},
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.sidedish,
        )
        for dish_id in range(88)
    )
    return candidates


def _week_slots() -> list[GenerationSlot]:
    return [
        GenerationSlot(
            item_id=1000 + index,
            meal_date=date(2026, 7, 7) + timedelta(days=index // 2),
            meal_slot=MealSlot.lunch if index % 2 == 0 else MealSlot.dinner,
        )
        for index in range(14)
    ]


def _structure_rules(**overrides) -> PlanningRulesConfig:
    defaults = {
        "weekly_targets": {},
        "weekly_target_tolerance": 1,
        "avoid_same_dish_within_days": 21,
        "avoid_similar_meals_within_days": 14,
        "similarity_threshold": 0.75,
        "prefer_seasonal": False,
        "prefer_high_rated": False,
        "plan_attempts": 30,
        "history_window_days": 14,
        "composed_meals_per_week": ComposedMealsPerWeekSpec(min=4, max=7),
        "structure_neutral_share": StructureNeutralShare(main=0.60, composed_pair=0.40),
    }
    defaults.update(overrides)
    return PlanningRulesConfig(**defaults)


def _structure_counts(assignments) -> tuple[int, int]:
    composed = 0
    mains = 0
    for assignment in assignments:
        if assignment_structure(assignment) == MealStructure.composed_pair:
            composed += 1
        else:
            mains += 1
    return composed, mains


def test_large_catalog_week_includes_both_structures():
    result = generate_week_assignments(
        _week_slots(),
        _large_catalog_candidates(),
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=_structure_rules(),
        today=date(2026, 7, 1),
        rng=random.Random(42),
    )

    composed, mains = _structure_counts(result.assignments)
    assert len(result.assignments) == 14
    assert mains > 0
    assert composed > 0
    assert 4 <= composed <= 7


def test_structure_policy_prefers_main_when_composed_max_reached():
    candidates = _large_catalog_candidates()
    slots = _week_slots()[:1]
    fixed_assignments = {1000 + index: 100 + index for index in range(7)}
    fixed_dates = {item_id: date(2026, 7, 6) + timedelta(days=index // 2) for index, item_id in enumerate(fixed_assignments)}

    result = generate_week_assignments(
        slots,
        candidates,
        fixed_assignments=fixed_assignments,
        fixed_dates_by_item=fixed_dates,
        eaten_meals=[],
        rules=_structure_rules(),
        today=date(2026, 7, 1),
        rng=random.Random(7),
    )

    assert len(result.assignments) == 1
    assert assignment_structure(result.assignments[0]) == MealStructure.main_dish


def test_reroll_prefers_mains_when_composed_max_reached():
    candidates = _large_catalog_candidates()
    slot = _week_slots()[0]
    rules = _structure_rules()
    outcomes: set[str] = set()
    fixed_assignments = {1000 + index: 100 + index for index in range(1, 8)}
    fixed_dates = {item_id: date(2026, 7, 6) for item_id in fixed_assignments}

    for seed in range(30):
        excluded: frozenset[tuple] = frozenset()
        for _ in range(10):
            result = generate_week_assignments(
                [slot],
                candidates,
                fixed_assignments=fixed_assignments,
                fixed_dates_by_item=fixed_dates,
                eaten_meals=[],
                rules=rules,
                today=date(2026, 7, 1),
                rng=random.Random(seed),
                forbidden_combination_keys=excluded,
            )
            if not result.assignments:
                break
            assignment = result.assignments[0]
            outcomes.add(assignment_structure(assignment).value)
            from mealroulette.services.scheduler.reroll_memory import combination_key_from_assignment

            excluded = excluded | {combination_key_from_assignment(assignment)}

    assert outcomes == {MealStructure.main_dish.value}


def test_reroll_can_pick_composed_when_week_below_min():
    candidates = _large_catalog_candidates()
    slot = _week_slots()[0]
    rules = _structure_rules()
    outcomes: set[str] = set()

    for seed in range(20):
        result = generate_week_assignments(
            [slot],
            candidates,
            fixed_assignments={},
            fixed_dates_by_item={},
            eaten_meals=[],
            rules=rules,
            today=date(2026, 7, 1),
            rng=random.Random(seed),
        )
        if result.assignments:
            outcomes.add(assignment_structure(result.assignments[0]).value)

    assert MealStructure.composed_pair.value in outcomes
