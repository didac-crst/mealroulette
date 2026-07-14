import pytest

from mealroulette.models.enums import MealComposition, SeasonalityMode, SimpleDishPart
from mealroulette.services.scheduler.pair_diagnostics import CandidatePairSummary, SimpleDishSemanticRole
from mealroulette.services.scheduler.pair_rejections import (
    PairRejectionCode,
    evaluate_pair_hard_rejections,
    pair_is_hard_rejected,
)
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


def _fish_traits(*, dominant_protein: str, fish_pct: float = 70.0) -> dict:
    return {
        "food_group_weights": {"fish": fish_pct, "vegetable": 100.0 - fish_pct},
        "dominant_protein": dominant_protein,
        "total_trait_grams": 400.0,
    }


def _summary(
    *,
    ingredient_ids: frozenset[int] = frozenset(),
    family_keys: frozenset[str] = frozenset(),
    role: SimpleDishSemanticRole | None = None,
) -> CandidatePairSummary:
    return CandidatePairSummary(
        primary_ingredient_ids=ingredient_ids,
        primary_family_keys=family_keys,
        semantic_role=role,
    )


@pytest.mark.parametrize(
    ("centerpiece", "side", "expected_codes"),
    [
        pytest.param(
            _candidate(
                1,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits=_fish_traits(dominant_protein="sardine_family"),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
            ),
            _candidate(
                2,
                simple_dish_part=SimpleDishPart.sidedish,
                traits=_fish_traits(dominant_protein="tuna_family", fish_pct=35.0),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_side),
            ),
            {PairRejectionCode.duplicate_dominant_protein},
            id="sardines_plus_tomato_with_tuna",
        ),
        pytest.param(
            _candidate(
                3,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits=_fish_traits(dominant_protein="tuna_family"),
                pair_summary=_summary(
                    ingredient_ids=frozenset({501}),
                    role=SimpleDishSemanticRole.protein_centerpiece,
                ),
            ),
            _candidate(
                4,
                simple_dish_part=SimpleDishPart.sidedish,
                traits=_fish_traits(dominant_protein="tuna_family", fish_pct=30.0),
                pair_summary=_summary(
                    ingredient_ids=frozenset({501}),
                    role=SimpleDishSemanticRole.protein_side,
                ),
            ),
            {PairRejectionCode.shared_primary_ingredient, PairRejectionCode.duplicate_dominant_protein},
            id="tuna_steak_plus_tomato_with_tuna",
        ),
        pytest.param(
            _candidate(
                5,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits=_fish_traits(dominant_protein="white_fish_family"),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
            ),
            _candidate(
                6,
                simple_dish_part=SimpleDishPart.sidedish,
                traits=_fish_traits(dominant_protein="tuna_family", fish_pct=30.0),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_side),
            ),
            {PairRejectionCode.duplicate_dominant_protein},
            id="fish_fillet_plus_tomato_with_tuna",
        ),
        pytest.param(
            _candidate(
                7,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits={
                    "food_group_weights": {"meat": 65.0, "vegetable": 35.0},
                    "dominant_protein": "pork_family",
                    "total_trait_grams": 450.0,
                },
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
            ),
            _candidate(
                8,
                simple_dish_part=SimpleDishPart.sidedish,
                traits=_fish_traits(dominant_protein="tuna_family", fish_pct=30.0),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_side),
            ),
            {PairRejectionCode.competing_animal_proteins},
            id="sausages_plus_tomato_with_tuna",
        ),
        pytest.param(
            _candidate(
                9,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits={
                    "food_group_weights": {"legume": 55.0, "vegetable": 45.0},
                    "dominant_protein": "bean_family",
                    "total_trait_grams": 420.0,
                },
                pair_summary=_summary(
                    family_keys=frozenset({"bean_family"}),
                    role=SimpleDishSemanticRole.legume_centerpiece,
                ),
            ),
            _candidate(
                10,
                simple_dish_part=SimpleDishPart.sidedish,
                traits={
                    "food_group_weights": {"legume": 60.0, "vegetable": 40.0},
                    "dominant_protein": "green_bean_family",
                    "total_trait_grams": 300.0,
                },
                pair_summary=_summary(
                    family_keys=frozenset({"bean_family"}),
                    role=SimpleDishSemanticRole.vegetable_side,
                ),
            ),
            {PairRejectionCode.primary_family_overlap},
            id="baked_beans_plus_steamed_green_beans",
        ),
        pytest.param(
            _candidate(
                11,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits={
                    "food_group_weights": {"egg": 55.0, "vegetable": 45.0},
                    "dominant_protein": "egg_family",
                    "total_trait_grams": 350.0,
                },
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
            ),
            _candidate(
                12,
                simple_dish_part=SimpleDishPart.sidedish,
                traits={
                    "food_group_weights": {"vegetable": 85.0, "pantry": 15.0},
                    "total_trait_grams": 280.0,
                },
                pair_summary=_summary(role=SimpleDishSemanticRole.vegetable_side),
            ),
            set(),
            id="zucchini_omelette_plus_grilled_eggplant",
        ),
        pytest.param(
            _candidate(
                13,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits=_fish_traits(dominant_protein="sardine_family"),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
            ),
            _candidate(
                14,
                simple_dish_part=SimpleDishPart.sidedish,
                traits={
                    "food_group_weights": {"vegetable": 80.0, "pantry": 20.0},
                    "total_trait_grams": 250.0,
                },
                pair_summary=_summary(role=SimpleDishSemanticRole.salad_side),
                tag_names=frozenset({"salad"}),
            ),
            set(),
            id="sardines_plus_tomato_salad",
        ),
        pytest.param(
            _candidate(
                15,
                simple_dish_part=SimpleDishPart.centerpiece,
                traits=_fish_traits(dominant_protein="sardine_family"),
                pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
            ),
            _candidate(
                16,
                simple_dish_part=SimpleDishPart.sidedish,
                traits={
                    "food_group_weights": {"carbohydrate": 75.0, "vegetable": 25.0},
                    "dominant_carb": "potato_family",
                    "total_trait_grams": 320.0,
                },
                pair_summary=_summary(role=SimpleDishSemanticRole.carb_side),
            ),
            set(),
            id="sardines_plus_boiled_potatoes",
        ),
    ],
)
def test_pair_hard_rejections_match_acceptance_table(centerpiece, side, expected_codes):
    result = evaluate_pair_hard_rejections(centerpiece, side)
    assert {reason.code for reason in result.reasons} == expected_codes
    assert result.rejected == bool(expected_codes)


def test_sauce_or_condiment_side_is_rejected():
    centerpiece = _candidate(
        20,
        simple_dish_part=SimpleDishPart.centerpiece,
        traits={
            "food_group_weights": {"meat": 70.0, "vegetable": 30.0},
            "dominant_protein": "chicken_family",
            "total_trait_grams": 400.0,
        },
        pair_summary=_summary(role=SimpleDishSemanticRole.protein_centerpiece),
    )
    side = _candidate(
        21,
        simple_dish_part=SimpleDishPart.sidedish,
        traits={"food_group_weights": {"condiment": 100.0}, "total_trait_grams": 40.0},
        pair_summary=_summary(role=SimpleDishSemanticRole.sauce_or_condiment),
    )

    result = evaluate_pair_hard_rejections(centerpiece, side)
    assert result.rejected
    assert result.reasons[0].code == PairRejectionCode.invalid_side_identity


def test_missing_pair_data_does_not_invent_rejections():
    centerpiece = _candidate(30, simple_dish_part=SimpleDishPart.centerpiece)
    side = _candidate(31, simple_dish_part=SimpleDishPart.sidedish)
    assert not pair_is_hard_rejected(centerpiece, side)
