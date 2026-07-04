from __future__ import annotations

from datetime import date

from mealroulette.models.enums import MealPlanItemStatus, MealSlot
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.scheduler.types import DishCandidate, EatenMealSnapshot, GenerationSlot


def slot_is_regenerable(
    *,
    meal_date: date,
    today: date,
    is_locked: bool,
    manually_selected: bool,
    status: MealPlanItemStatus,
) -> bool:
    if is_locked or manually_selected:
        return False
    if meal_date < today:
        return False
    if status != MealPlanItemStatus.planned:
        return False
    return True


def passes_slot_suitability(candidate: DishCandidate, meal_slot: MealSlot) -> bool:
    if meal_slot == MealSlot.lunch and candidate.suitable_for_lunch is False:
        return False
    if meal_slot == MealSlot.dinner and candidate.suitable_for_dinner is False:
        return False
    return True


def build_dish_date_index(
    eaten_meals: list[EatenMealSnapshot],
    planned_dish_dates: list[tuple[int, date]],
) -> dict[int, list[date]]:
    index: dict[int, list[date]] = {}
    for meal in eaten_meals:
        index.setdefault(meal.dish_id, []).append(meal.meal_date)
    for dish_id, meal_date in planned_dish_dates:
        index.setdefault(dish_id, []).append(meal_date)
    return index


def passes_same_dish_window(
    candidate: DishCandidate,
    slot: GenerationSlot,
    *,
    dish_dates: dict[int, list[date]],
    rules: PlanningRulesConfig,
) -> bool:
    from datetime import timedelta

    window_start = slot.meal_date - timedelta(days=rules.avoid_same_dish_within_days)
    for meal_date in dish_dates.get(candidate.dish_id, []):
        if window_start <= meal_date <= slot.meal_date:
            return False
    return True
