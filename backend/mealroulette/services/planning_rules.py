from datetime import date, timedelta

from mealroulette.models.enums import MealPlanItemStatus, MealSlot

LEFTOVER_SOURCE_WINDOW_DAYS = 7
_SLOT_ORDER = {MealSlot.lunch: 0, MealSlot.dinner: 1}
_EATEN_STATUSES = {MealPlanItemStatus.eaten, MealPlanItemStatus.ate_leftovers}


def is_future_meal_date(meal_date: date, *, today: date | None = None) -> bool:
    reference = today if today is not None else date.today()
    return meal_date > reference


def can_execute_meal_status(meal_date: date, *, today: date | None = None) -> bool:
    return not is_future_meal_date(meal_date, today=today)


def meal_slot_sort_key(meal_slot: MealSlot) -> int:
    return _SLOT_ORDER[meal_slot]


def is_valid_leftover_source_status(status: MealPlanItemStatus) -> bool:
    return status == MealPlanItemStatus.eaten


def is_within_leftover_window(
    source_date: date,
    item_date: date,
    *,
    window_days: int = LEFTOVER_SOURCE_WINDOW_DAYS,
) -> bool:
    earliest = item_date - timedelta(days=window_days)
    return earliest <= source_date <= item_date


def is_leftover_source_candidate(
    *,
    source_id: int,
    source_date: date,
    source_status: MealPlanItemStatus,
    item_id: int,
    item_date: date,
    window_days: int = LEFTOVER_SOURCE_WINDOW_DAYS,
) -> bool:
    if source_id == item_id:
        return False
    if not is_valid_leftover_source_status(source_status):
        return False
    return is_within_leftover_window(source_date, item_date, window_days=window_days)
