"""Unit compatibility and quantity aggregation rules.

This module encodes SPECS §7.7–§7.8 and §9 in executable form. Shopping lists,
exports, and any future feature that combines ingredient amounts must use these
helpers instead of ad-hoc arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mealroulette.models.enums import UnitDimension


class UnitsNotCompatibleError(ValueError):
    """Raised when two units cannot be converted without inventing precision."""


@dataclass(frozen=True)
class UnitInfo:
    id: int
    symbol: str
    dimension: UnitDimension
    conversion_to_base: Decimal


@dataclass(frozen=True)
class IngredientConversion:
    from_unit_id: int
    to_unit_id: int
    factor: Decimal


@dataclass(frozen=True)
class QuantityLine:
    ingredient_id: int
    quantity: Decimal
    unit: UnitInfo


@dataclass(frozen=True)
class AggregatedQuantity:
    ingredient_id: int
    quantity: Decimal
    unit: UnitInfo
    approximate: bool = False


def units_mergeable(
    left: UnitInfo,
    right: UnitInfo,
    conversions: list[IngredientConversion] | None = None,
) -> bool:
    """Return True when two quantities using these units may be summed."""
    try:
        convert_quantity(Decimal("1"), left, right, conversions)
        return True
    except UnitsNotCompatibleError:
        return False


def convert_quantity(
    quantity: Decimal,
    from_unit: UnitInfo,
    to_unit: UnitInfo,
    conversions: list[IngredientConversion] | None = None,
) -> tuple[Decimal, bool]:
    """Convert quantity between units. Returns (amount, is_approximate)."""
    if from_unit.id == to_unit.id:
        return quantity, False

    if from_unit.dimension == to_unit.dimension:
        if from_unit.dimension == UnitDimension.count:
            raise UnitsNotCompatibleError(
                f"Cannot convert count units '{from_unit.symbol}' and '{to_unit.symbol}' "
                "without an ingredient-specific conversion"
            )
        converted = quantity * from_unit.conversion_to_base / to_unit.conversion_to_base
        return converted, False

    conversions = conversions or []
    direct = _find_conversion(from_unit.id, to_unit.id, conversions)
    if direct is not None:
        return quantity * direct, True

    reverse = _find_conversion(to_unit.id, from_unit.id, conversions)
    if reverse is not None:
        return quantity / reverse, True

    raise UnitsNotCompatibleError(
        f"Cannot convert '{from_unit.symbol}' ({from_unit.dimension.value}) to "
        f"'{to_unit.symbol}' ({to_unit.dimension.value})"
    )


def aggregate_quantities(
    lines: list[QuantityLine],
    conversions: list[IngredientConversion] | None = None,
) -> list[AggregatedQuantity]:
    """Merge compatible quantity lines for one ingredient; keep incompatible lines separate."""
    if not lines:
        return []

    conversions = conversions or []
    ingredient_id = lines[0].ingredient_id
    if any(line.ingredient_id != ingredient_id for line in lines):
        raise ValueError("aggregate_quantities expects lines for a single ingredient")

    groups: list[list[QuantityLine]] = [[line] for line in lines]
    merged = True
    while merged:
        merged = False
        next_groups: list[list[QuantityLine]] = []
        consumed: set[int] = set()

        for index, group in enumerate(groups):
            if index in consumed:
                continue
            combined = list(group)
            for other_index, other_group in enumerate(groups):
                if other_index <= index or other_index in consumed:
                    continue
                if _groups_mergeable(combined, other_group, conversions):
                    combined.extend(other_group)
                    consumed.add(other_index)
                    merged = True
            consumed.add(index)
            next_groups.append(combined)
        groups = next_groups

    return [_collapse_group(ingredient_id, group, conversions) for group in groups]


def aggregate_by_ingredient(
    lines: list[QuantityLine],
    conversions_by_ingredient: dict[int, list[IngredientConversion]] | None = None,
) -> list[AggregatedQuantity]:
    """Aggregate quantity lines, grouped per ingredient."""
    conversions_by_ingredient = conversions_by_ingredient or {}
    grouped_lines: dict[int, list[QuantityLine]] = {}
    for line in lines:
        grouped_lines.setdefault(line.ingredient_id, []).append(line)

    results: list[AggregatedQuantity] = []
    for ingredient_id, ingredient_lines in grouped_lines.items():
        conversions = conversions_by_ingredient.get(ingredient_id, [])
        results.extend(aggregate_quantities(ingredient_lines, conversions))
    return results


def _find_conversion(
    from_unit_id: int,
    to_unit_id: int,
    conversions: list[IngredientConversion],
) -> Decimal | None:
    for conversion in conversions:
        if conversion.from_unit_id == from_unit_id and conversion.to_unit_id == to_unit_id:
            return conversion.factor
    return None


def _groups_mergeable(
    left: list[QuantityLine],
    right: list[QuantityLine],
    conversions: list[IngredientConversion],
) -> bool:
    return any(
        units_mergeable(left_line.unit, right_line.unit, conversions)
        for left_line in left
        for right_line in right
    )


def _collapse_group(
    ingredient_id: int,
    group: list[QuantityLine],
    conversions: list[IngredientConversion],
) -> AggregatedQuantity:
    target_unit = _display_unit_for_group(group, conversions)
    total = Decimal("0")
    approximate = False

    for line in group:
        converted, is_approximate = convert_quantity(line.quantity, line.unit, target_unit, conversions)
        total += converted
        approximate = approximate or is_approximate

    return AggregatedQuantity(
        ingredient_id=ingredient_id,
        quantity=total,
        unit=target_unit,
        approximate=approximate,
    )


def _display_unit_for_group(
    group: list[QuantityLine],
    conversions: list[IngredientConversion],
) -> UnitInfo:
    unique_units = list({line.unit.id: line.unit for line in group}.values())
    unique_units.sort(
        key=lambda unit: (
            0 if unit.dimension in {UnitDimension.mass, UnitDimension.volume} else 1,
            unit.conversion_to_base,
            unit.symbol,
        )
    )
    for candidate in unique_units:
        if all(
            units_mergeable(line.unit, candidate, conversions)
            for line in group
        ):
            return candidate
    return group[0].unit
