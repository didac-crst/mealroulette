from decimal import Decimal

import pytest

from mealroulette.models.enums import UnitDimension
from mealroulette.services.quantities import (
    AggregatedQuantity,
    IngredientConversion,
    QuantityLine,
    UnitInfo,
    UnitsNotCompatibleError,
    aggregate_by_ingredient,
    aggregate_quantities,
    convert_quantity,
    units_mergeable,
)

GRAM = UnitInfo(id=1, symbol="g", dimension=UnitDimension.mass, conversion_to_base=Decimal("1"))
KILOGRAM = UnitInfo(id=2, symbol="kg", dimension=UnitDimension.mass, conversion_to_base=Decimal("1000"))
UNIT = UnitInfo(id=3, symbol="unit", dimension=UnitDimension.count, conversion_to_base=Decimal("1"))
CLOVE = UnitInfo(id=4, symbol="clove", dimension=UnitDimension.count, conversion_to_base=Decimal("1"))


def test_convert_mass_units_through_base():
    converted, approximate = convert_quantity(Decimal("0.5"), KILOGRAM, GRAM)
    assert converted == Decimal("500")
    assert approximate is False


def test_count_units_with_different_symbols_are_not_mergeable():
    assert units_mergeable(UNIT, CLOVE) is False


def test_convert_count_units_requires_ingredient_conversion():
    conversion = IngredientConversion(from_unit_id=UNIT.id, to_unit_id=GRAM.id, factor=Decimal("120"))
    converted, approximate = convert_quantity(Decimal("2"), UNIT, GRAM, [conversion])
    assert converted == Decimal("240")
    assert approximate is True


def test_convert_count_units_via_reverse_conversion():
    conversion = IngredientConversion(from_unit_id=UNIT.id, to_unit_id=GRAM.id, factor=Decimal("120"))
    converted, approximate = convert_quantity(Decimal("240"), GRAM, UNIT, [conversion])
    assert converted == Decimal("2")
    assert approximate is True


def test_convert_count_units_without_conversion_raises():
    with pytest.raises(UnitsNotCompatibleError):
        convert_quantity(Decimal("2"), UNIT, GRAM)


def test_aggregate_compatible_mass_quantities():
    lines = [
        QuantityLine(ingredient_id=10, quantity=Decimal("500"), unit=GRAM),
        QuantityLine(ingredient_id=10, quantity=Decimal("0.5"), unit=KILOGRAM),
    ]

    result = aggregate_quantities(lines)

    assert result == [
        AggregatedQuantity(ingredient_id=10, quantity=Decimal("1000"), unit=GRAM, approximate=False)
    ]


def test_aggregate_incompatible_quantities_stay_separate():
    lines = [
        QuantityLine(ingredient_id=11, quantity=Decimal("2"), unit=UNIT),
        QuantityLine(ingredient_id=11, quantity=Decimal("200"), unit=GRAM),
    ]

    result = aggregate_quantities(lines)

    assert len(result) == 2
    assert {entry.quantity for entry in result} == {Decimal("2"), Decimal("200")}
    assert {entry.unit.symbol for entry in result} == {"unit", "g"}


def test_aggregate_uses_ingredient_conversion_when_configured():
    lines = [
        QuantityLine(ingredient_id=11, quantity=Decimal("2"), unit=UNIT),
        QuantityLine(ingredient_id=11, quantity=Decimal("200"), unit=GRAM),
    ]
    conversions = [IngredientConversion(from_unit_id=UNIT.id, to_unit_id=GRAM.id, factor=Decimal("120"))]

    result = aggregate_quantities(lines, conversions)

    assert result == [
        AggregatedQuantity(ingredient_id=11, quantity=Decimal("440"), unit=GRAM, approximate=True)
    ]


def test_aggregate_same_count_unit():
    lines = [
        QuantityLine(ingredient_id=12, quantity=Decimal("2"), unit=CLOVE),
        QuantityLine(ingredient_id=12, quantity=Decimal("3"), unit=CLOVE),
    ]

    result = aggregate_quantities(lines)

    assert result == [
        AggregatedQuantity(ingredient_id=12, quantity=Decimal("5"), unit=CLOVE, approximate=False)
    ]


def test_aggregate_by_ingredient_groups_independently():
    lines = [
        QuantityLine(ingredient_id=1, quantity=Decimal("100"), unit=GRAM),
        QuantityLine(ingredient_id=2, quantity=Decimal("1"), unit=UNIT),
        QuantityLine(ingredient_id=2, quantity=Decimal("2"), unit=UNIT),
    ]

    result = aggregate_by_ingredient(lines)

    assert result == [
        AggregatedQuantity(ingredient_id=1, quantity=Decimal("100"), unit=GRAM, approximate=False),
        AggregatedQuantity(ingredient_id=2, quantity=Decimal("3"), unit=UNIT, approximate=False),
    ]
