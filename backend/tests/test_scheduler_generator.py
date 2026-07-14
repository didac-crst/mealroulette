import random
from datetime import date, timedelta

import pytest

from mealroulette.models.enums import MealComposition, MealSlot, SeasonalityMode, SimpleDishPart
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.scheduler import generator as generator_module
from mealroulette.services.scheduler.generator import (
    MAX_PAIR_CENTERPIECES,
    MAX_PAIR_SIDES,
    _ScoredCandidate,
    _build_slot_options,
    _diverse_shortlist,
    _effective_plan_attempts,
    _partition_candidates,
    generate_week_assignments,
)
from mealroulette.services.scheduler.pair_diagnostics import CandidatePairSummary, SimpleDishSemanticRole
from mealroulette.services.scheduler.types import DishCandidate, GenerationSlot

pytestmark = pytest.mark.unit


def _candidate(
    dish_id: int,
    vector: dict[str, float],
    *,
    meal_composition: MealComposition = MealComposition.main_dish,
    simple_dish_part: SimpleDishPart | None = None,
    computed_traits_json: dict | None = None,
    pair_summary: CandidatePairSummary | None = None,
) -> DishCandidate:
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
        computed_traits_json=computed_traits_json,
        pair_summary=pair_summary,
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


def test_generate_week_can_assign_centerpiece_side_pair():
    candidates = [
        _candidate(1, {"a": 1.0}, meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.centerpiece),
        _candidate(2, {"b": 1.0}, meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.sidedish),
    ]
    slots = [
        GenerationSlot(item_id=101, meal_date=date(2026, 7, 7), meal_slot=MealSlot.lunch),
    ]
    result = generate_week_assignments(
        slots,
        candidates,
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=_rules(plan_attempts=5),
        today=date(2026, 7, 1),
        rng=random.Random(3),
    )

    assert len(result.assignments) == 1
    assignment = result.assignments[0]
    assert len(assignment.lines) == 2
    roles = {line.role.value for line in assignment.lines}
    assert roles == {"centerpiece", "side"}


def test_build_slot_options_skips_hard_rejected_centerpiece_side_pairs():
    fish_traits = {
        "food_group_weights": {"fish": 70.0, "vegetable": 30.0},
        "dominant_protein": "sardine_family",
        "total_trait_grams": 400.0,
    }
    potato_traits = {
        "food_group_weights": {"carbohydrate": 75.0, "vegetable": 25.0},
        "dominant_carb": "potato_family",
        "total_trait_grams": 320.0,
    }
    centerpieces = [
        _candidate(
            1,
            {"fish": 1.0},
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.centerpiece,
            computed_traits_json=fish_traits,
            pair_summary=CandidatePairSummary(
                primary_ingredient_ids=frozenset(),
                primary_family_keys=frozenset({"sardine_family"}),
                semantic_role=SimpleDishSemanticRole.protein_centerpiece,
            ),
        )
    ]
    sides = [
        _candidate(
            2,
            {"fish-side": 1.0},
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.sidedish,
            computed_traits_json={
                "food_group_weights": {"fish": 35.0, "vegetable": 65.0},
                "dominant_protein": "tuna_family",
                "total_trait_grams": 250.0,
            },
            pair_summary=CandidatePairSummary(
                primary_ingredient_ids=frozenset(),
                primary_family_keys=frozenset({"tuna_family"}),
                semantic_role=SimpleDishSemanticRole.protein_side,
            ),
        ),
        _candidate(
            3,
            {"potato": 1.0},
            meal_composition=MealComposition.simple_dish,
            simple_dish_part=SimpleDishPart.sidedish,
            computed_traits_json=potato_traits,
            pair_summary=CandidatePairSummary(
                primary_ingredient_ids=frozenset(),
                primary_family_keys=frozenset({"potato_family"}),
                semantic_role=SimpleDishSemanticRole.carb_side,
            ),
        ),
    ]
    slot = GenerationSlot(item_id=101, meal_date=date(2026, 7, 7), meal_slot=MealSlot.lunch)
    options = _build_slot_options(
        slot,
        mains=[],
        centerpieces=centerpieces,
        sides=sides,
        assigned_dish_ids=[],
        forbidden_dish_ids=None,
        dish_date_index={},
        neighbours=[],
        candidates_by_id={candidate.dish_id: candidate for candidate in centerpieces + sides},
        rules=_rules(),
        rng=random.Random(0),
    )

    pair_dish_ids = {
        tuple(sorted(line.dish_id for line in option.assignment.lines))
        for option in options
        if len(option.assignment.lines) == 2
    }
    assert pair_dish_ids == {(1, 3)}


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


def _production_like_rules(**overrides) -> PlanningRulesConfig:
    defaults = {
        "weekly_targets": {
            "fish": {"min": 1, "max": 2},
            "meat": {"min": 2, "max": 4},
            "vegetarian": {"min": 2, "max": 5},
            "pasta": {"min": 1, "max": 3},
            "rice": {"min": 1, "max": 3},
            "soup": {"min": 0, "max": 3},
        },
        "weekly_target_tolerance": 1,
        "avoid_same_dish_within_days": 21,
        "avoid_similar_meals_within_days": 14,
        "similarity_threshold": 0.75,
        "prefer_seasonal": True,
        "prefer_high_rated": True,
        "allow_leftovers": True,
        "default_grams_per_count": 100,
        "vector_min_grams": 5,
        "plan_attempts": 50,
        "history_window_days": 14,
    }
    defaults.update(overrides)
    return PlanningRulesConfig(**defaults)


def _week_slots() -> list[GenerationSlot]:
    return [
        GenerationSlot(
            item_id=1000 + index,
            meal_date=date(2026, 7, 7) + timedelta(days=index // 2),
            meal_slot=MealSlot.lunch if index % 2 == 0 else MealSlot.dinner,
        )
        for index in range(14)
    ]


def test_diverse_shortlist_includes_random_non_top_candidates():
    guaranteed_top = 8
    random_pick = 7
    scored = [
        _ScoredCandidate(_candidate(index, {f"k{index}": 1.0}), float(index), {})
        for index in range(30)
    ]
    guaranteed_top_ids = {index for index in range(30 - guaranteed_top, 30)}
    non_top_ids = {index for index in range(0, 30 - guaranteed_top)}

    observed_non_top_ids: set[int] = set()
    for seed in range(100):
        shortlist = _diverse_shortlist(
            scored,
            max_count=15,
            guaranteed_top=guaranteed_top,
            random_pick=random_pick,
            rng=random.Random(seed),
        )
        shortlisted_ids = {entry.candidate.dish_id for entry in shortlist}

        assert len(shortlist) == 15
        assert guaranteed_top_ids.issubset(shortlisted_ids)
        observed_non_top_ids.update(shortlisted_ids & non_top_ids)

    assert observed_non_top_ids


def test_effective_plan_attempts_scales_down_for_large_simple_dish_catalog():
    rules = _production_like_rules(plan_attempts=50)
    candidates = _large_catalog_candidates()

    assert _effective_plan_attempts(rules, candidates) == 25


def test_generate_week_is_deterministic_with_seed():
    candidates = _large_catalog_candidates()
    slots = _week_slots()
    rules = _production_like_rules()
    kwargs = dict(
        slots=slots,
        candidates=candidates,
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=rules,
        today=date(2026, 7, 1),
    )

    first = generate_week_assignments(**kwargs, rng=random.Random(42))
    second = generate_week_assignments(**kwargs, rng=random.Random(42))

    assert [(assignment.item_id, assignment.dish_id, tuple(line.dish_id for line in assignment.lines)) for assignment in first.assignments] == [
        (assignment.item_id, assignment.dish_id, tuple(line.dish_id for line in assignment.lines)) for assignment in second.assignments
    ]


def test_diverse_shortlist_admits_low_ranked_simple_dish():
    scored = [
        _ScoredCandidate(_candidate(index, {f"k{index}": 1.0}), float(index), {})
        for index in range(40)
    ] + [_ScoredCandidate(_candidate(999, {"low": 0.01}), -100.0, {})]

    shortlisted_ids: set[int] = set()
    for seed in range(100):
        shortlist = _diverse_shortlist(
            scored,
            max_count=25,
            guaranteed_top=12,
            random_pick=13,
            rng=random.Random(seed),
        )
        shortlisted_ids.update(entry.candidate.dish_id for entry in shortlist)

    assert 999 in shortlisted_ids


def test_generate_week_varies_across_seeds():
    candidates = _large_catalog_candidates()
    slots = _week_slots()[:4]
    rules = _production_like_rules(plan_attempts=10)
    kwargs = dict(
        slots=slots,
        candidates=candidates,
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=rules,
        today=date(2026, 7, 1),
    )

    signatures: set[tuple[tuple[int, int | None, tuple[int, ...]], ...]] = set()
    for seed in range(12):
        result = generate_week_assignments(**kwargs, rng=random.Random(seed))
        signatures.add(
            tuple(
                (assignment.item_id, assignment.dish_id, tuple(line.dish_id for line in assignment.lines))
                for assignment in result.assignments
            )
        )

    assert len(signatures) > 1


def test_generate_week_explores_beyond_guaranteed_top_candidates():
    candidates = _large_catalog_candidates()
    slots = _week_slots()[:6]
    rules = _production_like_rules(plan_attempts=10)

    observed_dish_ids: set[int] = set()
    for seed in range(10):
        result = generate_week_assignments(
            slots,
            candidates,
            fixed_assignments={},
            fixed_dates_by_item={},
            eaten_meals=[],
            rules=rules,
            today=date(2026, 7, 1),
            rng=random.Random(seed),
        )
        for assignment in result.assignments:
            if assignment.dish_id is not None:
                observed_dish_ids.add(assignment.dish_id)
            for line in assignment.lines:
                observed_dish_ids.add(line.dish_id)

    assert len(observed_dish_ids) > 15


def test_build_slot_options_caps_pair_exploration_for_large_catalog():
    candidates = _large_catalog_candidates()
    slot = _week_slots()[0]
    candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
    partitions = _partition_candidates(candidates)

    options = _build_slot_options(
        slot,
        mains=partitions.mains,
        centerpieces=partitions.centerpieces,
        sides=partitions.sides,
        assigned_dish_ids=[],
        forbidden_dish_ids=None,
        dish_date_index={},
        neighbours=[],
        candidates_by_id=candidates_by_id,
        rules=_production_like_rules(),
        rng=random.Random(0),
    )

    pair_options = [option for option in options if len(option.assigned_dish_ids) == 2]
    assert len(pair_options) <= MAX_PAIR_CENTERPIECES * MAX_PAIR_SIDES


def test_build_slot_options_scores_each_eligible_candidate_once_per_slot(monkeypatch):
    score_calls: dict[int, int] = {}
    original = generator_module.score_candidate_for_slot

    def counting(candidate, *args, **kwargs):
        score_calls[candidate.dish_id] = score_calls.get(candidate.dish_id, 0) + 1
        return original(candidate, *args, **kwargs)

    monkeypatch.setattr(generator_module, "score_candidate_for_slot", counting)

    candidates = _large_catalog_candidates()
    slot = _week_slots()[0]
    candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
    partitions = _partition_candidates(candidates)

    _build_slot_options(
        slot,
        mains=partitions.mains,
        centerpieces=partitions.centerpieces,
        sides=partitions.sides,
        assigned_dish_ids=[],
        forbidden_dish_ids=None,
        dish_date_index={},
        neighbours=[],
        candidates_by_id=candidates_by_id,
        rules=_production_like_rules(),
        rng=random.Random(0),
    )

    assert score_calls
    assert all(count == 1 for count in score_calls.values())


def test_large_catalog_uses_bounded_plan_attempts_and_generates_full_week():
    candidates = _large_catalog_candidates()
    slots = _week_slots()
    rules = _production_like_rules()

    assert _effective_plan_attempts(rules, candidates) == 25

    result = generate_week_assignments(
        slots,
        candidates,
        fixed_assignments={},
        fixed_dates_by_item={},
        eaten_meals=[],
        rules=rules,
        today=date(2026, 7, 1),
        rng=random.Random(7),
    )

    assert len(result.assignments) == 14
