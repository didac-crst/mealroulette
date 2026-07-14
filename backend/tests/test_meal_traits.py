from decimal import Decimal

from mealroulette.services.recipe_traits import aggregate_meal_traits


def test_aggregate_meal_traits_sums_grams_across_lines():
    main = {
        "food_group_grams": {"carbohydrate": 300.0, "meat": 200.0},
        "total_trait_grams": 500.0,
        "food_group_weights": {"carbohydrate": 60.0, "meat": 40.0},
        "contains_meat": True,
        "vegan": False,
    }
    side = {
        "food_group_grams": {"vegetable": 150.0},
        "total_trait_grams": 150.0,
        "food_group_weights": {"vegetable": 100.0},
        "contains_meat": False,
        "vegan": True,
    }

    aggregated = aggregate_meal_traits([main, side])
    assert aggregated is not None
    assert aggregated["food_group_grams"]["carbohydrate"] == 300.0
    assert aggregated["food_group_grams"]["vegetable"] == 150.0
    assert aggregated["total_trait_grams"] == 650.0
    assert aggregated["food_group_weights"]["carbohydrate"] == 300 / 650 * 100
    assert aggregated["contains_meat"] is True
    assert aggregated["vegan"] is False


def test_aggregate_meal_traits_reconstructs_grams_from_legacy_weights():
    first = {
        "food_group_weights": {"carbohydrate": 80.0, "cheese": 20.0},
        "total_trait_grams": 100.0,
        "vegan": True,
    }
    second = {
        "food_group_weights": {"vegetable": 100.0},
        "total_trait_grams": 50.0,
        "vegan": True,
    }

    aggregated = aggregate_meal_traits([first, second])
    assert aggregated is not None
    assert aggregated["total_trait_grams"] == 150.0
    assert aggregated["food_group_weights"]["carbohydrate"] == 80 / 150 * 100


def test_aggregate_meal_traits_returns_none_without_data():
    assert aggregate_meal_traits([]) is None
    assert aggregate_meal_traits([{}, {"food_group_weights": {"fruit": 100.0}}]) is None
