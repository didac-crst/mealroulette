from datetime import date

import pytest

from mealroulette.models.enums import MealSlot, SeasonalityMode
from mealroulette.schemas.scheduler import PlanningRulesConfig, WeeklyTargetSpec
from mealroulette.services.scheduler.constraints import (
    build_dish_date_index,
    passes_same_dish_window,
    passes_slot_suitability,
    slot_is_regenerable,
)
from mealroulette.models.enums import MealPlanItemStatus
from mealroulette.services.scheduler.scoring import history_similarity_penalty, score_candidate_for_slot
from mealroulette.services.scheduler.targets import dish_matches_weekly_target, weekly_target_warnings
from mealroulette.services.scheduler.types import DishCandidate, EatenMealSnapshot, GenerationSlot
from mealroulette.services.scheduler.variety import build_variety_assessment


def _candidate(
    dish_id: int,
    *,
    name: str = "Dish",
    vector: dict[str, float] | None = None,
    protein_tags: frozenset[str] | None = None,
    tag_names: frozenset[str] | None = None,
    suitable_for_lunch: bool | None = True,
    suitable_for_dinner: bool | None = True,
) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        dish_name=name,
        recipe_id=dish_id * 10,
        tag_names=tag_names or frozenset(),
        protein_tags=protein_tags or frozenset(),
        carb_tags=frozenset(),
        style_tags=frozenset(),
        vector=vector or {"vegetables": 0.5, "grains": 0.5},
        average_rating=None,
        seasonality_mode=SeasonalityMode.all_year,
        preferred_months=frozenset(),
        suitable_for_lunch=suitable_for_lunch,
        suitable_for_dinner=suitable_for_dinner,
    )


def _rules(**overrides) -> PlanningRulesConfig:
    base = {
        "weekly_targets": {"fish": WeeklyTargetSpec(min=0, max=5)},
        "weekly_target_tolerance": 1,
        "avoid_same_dish_within_days": 7,
        "avoid_similar_meals_within_days": 14,
        "similarity_threshold": 0.75,
        "prefer_seasonal": False,
        "prefer_high_rated": False,
        "plan_attempts": 5,
        "history_window_days": 14,
    }
    base.update(overrides)
    return PlanningRulesConfig(**base)


def test_slot_is_regenerable_respects_lock_and_past_dates():
    today = date(2026, 7, 1)
    assert slot_is_regenerable(
        meal_date=date(2026, 7, 2),
        today=today,
        is_locked=False,
        manually_selected=False,
        status=MealPlanItemStatus.planned,
    )
    assert not slot_is_regenerable(
        meal_date=date(2026, 6, 30),
        today=today,
        is_locked=False,
        manually_selected=False,
        status=MealPlanItemStatus.planned,
    )
    assert not slot_is_regenerable(
        meal_date=date(2026, 7, 2),
        today=today,
        is_locked=True,
        manually_selected=False,
        status=MealPlanItemStatus.planned,
    )


def test_passes_slot_suitability():
    lunch_only = _candidate(1, suitable_for_dinner=False)
    assert passes_slot_suitability(lunch_only, MealSlot.lunch)
    assert not passes_slot_suitability(lunch_only, MealSlot.dinner)


def test_same_dish_window_blocks_recent_repeat():
    rules = _rules(avoid_same_dish_within_days=7)
    candidate = _candidate(1)
    slot = GenerationSlot(item_id=10, meal_date=date(2026, 7, 10), meal_slot=MealSlot.dinner)
    dish_dates = build_dish_date_index(
        [],
        [(1, date(2026, 7, 8))],
    )
    assert not passes_same_dish_window(candidate, slot, dish_dates=dish_dates, rules=rules)


def test_history_penalty_higher_for_similar_meals():
    rules = _rules(similarity_threshold=0.75)
    candidate = _candidate(1, vector={"chicken": 1.0})
    slot = GenerationSlot(item_id=1, meal_date=date(2026, 7, 10), meal_slot=MealSlot.dinner)
    similar_meal = EatenMealSnapshot(
        dish_id=2,
        dish_name="Roast chicken",
        meal_date=date(2026, 7, 5),
        vector={"chicken": 1.0},
    )
    different_meal = EatenMealSnapshot(
        dish_id=3,
        dish_name="Lentil stew",
        meal_date=date(2026, 7, 5),
        vector={"legumes": 1.0},
    )

    similar_penalty, similar_reasons = history_similarity_penalty(
        candidate, slot, eaten_meals=[similar_meal], rules=rules
    )
    different_penalty, _ = history_similarity_penalty(
        candidate, slot, eaten_meals=[different_meal], rules=rules
    )

    assert similar_penalty > different_penalty
    assert any("Similar to Roast chicken" in reason for reason in similar_reasons)


def test_weekly_target_matching_and_warnings():
    fish_dish = _candidate(1, tag_names=frozenset({"fish"}))
    meat_dish = _candidate(2, protein_tags=frozenset({"chicken"}))

    assert dish_matches_weekly_target(fish_dish, "fish")
    assert dish_matches_weekly_target(meat_dish, "meat")

    rules = _rules(weekly_targets={"fish": WeeklyTargetSpec(min=2, max=2)}, weekly_target_tolerance=0)
    warnings = weekly_target_warnings([1], candidates_by_id={1: fish_dish, 2: meat_dish}, rules=rules)
    assert any("below minimum" in warning for warning in warnings)


def test_score_candidate_prefers_different_history():
    rules = _rules(similarity_threshold=0.75, prefer_seasonal=False, prefer_high_rated=False)
    slot = GenerationSlot(item_id=1, meal_date=date(2026, 7, 10), meal_slot=MealSlot.dinner)
    similar = _candidate(1, name="Similar", vector={"pasta": 1.0})
    different = _candidate(2, name="Different", vector={"fish": 1.0})
    eaten = [
        EatenMealSnapshot(
            dish_id=99,
            dish_name="Recent pasta",
            meal_date=date(2026, 7, 5),
            vector={"pasta": 1.0},
        )
    ]

    similar_score, _ = score_candidate_for_slot(
        similar, slot, assigned_dish_ids=[], eaten_meals=eaten, rules=rules
    )
    different_score, _ = score_candidate_for_slot(
        different, slot, assigned_dish_ids=[], eaten_meals=eaten, rules=rules
    )

    assert different_score > similar_score


def test_variety_assessment_labels_distance():
    recent = EatenMealSnapshot(
        dish_id=1,
        dish_name="Pasta",
        meal_date=date(2026, 6, 28),
        vector={"pasta": 1.0},
    )
    assessment = build_variety_assessment(
        new_assignments=[
            (2, "Fish stew", {"fish": 1.0}),
            (3, "More pasta", {"pasta": 1.0}),
        ],
        recent_meals=[recent],
    )

    by_name = {item["dish_name"]: item for item in assessment["items"]}
    assert by_name["Fish stew"]["variety_label"] == "very different"
    assert by_name["More pasta"]["variety_label"] == "very similar"
    assert assessment["average_distance_to_recent"] is not None
