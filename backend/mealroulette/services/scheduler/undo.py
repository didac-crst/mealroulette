from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from mealroulette.models.planning import MealPlan, MealPlanItem


def capture_item_state(item: MealPlanItem) -> dict:
    return {
        "item_id": item.id,
        "dish_id": item.dish_id,
        "recipe_id": item.recipe_id,
        "selection_reasons_json": item.selection_reasons_json,
        "manually_selected": item.manually_selected,
    }


def save_undo_snapshot(
    plan: MealPlan,
    *,
    action: str,
    items: list[MealPlanItem],
) -> None:
    plan.last_roulette_undo_json = {
        "action": action,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "items": [capture_item_state(item) for item in items],
    }


def clear_undo_snapshot(plan: MealPlan) -> None:
    plan.last_roulette_undo_json = None


def restore_undo_snapshot(db: Session, plan: MealPlan) -> bool:
    snapshot = plan.last_roulette_undo_json
    if not snapshot:
        return False

    for entry in snapshot.get("items", []):
        item = db.get(MealPlanItem, entry["item_id"])
        if item is None or item.meal_plan_id != plan.id:
            continue
        item.dish_id = entry.get("dish_id")
        item.recipe_id = entry.get("recipe_id")
        item.selection_reasons_json = entry.get("selection_reasons_json")
        item.manually_selected = entry.get("manually_selected", False)

    plan.last_roulette_undo_json = None
    return True
