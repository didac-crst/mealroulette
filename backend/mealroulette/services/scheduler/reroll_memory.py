from __future__ import annotations

from mealroulette.models.enums import MealPlanDishLineRole, MealPlanDishLineSource
from mealroulette.models.planning import MealPlanItem
from mealroulette.services.scheduler.composition import item_has_roulette_lines
from mealroulette.services.scheduler.types import SlotAssignment


def combination_key_from_role_dish_pairs(pairs: list[tuple[MealPlanDishLineRole, int]]) -> tuple:
    by_role = {role: dish_id for role, dish_id in pairs}
    if MealPlanDishLineRole.main in by_role:
        return ("main", by_role[MealPlanDishLineRole.main])

    centerpiece = by_role.get(MealPlanDishLineRole.centerpiece)
    side = by_role.get(MealPlanDishLineRole.side)
    if centerpiece is not None and side is not None:
        return ("centerpiece", centerpiece, "side", side)

    if len(pairs) == 1:
        role, dish_id = pairs[0]
        return (role.value, dish_id)

    raise ValueError("Cannot normalize meal combination from role/dish pairs")


def combination_key_from_assignment(assignment: SlotAssignment) -> tuple:
    return combination_key_from_role_dish_pairs([(line.role, line.dish_id) for line in assignment.lines])


def combination_key_from_item(item: MealPlanItem) -> tuple | None:
    roulette_pairs = [
        (line.role, line.dish_id)
        for line in item.lines
        if line.source == MealPlanDishLineSource.roulette and line.dish_id is not None
    ]
    if roulette_pairs:
        return combination_key_from_role_dish_pairs(roulette_pairs)

    if item.dish_id is not None and not item_has_roulette_lines(item):
        return ("main", item.dish_id)
    return None


def _deserialize_combination(raw: list) -> tuple:
    return tuple(raw)


def load_reroll_history(item: MealPlanItem) -> frozenset[tuple]:
    payload = item.reroll_history_json
    if not isinstance(payload, dict):
        return frozenset()

    combinations = payload.get("combinations")
    if not isinstance(combinations, list):
        return frozenset()

    keys: set[tuple] = set()
    for entry in combinations:
        if isinstance(entry, list) and entry:
            keys.add(_deserialize_combination(entry))
    return frozenset(keys)


def save_reroll_history(item: MealPlanItem, combinations: frozenset[tuple]) -> None:
    if not combinations:
        item.reroll_history_json = None
        return
    item.reroll_history_json = {
        "combinations": [list(key) for key in sorted(combinations, key=str)],
    }


def clear_reroll_history(item: MealPlanItem) -> None:
    item.reroll_history_json = None


def append_reroll_combination(item: MealPlanItem, combination: tuple) -> None:
    history = load_reroll_history(item)
    save_reroll_history(item, history | {combination})


def forbidden_combination_keys(item: MealPlanItem) -> frozenset[tuple]:
    current = combination_key_from_item(item)
    history = load_reroll_history(item)
    if current is None:
        return history
    return history | {current}
