from datetime import date

import pytest

from mealroulette.models.enums import MealComposition, MealPlanItemStatus, MealPlanningState, MealSlot
from mealroulette.schemas.scheduler import PlanningRulesConfig, WeeklyTargetSpec
from mealroulette.services.scheduler.constraints import (
    build_dish_date_index,
    passes_same_dish_window,
    passes_slot_suitability,
    slot_is_regenerable,
)
from mealroulette.services.scheduler.neighbours import build_similarity_neighbours
from mealroulette.services.scheduler.scoring import neighbour_similarity_penalty, score_candidate_for_slot, temporal_weight
from mealroulette.services.scheduler.targets import (
    dish_matches_weekly_target,
    weekly_target_score_delta,
    weekly_target_warnings,
)
from mealroulette.services.scheduler.types import DishCandidate, GenerationSlot, MealNeighbourSnapshot
from mealroulette.services.scheduler.variety import build_variety_assessment
from mealroulette.models.enums import SeasonalityMode


def _candidate(
    dish_id: int,
    *,
    name: str = "Dish",
    vector: dict[str, float] | None = None,
    protein_tags: frozenset[str] | None = None,
    tag_names: frozenset[str] | None = None,
    computed_traits_json: dict | None = None,
    suitable_for_lunch: bool | None = True,
    suitable_for_dinner: bool | None = True,
) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        dish_name=name,
        recipe_id=dish_id * 10,
        meal_composition=MealComposition.main_dish,
        simple_dish_part=None,
        tag_names=tag_names or frozenset(),
        protein_tags=protein_tags or frozenset(),
        carb_tags=frozenset(),
        style_tags=frozenset(),
        vector=vector or {"vegetables": 0.5, "grains": 0.5},
        computed_traits_json=computed_traits_json,
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
    assert not slot_is_regenerable(
        meal_date=date(2026, 7, 2),
        today=today,
        is_locked=False,
        manually_selected=False,
        status=MealPlanItemStatus.planned,
        planning_state=MealPlanningState.do_not_plan,
    )


def test_passes_slot_suitability():
    lunch_only = _candidate(1, suitable_for_dinner=False)
    assert passes_slot_suitability(lunch_only, MealSlot.lunch)
    assert not passes_slot_suitability(lunch_only, MealSlot.dinner)


def test_same_dish_window_blocks_recent_repeat():
    rules = _rules(avoid_same_dish_within_days=7)
    candidate = _candidate(1)
    slot = GenerationSlot(item_id=10, meal_date=date(2026, 7, 10), meal_slot=MealSlot.dinner)
    dish_dates = build_dish_date_index([], [(1, date(2026, 7, 8))])
    assert not passes_same_dish_window(candidate, slot, dish_dates=dish_dates, rules=rules)


def test_temporal_weight_is_symmetric():
    assert temporal_weight(0, window_days=14) == pytest.approx(1.0)
    assert temporal_weight(7, window_days=14) == pytest.approx(0.5)
    assert temporal_weight(14, window_days=14) == pytest.approx(0.2)


def test_neighbour_penalty_higher_for_similar_meals():
    rules = _rules(similarity_threshold=0.75)
    candidate = _candidate(1, vector={"chicken": 1.0})
    slot = GenerationSlot(item_id=1, meal_date=date(2026, 7, 10), meal_slot=MealSlot.dinner)
    similar_meal = MealNeighbourSnapshot(
        dish_id=2,
        dish_name="Roast chicken",
        meal_date=date(2026, 7, 5),
        vector={"chicken": 1.0},
        source="eaten",
    )
    different_meal = MealNeighbourSnapshot(
        dish_id=3,
        dish_name="Lentil stew",
        meal_date=date(2026, 7, 5),
        vector={"legumes": 1.0},
        source="eaten",
    )

    similar_penalty, similar_reasons = neighbour_similarity_penalty(
        candidate, slot, neighbours=[similar_meal], rules=rules
    )
    different_penalty, _ = neighbour_similarity_penalty(
        candidate, slot, neighbours=[different_meal], rules=rules
    )

    assert similar_penalty > different_penalty
    assert any("Similar to Roast chicken" in reason for reason in similar_reasons)


def test_future_planned_neighbour_penalizes_closer_slots_more():
    rules = _rules(similarity_threshold=0.75, avoid_similar_meals_within_days=14)
    candidate = _candidate(1, vector={"pasta": 1.0})
    slot = GenerationSlot(item_id=10, meal_date=date(2026, 7, 10), meal_slot=MealSlot.lunch)
    close_neighbour = MealNeighbourSnapshot(
        dish_id=2,
        dish_name="Fixed risotto",
        meal_date=date(2026, 7, 11),
        vector={"pasta": 1.0},
        source="planned",
    )
    far_neighbour = MealNeighbourSnapshot(
        dish_id=3,
        dish_name="Fixed risotto",
        meal_date=date(2026, 7, 13),
        vector={"pasta": 1.0},
        source="planned",
    )

    close_penalty, _ = neighbour_similarity_penalty(candidate, slot, neighbours=[close_neighbour], rules=rules)
    far_penalty, _ = neighbour_similarity_penalty(candidate, slot, neighbours=[far_neighbour], rules=rules)

    assert close_penalty > far_penalty


def test_build_similarity_neighbours_includes_fixed_and_generated():
    eaten = [
        MealNeighbourSnapshot(
            dish_id=99,
            dish_name="Old pasta",
            meal_date=date(2026, 7, 1),
            vector={"pasta": 1.0},
            source="eaten",
        )
    ]
    fixed = {20: 2}
    fixed_dates = {20: date(2026, 7, 9)}
    attempt = []
    candidates = {
        2: _candidate(2, name="Locked fish", vector={"fish": 1.0}),
        3: _candidate(3, name="New veg", vector={"vegetables": 1.0}),
    }

    neighbours = build_similarity_neighbours(
        eaten_meals=eaten,
        fixed_assignments=fixed,
        fixed_dates_by_item=fixed_dates,
        attempt_assignments=attempt,
        slot_dates_by_item={**fixed_dates, 30: date(2026, 7, 10)},
        candidates_by_id=candidates,
    )

    assert len(neighbours) == 2
    assert {meal.source for meal in neighbours} == {"eaten", "planned"}


def test_weekly_target_matching_and_warnings():
    fish_dish = _candidate(1, tag_names=frozenset({"fish"}))
    meat_dish = _candidate(2, protein_tags=frozenset({"chicken"}))
    trait_fish = _candidate(
        3,
        computed_traits_json={"contains_food_groups": ["fish"], "contains_meat": False},
    )

    assert dish_matches_weekly_target(fish_dish, "fish")
    assert dish_matches_weekly_target(meat_dish, "meat")
    assert dish_matches_weekly_target(trait_fish, "fish")

    rules = _rules(weekly_targets={"fish": WeeklyTargetSpec(min=2, max=2)}, weekly_target_tolerance=0)
    warnings = weekly_target_warnings([1], candidates_by_id={1: fish_dish, 2: meat_dish}, rules=rules)
    assert any("below minimum" in warning for warning in warnings)


def test_score_candidate_prefers_different_neighbours():
    rules = _rules(similarity_threshold=0.75, prefer_seasonal=False, prefer_high_rated=False)
    slot = GenerationSlot(item_id=1, meal_date=date(2026, 7, 10), meal_slot=MealSlot.dinner)
    similar = _candidate(1, name="Similar", vector={"pasta": 1.0})
    different = _candidate(2, name="Different", vector={"fish": 1.0})
    neighbours = [
        MealNeighbourSnapshot(
            dish_id=99,
            dish_name="Recent pasta",
            meal_date=date(2026, 7, 5),
            vector={"pasta": 1.0},
            source="eaten",
        )
    ]

    similar_score, _ = score_candidate_for_slot(
        similar,
        slot,
        assigned_dish_ids=[],
        candidates_by_id={1: similar, 2: different},
        neighbours=neighbours,
        rules=rules,
    )
    different_score, _ = score_candidate_for_slot(
        different,
        slot,
        assigned_dish_ids=[],
        candidates_by_id={1: similar, 2: different},
        neighbours=neighbours,
        rules=rules,
    )

    assert different_score > similar_score


def test_variety_assessment_labels_distance():
    neighbours = [
        MealNeighbourSnapshot(
            dish_id=1,
            dish_name="Pasta",
            meal_date=date(2026, 6, 28),
            vector={"pasta": 1.0},
            source="eaten",
        )
    ]
    assessment = build_variety_assessment(
        new_assignments=[
            (10, 2, "Fish stew", {"fish": 1.0}),
            (11, 3, "More pasta", {"pasta": 1.0}),
        ],
        neighbours=neighbours,
    )

    by_name = {item["dish_name"]: item for item in assessment["items"]}
    assert by_name["Fish stew"]["variety_label"] == "very different"
    assert by_name["More pasta"]["variety_label"] == "very similar"
    assert assessment["average_distance_to_neighbours"] is not None


def test_same_dish_window_blocks_future_meals():
    rules = _rules(avoid_same_dish_within_days=7)
    slot = GenerationSlot(item_id=1, meal_date=date(2026, 7, 10), meal_slot=MealSlot.lunch)
    candidate = _candidate(5, name="Repeat")
    dish_dates = build_dish_date_index([], [(5, date(2026, 7, 11))])

    assert passes_same_dish_window(candidate, slot, dish_dates=dish_dates, rules=rules) is False


def test_weekly_target_score_uses_assigned_catalog():
    rules = _rules(weekly_targets={"fish": WeeklyTargetSpec(min=2, max=2)}, weekly_target_tolerance=0)
    fish = _candidate(1, name="Fish", protein_tags=frozenset({"fish"}))
    fish_two = _candidate(3, name="Another fish", protein_tags=frozenset({"fish"}))
    candidates_by_id = {1: fish, 3: fish_two}

    score_delta, reasons = weekly_target_score_delta(
        fish_two,
        assigned_dish_ids=[1],
        candidates_by_id=candidates_by_id,
        rules=rules,
    )

    assert score_delta > 0
    assert any("Helps fish target" in reason for reason in reasons)


def test_variety_assessment_excludes_current_assignment():
    neighbours = [
        MealNeighbourSnapshot(
            dish_id=3,
            dish_name="More pasta",
            meal_date=date(2026, 7, 9),
            vector={"pasta": 1.0},
            source="generated",
            item_id=11,
        ),
        MealNeighbourSnapshot(
            dish_id=1,
            dish_name="Fish stew",
            meal_date=date(2026, 6, 28),
            vector={"fish": 1.0},
            source="eaten",
        ),
    ]
    assessment = build_variety_assessment(
        new_assignments=[(11, 3, "More pasta", {"pasta": 1.0})],
        neighbours=neighbours,
    )

    item = assessment["items"][0]
    assert item["nearest_neighbour_dish"] == "Fish stew"
    assert item["variety_label"] == "very different"
