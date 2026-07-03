"""Unit compatibility and quantity aggregation rules.

This module encodes SPECS §7.7–§7.8 and §9 in executable form. Shopping lists,
exports, and any future feature that combines ingredient amounts must use these
helpers instead of ad-hoc arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from collections.abc import Callable
from typing import TypeVar

from mealroulette.models.enums import AggregationStrategy, UnitDimension

T = TypeVar("T")


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


def partition_merge_groups(items: list[T], mergeable: Callable[[T, T], bool]) -> list[list[T]]:
    """Group items transitively when any pair satisfies mergeable."""
    groups: list[list[T]] = [[item] for item in items]
    merged = True
    while merged:
        merged = False
        next_groups: list[list[T]] = []
        consumed: set[int] = set()

        for index, group in enumerate(groups):
            if index in consumed:
                continue
            combined = list(group)
            for other_index, other_group in enumerate(groups):
                if other_index <= index or other_index in consumed:
                    continue
                if any(mergeable(left, right) for left in combined for right in other_group):
                    combined.extend(other_group)
                    consumed.add(other_index)
                    merged = True
            consumed.add(index)
            next_groups.append(combined)
        groups = next_groups
    return groups


def cross_dimension_mergeable(
    left: UnitInfo,
    right: UnitInfo,
    strategy: AggregationStrategy | None,
    conversions: list[IngredientConversion] | None = None,
) -> bool:
    """Whether two quantities may be summed when dimensions differ."""
    if left.dimension == right.dimension:
        return units_mergeable(left, right, conversions)
    if strategy == AggregationStrategy.strict_same_dimension:
        return False
    if strategy == AggregationStrategy.never_convert_count:
        if UnitDimension.count in {left.dimension, right.dimension}:
            return False
        return units_mergeable(left, right, conversions)
    if strategy == AggregationStrategy.prefer_count:
        return False
    if strategy == AggregationStrategy.prefer_mass:
        if UnitDimension.mass not in {left.dimension, right.dimension}:
            return False
        return units_mergeable(left, right, conversions)
    if strategy == AggregationStrategy.prefer_volume:
        if UnitDimension.volume not in {left.dimension, right.dimension}:
            return False
        return units_mergeable(left, right, conversions)
    return units_mergeable(left, right, conversions)


def aggregate_quantities(
    lines: list[QuantityLine],
    conversions: list[IngredientConversion] | None = None,
    *,
    aggregation_strategy: AggregationStrategy | None = None,
    preferred_display_unit: UnitInfo | None = None,
) -> list[AggregatedQuantity]:
    """Merge compatible quantity lines for one ingredient; keep incompatible lines separate."""
    if not lines:
        return []

    conversions = conversions or []
    ingredient_id = lines[0].ingredient_id
    if any(line.ingredient_id != ingredient_id for line in lines):
        raise ValueError("aggregate_quantities expects lines for a single ingredient")

    groups = partition_merge_groups(
        lines,
        lambda left, right: _groups_mergeable([left], [right], conversions, aggregation_strategy),
    )

    return [_collapse_group(ingredient_id, group, conversions, aggregation_strategy, preferred_display_unit) for group in groups]


def aggregate_by_ingredient(
    lines: list[QuantityLine],
    conversions_by_ingredient: dict[int, list[IngredientConversion]] | None = None,
    *,
    aggregation_strategy_by_ingredient: dict[int, AggregationStrategy | None] | None = None,
    preferred_display_unit_by_ingredient: dict[int, UnitInfo | None] | None = None,
) -> list[AggregatedQuantity]:
    """Aggregate quantity lines, grouped per ingredient."""
    conversions_by_ingredient = conversions_by_ingredient or {}
    aggregation_strategy_by_ingredient = aggregation_strategy_by_ingredient or {}
    preferred_display_unit_by_ingredient = preferred_display_unit_by_ingredient or {}
    grouped_lines: dict[int, list[QuantityLine]] = {}
    for line in lines:
        grouped_lines.setdefault(line.ingredient_id, []).append(line)

    results: list[AggregatedQuantity] = []
    for ingredient_id, ingredient_lines in grouped_lines.items():
        conversions = conversions_by_ingredient.get(ingredient_id, [])
        results.extend(
            aggregate_quantities(
                ingredient_lines,
                conversions,
                aggregation_strategy=aggregation_strategy_by_ingredient.get(ingredient_id),
                preferred_display_unit=preferred_display_unit_by_ingredient.get(ingredient_id),
            )
        )
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
    aggregation_strategy: AggregationStrategy | None = None,
) -> bool:
    return any(
        cross_dimension_mergeable(left_line.unit, right_line.unit, aggregation_strategy, conversions)
        for left_line in left
        for right_line in right
    )


def _collapse_group(
    ingredient_id: int,
    group: list[QuantityLine],
    conversions: list[IngredientConversion],
    aggregation_strategy: AggregationStrategy | None = None,
    preferred_display_unit: UnitInfo | None = None,
) -> AggregatedQuantity:
    target_unit = _display_unit_for_group(group, conversions, aggregation_strategy, preferred_display_unit)
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
    aggregation_strategy: AggregationStrategy | None = None,
    preferred_display_unit: UnitInfo | None = None,
) -> UnitInfo:
    def validated(candidates: list[UnitInfo]) -> UnitInfo | None:
        for candidate in candidates:
            if all(
                cross_dimension_mergeable(line.unit, candidate, aggregation_strategy, conversions)
                for line in group
            ):
                return candidate
        return None

    if preferred_display_unit is not None:
        candidate = validated([preferred_display_unit])
        if candidate is not None:
            return candidate

    unique_units = list({line.unit.id: line.unit for line in group}.values())
    if aggregation_strategy == AggregationStrategy.prefer_count:
        count_units = sorted(
            (unit for unit in unique_units if unit.dimension == UnitDimension.count),
            key=lambda unit: unit.symbol,
        )
        candidate = validated(count_units)
        if candidate is not None:
            return candidate
    if aggregation_strategy == AggregationStrategy.prefer_mass:
        mass_units = sorted(
            (unit for unit in unique_units if unit.dimension == UnitDimension.mass),
            key=lambda unit: (unit.conversion_to_base, unit.symbol),
        )
        candidate = validated(mass_units)
        if candidate is not None:
            return candidate
    if aggregation_strategy == AggregationStrategy.prefer_volume:
        volume_units = sorted(
            (unit for unit in unique_units if unit.dimension == UnitDimension.volume),
            key=lambda unit: (unit.conversion_to_base, unit.symbol),
        )
        candidate = validated(volume_units)
        if candidate is not None:
            return candidate

    unique_units.sort(
        key=lambda unit: (
            0 if unit.dimension in {UnitDimension.mass, UnitDimension.volume} else 1,
            unit.conversion_to_base,
            unit.symbol,
        )
    )
    candidate = validated(unique_units)
    if candidate is not None:
        return candidate
    return group[0].unit
