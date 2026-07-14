from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from mealroulette.models.enums import MealPlanDishLineRole, MealPlanDishLineSource, MealPlanningState
from mealroulette.models.planning import MealPlan, MealPlanItem, MealPlanItemDish
from mealroulette.services.meal_plan_lines import sync_legacy_mirror


def capture_item_state(item: MealPlanItem) -> dict:
    return {
        "item_id": item.id,
        "planning_state": item.planning_state.value,
        "dish_id": item.dish_id,
        "recipe_id": item.recipe_id,
        "selection_reasons_json": item.selection_reasons_json,
        "manually_selected": item.manually_selected,
        "lines": [
            {
                "dish_id": line.dish_id,
                "recipe_id": line.recipe_id,
                "position": line.position,
                "role": line.role.value,
                "source": line.source.value,
                "selection_reasons_json": line.selection_reasons_json,
            }
            for line in sorted(item.lines, key=lambda row: row.position)
        ],
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


def _restore_legacy_only(item: MealPlanItem, entry: dict) -> None:
    item.planning_state = MealPlanningState(entry.get("planning_state", MealPlanningState.open.value))
    item.dish_id = entry.get("dish_id")
    item.recipe_id = entry.get("recipe_id")
    item.selection_reasons_json = entry.get("selection_reasons_json")
    item.manually_selected = entry.get("manually_selected", False)
    item.lines.clear()
    if item.dish_id is not None:
        item.lines.append(
            MealPlanItemDish(
                meal_plan_item_id=item.id,
                dish_id=item.dish_id,
                recipe_id=item.recipe_id,
                position=0,
                role=MealPlanDishLineRole.main,
                source=(
                    MealPlanDishLineSource.manual
                    if item.manually_selected
                    else MealPlanDishLineSource.roulette
                ),
                selection_reasons_json=item.selection_reasons_json,
            )
        )


def restore_undo_snapshot(db: Session, plan: MealPlan) -> bool:
    snapshot = plan.last_roulette_undo_json
    if not snapshot:
        return False

    for entry in snapshot.get("items", []):
        item = db.get(MealPlanItem, entry["item_id"])
        if item is None or item.meal_plan_id != plan.id:
            continue
        line_entries = entry.get("lines")
        if line_entries is None:
            _restore_legacy_only(item, entry)
            sync_legacy_mirror(item)
            continue

        item.planning_state = MealPlanningState(entry.get("planning_state", MealPlanningState.open.value))
        db.execute(delete(MealPlanItemDish).where(MealPlanItemDish.meal_plan_item_id == item.id))
        db.flush()
        item.lines.clear()
        for line_entry in line_entries:
            item.lines.append(
                MealPlanItemDish(
                    meal_plan_item_id=item.id,
                    dish_id=line_entry.get("dish_id"),
                    recipe_id=line_entry.get("recipe_id"),
                    position=line_entry.get("position", 0),
                    role=MealPlanDishLineRole(line_entry.get("role", MealPlanDishLineRole.main.value)),
                    source=MealPlanDishLineSource(line_entry.get("source", MealPlanDishLineSource.roulette.value)),
                    selection_reasons_json=line_entry.get("selection_reasons_json"),
                )
            )
        sync_legacy_mirror(item)

    plan.last_roulette_undo_json = None
    return True
