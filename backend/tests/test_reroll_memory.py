from datetime import date

import pytest

from mealroulette.models.enums import MealPlanDishLineRole, MealPlanDishLineSource, MealPlanItemStatus, MealSlot
from mealroulette.models.planning import MealPlan, MealPlanItem, MealPlanItemDish
from mealroulette.services.scheduler.reroll_memory import (
    append_reroll_combination,
    clear_reroll_history,
    clear_stale_reroll_history,
    combination_key_from_assignment,
    combination_key_from_item,
    combination_key_from_role_dish_pairs,
    forbidden_combination_keys,
    item_reroll_history_is_stale,
    load_reroll_history,
)
from mealroulette.services.scheduler.types import SlotAssignment, SlotAssignmentLine

pytestmark = pytest.mark.unit


def _item(*, dish_id: int | None = None, lines: list[MealPlanItemDish] | None = None) -> MealPlanItem:
    item = MealPlanItem(
        id=1,
        meal_plan_id=10,
        date=__import__("datetime").date(2026, 7, 7),
        meal_slot=MealSlot.lunch,
        dish_id=dish_id,
        status=MealPlanItemStatus.planned,
    )
    if lines is not None:
        item.lines = lines
    return item


def test_combination_key_normalizes_centerpiece_side_order():
    key = combination_key_from_role_dish_pairs(
        [
            (MealPlanDishLineRole.side, 20),
            (MealPlanDishLineRole.centerpiece, 10),
        ]
    )
    assert key == ("centerpiece", 10, "side", 20)


def test_combination_key_from_assignment_for_main_dish():
    assignment = SlotAssignment(
        item_id=1,
        lines=(
            SlotAssignmentLine(
                dish_id=5,
                recipe_id=50,
                role=MealPlanDishLineRole.main,
                position=0,
                selection_reasons_json=None,
            ),
        ),
        score=1.0,
        selection_reasons_json={},
    )
    assert combination_key_from_assignment(assignment) == ("main", 5)


def test_reroll_history_persists_combinations_on_item():
    item = _item()
    append_reroll_combination(item, ("main", 5))
    append_reroll_combination(item, ("centerpiece", 1, "side", 2))

    assert load_reroll_history(item) == {("main", 5), ("centerpiece", 1, "side", 2)}


def test_forbidden_combination_keys_includes_current_and_history():
    item = _item(
        lines=[
            MealPlanItemDish(
                meal_plan_item_id=1,
                dish_id=10,
                recipe_id=100,
                position=0,
                role=MealPlanDishLineRole.main,
                source=MealPlanDishLineSource.roulette,
            )
        ]
    )
    append_reroll_combination(item, ("main", 5))

    forbidden = forbidden_combination_keys(item)
    assert forbidden == {("main", 5), ("main", 10)}


def test_clear_reroll_history_resets_item_payload():
    item = _item()
    append_reroll_combination(item, ("main", 5))
    clear_reroll_history(item)
    assert item.reroll_history_json is None
    assert load_reroll_history(item) == frozenset()


def test_combination_key_from_item_uses_roulette_lines_only():
    item = _item(
        dish_id=99,
        lines=[
            MealPlanItemDish(
                meal_plan_item_id=1,
                dish_id=10,
                recipe_id=100,
                position=0,
                role=MealPlanDishLineRole.centerpiece,
                source=MealPlanDishLineSource.roulette,
            ),
            MealPlanItemDish(
                meal_plan_item_id=1,
                dish_id=20,
                recipe_id=200,
                position=1,
                role=MealPlanDishLineRole.side,
                source=MealPlanDishLineSource.roulette,
            ),
            MealPlanItemDish(
                meal_plan_item_id=1,
                dish_id=30,
                recipe_id=300,
                position=2,
                role=MealPlanDishLineRole.side,
                source=MealPlanDishLineSource.manual,
            ),
        ],
    )
    assert combination_key_from_item(item) == ("centerpiece", 10, "side", 20)


def test_item_reroll_history_is_stale_for_past_slot():
    item = _item()
    item.date = date(2026, 7, 10)
    append_reroll_combination(item, ("main", 5))

    assert item_reroll_history_is_stale(
        item,
        reference_date=date(2026, 7, 14),
        current_week_start=date(2026, 7, 13),
        plan_week_start=date(2026, 7, 13),
    )


def test_item_reroll_history_is_stale_for_past_plan_week():
    item = _item()
    item.date = date(2026, 7, 7)
    append_reroll_combination(item, ("main", 5))

    assert item_reroll_history_is_stale(
        item,
        reference_date=date(2026, 7, 14),
        current_week_start=date(2026, 7, 13),
        plan_week_start=date(2026, 7, 6),
    )


def test_item_reroll_history_is_fresh_for_current_week_future_slot():
    item = _item()
    item.date = date(2026, 7, 16)
    append_reroll_combination(item, ("main", 5))

    assert not item_reroll_history_is_stale(
        item,
        reference_date=date(2026, 7, 14),
        current_week_start=date(2026, 7, 13),
        plan_week_start=date(2026, 7, 13),
    )


def test_clear_stale_reroll_history_clears_only_stale_items():
    plan = MealPlan(id=10, week_start_date=date(2026, 7, 13))
    past_item = _item()
    past_item.date = date(2026, 7, 13)
    future_item = _item()
    future_item.id = 2
    future_item.date = date(2026, 7, 18)
    append_reroll_combination(past_item, ("main", 5))
    append_reroll_combination(future_item, ("main", 6))
    plan.items = [past_item, future_item]

    cleared = clear_stale_reroll_history(
        plan,
        reference_date=date(2026, 7, 14),
        current_week_start=date(2026, 7, 13),
    )

    assert cleared == 1
    assert past_item.reroll_history_json is None
    assert load_reroll_history(future_item) == {("main", 6)}
