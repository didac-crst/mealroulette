from datetime import date

import pytest

from mealroulette.models.enums import MealComposition, MealPlanDishLineRole, SeasonalityMode, SimpleDishPart
from mealroulette.services.scheduler.composition import (
    aggregate_meal_vector,
    assignment_from_pair,
    assignment_meal_label,
    assignment_meal_vector,
)
from mealroulette.services.scheduler.neighbours import build_similarity_neighbours
from mealroulette.services.scheduler.types import DishCandidate
from mealroulette.services.scheduler.variety import build_variety_assessment

pytestmark = pytest.mark.unit


def _candidate(
    dish_id: int,
    name: str,
    vector: dict[str, float],
    *,
    grams: float = 100.0,
    part: SimpleDishPart | None = None,
) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        dish_name=name,
        recipe_id=dish_id * 10,
        meal_composition=MealComposition.simple_dish if part else MealComposition.main_dish,
        simple_dish_part=part,
        tag_names=frozenset(),
        protein_tags=frozenset(),
        carb_tags=frozenset(),
        style_tags=frozenset(),
        vector=vector,
        computed_traits_json={"total_trait_grams": grams},
        average_rating=None,
        seasonality_mode=SeasonalityMode.all_year,
        preferred_months=frozenset(),
        suitable_for_lunch=True,
        suitable_for_dinner=True,
    )


def test_aggregate_meal_vector_blends_centerpiece_and_side():
    centerpiece = _candidate(1, "Fish", {"fish": 1.0}, grams=300, part=SimpleDishPart.centerpiece)
    side = _candidate(2, "Potatoes", {"potato": 1.0}, grams=200, part=SimpleDishPart.sidedish)

    vector = aggregate_meal_vector([centerpiece, side])

    assert vector["fish"] == pytest.approx(0.6)
    assert vector["potato"] == pytest.approx(0.4)


def test_variety_assessment_uses_full_meal_label_and_vector():
    centerpiece = _candidate(10, "Zucchini Omelette", {"egg": 0.7, "vegetable": 0.3}, part=SimpleDishPart.centerpiece)
    side = _candidate(11, "Mushroom Rice", {"rice": 0.8, "vegetable": 0.2}, part=SimpleDishPart.sidedish)
    main = _candidate(20, "Fideua", {"pasta": 1.0})
    candidates_by_id = {10: centerpiece, 11: side, 20: main}

    assignment = assignment_from_pair(
        item_id=101,
        centerpiece=centerpiece,
        side=side,
        score=1.0,
        payload={"reasons": []},
    )
    neighbours = build_similarity_neighbours(
        eaten_meals=[],
        fixed_assignments={102: 20},
        fixed_dates_by_item={102: date(2026, 7, 15)},
        attempt_assignments=[assignment],
        slot_dates_by_item={101: date(2026, 7, 16), 102: date(2026, 7, 15)},
        candidates_by_id=candidates_by_id,
    )

    assessment = build_variety_assessment(
        new_assignments=[
            (
                101,
                assignment.dish_id,
                assignment_meal_label(assignment, candidates_by_id),
                assignment_meal_vector(assignment, candidates_by_id),
            )
        ],
        neighbours=neighbours,
    )

    item = assessment["items"][0]
    assert item["dish_name"] == "Zucchini Omelette with Mushroom Rice"
    assert item["nearest_neighbour_dish"] == "Fideua"
