import random

import pytest

from mealroulette.models.enums import MealComposition, SimpleDishPart, SeasonalityMode
from mealroulette.schemas.scheduler import ComposedMealsPerWeekSpec, PlanningRulesConfig, StructureNeutralShare
from mealroulette.services.scheduler.composition import assignment_from_main, assignment_from_pair
from mealroulette.services.scheduler.meal_structure import (
    MealStructure,
    assignment_structure,
    count_week_structures,
    select_preferred_structure,
)
from mealroulette.services.scheduler.types import DishCandidate

pytestmark = pytest.mark.unit


def _candidate(
    dish_id: int,
    *,
    main: bool = True,
    part: SimpleDishPart | None = None,
) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        dish_name=f"Dish {dish_id}",
        recipe_id=dish_id * 10,
        meal_composition=MealComposition.main_dish if main else MealComposition.simple_dish,
        simple_dish_part=part if not main else None,
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


def _rules(**overrides) -> PlanningRulesConfig:
    defaults = {
        "weekly_targets": {},
        "composed_meals_per_week": ComposedMealsPerWeekSpec(min=4, max=7),
        "structure_neutral_share": StructureNeutralShare(main=0.60, composed_pair=0.40),
    }
    defaults.update(overrides)
    return PlanningRulesConfig(**defaults)


def test_assignment_structure_main_and_pair():
    main_assignment = assignment_from_main(
        item_id=1,
        candidate=_candidate(1),
        score=1.0,
        payload={"reasons": []},
    )
    pair_assignment = assignment_from_pair(
        item_id=2,
        centerpiece=_candidate(10, main=False, part=SimpleDishPart.centerpiece),
        side=_candidate(20, main=False, part=SimpleDishPart.sidedish),
        score=2.0,
        payload={"reasons": []},
    )
    assert assignment_structure(main_assignment) == MealStructure.main_dish
    assert assignment_structure(pair_assignment) == MealStructure.composed_pair


def test_count_week_structures_includes_fixed_and_attempt():
    candidates_by_id = {
        1: _candidate(1, main=True),
        10: _candidate(10, main=False, part=SimpleDishPart.centerpiece),
    }
    attempt = [
        assignment_from_main(item_id=1, candidate=_candidate(1), score=1.0, payload={"reasons": []}),
    ]
    composed, mains = count_week_structures(
        fixed_assignments={99: 10},
        attempt_assignments=attempt,
        candidates_by_id=candidates_by_id,
    )
    assert composed == 1
    assert mains == 1


def test_select_preferred_structure_below_min_prefers_composed():
    structure, reasons, codes = select_preferred_structure(
        2,
        rules=_rules(),
        rng=random.Random(0),
    )
    assert structure == MealStructure.composed_pair
    assert reasons
    assert "structure_target_composed_pair" in codes


def test_select_preferred_structure_at_max_prefers_main():
    structure, reasons, codes = select_preferred_structure(
        7,
        rules=_rules(),
        rng=random.Random(0),
    )
    assert structure == MealStructure.main_dish
    assert "structure_target_main" in codes


def test_select_preferred_structure_in_range_uses_neutral_share():
    composed_picks = 0
    for seed in range(200):
        structure, _, _ = select_preferred_structure(
            5,
            rules=_rules(),
            rng=random.Random(seed),
        )
        if structure == MealStructure.composed_pair:
            composed_picks += 1
    assert 20 < composed_picks < 180
