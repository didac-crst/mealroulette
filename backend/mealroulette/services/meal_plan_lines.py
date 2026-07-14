from __future__ import annotations

from mealroulette.models.catalog import Dish
from mealroulette.models.enums import (
    MealComposition,
    MealPlanDishLineRole,
    MealPlanDishLineSource,
    MealPlanningState,
    SimpleDishPart,
)
from mealroulette.models.planning import MealPlanItem, MealPlanItemDish


def role_for_dish(dish: Dish) -> MealPlanDishLineRole:
    if dish.meal_composition == MealComposition.dessert:
        return MealPlanDishLineRole.dessert
    if dish.meal_composition == MealComposition.simple_dish:
        if dish.simple_dish_part == SimpleDishPart.centerpiece:
            return MealPlanDishLineRole.centerpiece
        if dish.simple_dish_part == SimpleDishPart.sidedish:
            return MealPlanDishLineRole.side
    return MealPlanDishLineRole.main


def primary_line(lines: list[MealPlanItemDish]) -> MealPlanItemDish | None:
    if not lines:
        return None
    roulette_main = next(
        (line for line in lines if line.source == MealPlanDishLineSource.roulette and line.role == MealPlanDishLineRole.main),
        None,
    )
    if roulette_main is not None:
        return roulette_main
    roulette_centerpiece = next(
        (
            line
            for line in lines
            if line.source == MealPlanDishLineSource.roulette and line.role == MealPlanDishLineRole.centerpiece
        ),
        None,
    )
    if roulette_centerpiece is not None:
        return roulette_centerpiece
    manual_main = next(
        (line for line in lines if line.source == MealPlanDishLineSource.manual and line.role == MealPlanDishLineRole.main),
        None,
    )
    if manual_main is not None:
        return manual_main
    manual_centerpiece = next(
        (
            line
            for line in lines
            if line.source == MealPlanDishLineSource.manual and line.role == MealPlanDishLineRole.centerpiece
        ),
        None,
    )
    if manual_centerpiece is not None:
        return manual_centerpiece
    return min(lines, key=lambda line: line.position)


def compute_meal_title(item: MealPlanItem, lines: list[MealPlanItemDish]) -> str:
    if item.planning_state == MealPlanningState.do_not_plan:
        return "Not planning"
    if not lines:
        return "Unassigned"

    ordered = sorted(lines, key=lambda line: line.position)
    names = [_dish_display_name(line) for line in ordered]
    names = [name for name in names if name]
    if not names:
        return "Unassigned"
    if len(names) == 1:
        return names[0]

    roulette_lines = [line for line in ordered if line.source == MealPlanDishLineSource.roulette]
    if len(ordered) == 2 and len(roulette_lines) == 2:
        centerpiece = next((line for line in roulette_lines if line.role == MealPlanDishLineRole.centerpiece), None)
        side = next((line for line in roulette_lines if line.role == MealPlanDishLineRole.side), None)
        if centerpiece is not None and side is not None:
            centerpiece_name = _dish_display_name(centerpiece)
            side_name = _dish_display_name(side)
            if centerpiece_name and side_name:
                return f"{centerpiece_name} with {side_name}"

    return " + ".join(names)


def _dish_display_name(line: MealPlanItemDish) -> str | None:
    if line.dish is not None:
        return line.dish.name
    return None


def sync_legacy_mirror(item: MealPlanItem) -> None:
    lines = sorted(item.lines, key=lambda line: line.position)
    primary = primary_line(lines)
    if primary is None:
        item.dish_id = None
        item.recipe_id = None
        item.manually_selected = False
        item.selection_reasons_json = None
        return

    item.dish_id = primary.dish_id
    item.recipe_id = primary.recipe_id
    item.manually_selected = primary.source == MealPlanDishLineSource.manual
    item.selection_reasons_json = primary.selection_reasons_json
