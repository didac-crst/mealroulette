import pytest

from mealroulette.models.enums import MealComposition, SeasonalityMode, SimpleDishPart
from mealroulette.services.scheduler.pair_diagnostics import CandidatePairSummary, SimpleDishSemanticRole
from mealroulette.services.scheduler.pair_scoring import score_pair_compatibility
from mealroulette.services.scheduler.types import DishCandidate

pytestmark = pytest.mark.unit


def _candidate(
    dish_id: int,
    *,
    simple_dish_part: SimpleDishPart,
    traits: dict | None = None,
    pair_summary: CandidatePairSummary | None = None,
    tag_names: frozenset[str] | None = None,
) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        dish_name=f"Dish {dish_id}",
        recipe_id=dish_id * 10,
        meal_composition=MealComposition.simple_dish,
        simple_dish_part=simple_dish_part,
        tag_names=tag_names or frozenset(),
        protein_tags=frozenset(),
        carb_tags=frozenset(),
        style_tags=frozenset(),
        vector={"x": 1.0},
        computed_traits_json=traits,
        pair_summary=pair_summary,
        average_rating=None,
        seasonality_mode=SeasonalityMode.all_year,
        preferred_months=frozenset(),
        suitable_for_lunch=True,
        suitable_for_dinner=True,
    )


def _summary(*, role: SimpleDishSemanticRole) -> CandidatePairSummary:
    return CandidatePairSummary(
        primary_ingredient_ids=frozenset(),
        primary_family_keys=frozenset(),
        semantic_role=role,
    )


def _traits_with_grams(weights: dict[str, float], *, total: float = 400.0) -> dict:
    grams = {group: (share / 100.0) * total for group, share in weights.items()}
    return {
        "food_group_weights": weights,
        "food_group_grams": grams,
        "total_trait_grams": total,
    }


def test_sardines_with_salad_or_potatoes_score_positively():
    sardines = _candidate(
        1,
        simple_dish_part=SimpleDishPart.centerpiece,
        traits=_traits_with_grams({"fish": 70.0, "vegetable": 30.0}, total=400.0)
        | {"dominant_protein": "sardine_family"},
        pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
    )
    salad = _candidate(
        2,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"vegetable": 85.0, "pantry": 15.0}, total=250.0),
        pair_summary=_summary(role=SimpleDishSemanticRole.salad_side),
        tag_names=frozenset({"salad"}),
    )
    potatoes = _candidate(
        3,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"carbohydrate": 75.0, "vegetable": 25.0}, total=320.0)
        | {"dominant_carb": "potato_family"},
        pair_summary=_summary(role=SimpleDishSemanticRole.carb_side),
    )

    salad_score = score_pair_compatibility(sardines, salad)
    potato_score = score_pair_compatibility(sardines, potatoes)

    assert salad_score.adjustment > 0
    assert potato_score.adjustment > 0
    assert "positive_complementarity" in salad_score.reason_codes
    assert "positive_complementarity" in potato_score.reason_codes
    assert "Adds a vegetable side" in salad_score.reasons
    assert "Balances a fish centerpiece with a carb side" in potato_score.reasons


def test_omelette_with_bread_scores_higher_than_with_eggplant():
    omelette = _candidate(
        4,
        simple_dish_part=SimpleDishPart.centerpiece,
        traits=_traits_with_grams({"egg": 55.0, "vegetable": 45.0}, total=350.0)
        | {"dominant_protein": "egg_family"},
        pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
    )
    eggplant = _candidate(
        5,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"vegetable": 85.0, "pantry": 15.0}, total=280.0),
        pair_summary=_summary(role=SimpleDishSemanticRole.vegetable_side),
    )
    bread = _candidate(
        6,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"carbohydrate": 80.0, "pantry": 20.0}, total=200.0)
        | {"dominant_carb": "bread_family"},
        pair_summary=_summary(role=SimpleDishSemanticRole.bread_side),
    )

    eggplant_score = score_pair_compatibility(omelette, eggplant)
    bread_score = score_pair_compatibility(omelette, bread)

    assert bread_score.adjustment > eggplant_score.adjustment


def test_combined_meal_can_earn_whole_meal_balance_reason():
    sardines = _candidate(
        7,
        simple_dish_part=SimpleDishPart.centerpiece,
        traits=_traits_with_grams({"fish": 60.0, "vegetable": 40.0}, total=400.0),
        pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
    )
    potatoes = _candidate(
        8,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"carbohydrate": 70.0, "vegetable": 30.0}, total=300.0),
        pair_summary=_summary(role=SimpleDishSemanticRole.carb_side),
    )

    result = score_pair_compatibility(sardines, potatoes)
    assert "whole_meal_balance" in result.reason_codes
    assert any("protein" in reason.lower() or "food group" in reason.lower() for reason in result.reasons)


def test_carb_centerpiece_with_carb_side_is_penalized():
    pasta = _candidate(
        9,
        simple_dish_part=SimpleDishPart.centerpiece,
        traits=_traits_with_grams({"carbohydrate": 70.0, "vegetable": 30.0}, total=450.0)
        | {"carb_heavy": True, "dominant_carb": "pasta_family"},
        pair_summary=_summary(role=SimpleDishSemanticRole.carb_centerpiece),
    )
    rice = _candidate(
        10,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"carbohydrate": 80.0, "vegetable": 20.0}, total=300.0)
        | {"carb_heavy": True, "dominant_carb": "rice_family"},
        pair_summary=_summary(role=SimpleDishSemanticRole.carb_side),
    )
    salad = _candidate(
        11,
        simple_dish_part=SimpleDishPart.sidedish,
        traits=_traits_with_grams({"vegetable": 90.0, "pantry": 10.0}, total=220.0),
        pair_summary=_summary(role=SimpleDishSemanticRole.salad_side),
    )

    carb_pair = score_pair_compatibility(pasta, rice)
    salad_pair = score_pair_compatibility(pasta, salad)

    assert carb_pair.adjustment < salad_pair.adjustment
    assert any("carb" in reason.lower() for reason in carb_pair.reasons)
