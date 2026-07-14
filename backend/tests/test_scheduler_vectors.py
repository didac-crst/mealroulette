from decimal import Decimal

import pytest

from mealroulette.models.enums import UnitDimension
from mealroulette.services.quantities import IngredientConversion, UnitInfo
from mealroulette.services.scheduler.family_vector import (
    VectorIngredientLine,
    build_family_vector,
    ingredient_line_to_reference_grams,
)
from mealroulette.services.scheduler.similarity import (
    cosine_similarity,
    shared_family_keys,
    similarity_distance,
)

GRAM = UnitInfo(id=1, symbol="g", dimension=UnitDimension.mass, conversion_to_base=Decimal("1"))
KILOGRAM = UnitInfo(id=2, symbol="kg", dimension=UnitDimension.mass, conversion_to_base=Decimal("1000"))
UNIT = UnitInfo(id=3, symbol="unit", dimension=UnitDimension.count, conversion_to_base=Decimal("1"))
MILLILITER = UnitInfo(id=4, symbol="ml", dimension=UnitDimension.volume, conversion_to_base=Decimal("1"))
LITER = UnitInfo(id=5, symbol="l", dimension=UnitDimension.volume, conversion_to_base=Decimal("1000"))


def test_mass_line_converts_to_grams():
    grams, fallback = ingredient_line_to_reference_grams(
        Decimal("0.5"),
        KILOGRAM,
        gram_unit=GRAM,
        ml_unit=MILLILITER,
    )
    assert grams == Decimal("500")
    assert fallback is False


def test_volume_line_converts_ml_then_treats_as_grams():
    grams, fallback = ingredient_line_to_reference_grams(
        Decimal("2"),
        LITER,
        gram_unit=GRAM,
        ml_unit=MILLILITER,
    )
    assert grams == Decimal("2000")
    assert fallback is False


def test_volume_without_conversion_uses_raw_quantity_as_grams():
    exotic_volume = UnitInfo(id=99, symbol="dash", dimension=UnitDimension.volume, conversion_to_base=Decimal("1"))
    grams, fallback = ingredient_line_to_reference_grams(
        Decimal("3"),
        exotic_volume,
        gram_unit=GRAM,
        ml_unit=MILLILITER,
        conversions=[],
    )
    assert grams == Decimal("3")
    assert fallback is False


def test_count_line_uses_approved_conversion():
    conversion = IngredientConversion(from_unit_id=UNIT.id, to_unit_id=GRAM.id, factor=Decimal("80"))
    grams, fallback = ingredient_line_to_reference_grams(
        Decimal("2"),
        UNIT,
        gram_unit=GRAM,
        ml_unit=MILLILITER,
        conversions=[conversion],
    )
    assert grams == Decimal("160")
    assert fallback is False


def test_count_line_uses_default_grams_per_count_fallback():
    grams, fallback = ingredient_line_to_reference_grams(
        Decimal("2"),
        UNIT,
        gram_unit=GRAM,
        ml_unit=MILLILITER,
        conversions=[],
        default_grams_per_count=100,
    )
    assert grams == Decimal("200")
    assert fallback is True


def test_build_family_vector_excludes_small_lines():
    result = build_family_vector(
        [
            VectorIngredientLine(
                family="pasta_family",
                category=None,
                canonical_name="pasta",
                pantry_item=False,
                quantity=Decimal("400"),
                unit=GRAM,
            ),
            VectorIngredientLine(
                family="spice_family",
                category=None,
                canonical_name="pepper",
                pantry_item=False,
                quantity=Decimal("2"),
                unit=GRAM,
            ),
        ],
        gram_unit=GRAM,
        ml_unit=MILLILITER,
        vector_min_grams=5,
    )

    assert result.weights == {"pasta_family": 100.0}
    assert result.count_fallback_lines == 0


def test_build_family_vector_includes_pantry_when_mass_is_significant():
    result = build_family_vector(
        [
            VectorIngredientLine(
                family="pasta_family",
                category=None,
                canonical_name="pasta",
                pantry_item=False,
                quantity=Decimal("400"),
                unit=GRAM,
            ),
            VectorIngredientLine(
                family="tomato_family",
                category=None,
                canonical_name="canned_tomatoes",
                pantry_item=True,
                quantity=Decimal("200"),
                unit=GRAM,
            ),
            VectorIngredientLine(
                family="salt_family",
                category=None,
                canonical_name="salt",
                pantry_item=True,
                quantity=Decimal("3"),
                unit=GRAM,
            ),
        ],
        gram_unit=GRAM,
        ml_unit=MILLILITER,
        vector_min_grams=5,
    )

    assert pytest.approx(result.weights["pasta_family"], rel=1e-6) == 66.666666
    assert pytest.approx(result.weights["tomato_family"], rel=1e-6) == 33.333333


def test_build_family_vector_l1_normalizes_to_one_hundred():
    result = build_family_vector(
        [
            VectorIngredientLine(
                family="pasta_family",
                category=None,
                canonical_name="pasta",
                pantry_item=False,
                quantity=Decimal("300"),
                unit=GRAM,
            ),
            VectorIngredientLine(
                family="tomato_family",
                category=None,
                canonical_name="tomato",
                pantry_item=False,
                quantity=Decimal("200"),
                unit=GRAM,
            ),
        ],
        gram_unit=GRAM,
        ml_unit=MILLILITER,
    )

    assert pytest.approx(sum(result.weights.values()), rel=1e-6) == 100.0
    assert pytest.approx(result.weights["pasta_family"], rel=1e-6) == 60.0
    assert pytest.approx(result.weights["tomato_family"], rel=1e-6) == 40.0


def test_build_family_vector_uses_category_and_canonical_fallback():
    result = build_family_vector(
        [
            VectorIngredientLine(
                family=None,
                category="vegetable",
                canonical_name="carrot",
                pantry_item=False,
                quantity=Decimal("100"),
                unit=GRAM,
            ),
            VectorIngredientLine(
                family=None,
                category=None,
                canonical_name="mystery",
                pantry_item=False,
                quantity=Decimal("100"),
                unit=GRAM,
            ),
        ],
        gram_unit=GRAM,
        ml_unit=MILLILITER,
    )

    assert set(result.weights) == {"vegetable", "mystery"}


def test_cosine_identical_vectors_have_zero_distance():
    vector = {"pasta_family": 60.0, "tomato_family": 40.0}
    assert cosine_similarity(vector, vector) == pytest.approx(1.0)
    assert similarity_distance(vector, vector) == pytest.approx(0.0)


def test_cosine_orthogonal_vectors_have_distance_one():
    left = {"pasta_family": 100.0}
    right = {"fish_family": 100.0}
    assert cosine_similarity(left, right) == pytest.approx(0.0)
    assert similarity_distance(left, right) == pytest.approx(1.0)


def test_new_family_key_does_not_break_comparison():
    older = {"pasta_family": 70.0, "tomato_family": 30.0}
    newer = {**older, "basil_family": 10.0}
    # Renormalized newer for realistic compare
    total = sum(newer.values())
    newer = {key: value / total * 100 for key, value in newer.items()}

    distance = similarity_distance(older, newer)
    assert 0.0 <= distance <= 1.0
    assert shared_family_keys(older, newer)


def test_empty_vectors_are_identical():
    assert similarity_distance({}, {}) == pytest.approx(0.0)
    assert similarity_distance({"pasta_family": 100.0}, {}) == pytest.approx(1.0)
