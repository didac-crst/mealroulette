from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from mealroulette.models.enums import MealSlot
from mealroulette.schemas.shopping import ShoppingListItemPublic, ShoppingListPublic, ShoppingPlannedMeal

TELEGRAM_MESSAGE_LIMIT = 4096


def _format_quantity(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        return str(int(normalized))
    return format(normalized, "f").rstrip("0").rstrip(".")


def _format_slot(meal_slot: MealSlot) -> str:
    return "lunch" if meal_slot == MealSlot.lunch else "dinner"


def _format_planned_meal(meal: ShoppingPlannedMeal) -> str:
    recipe = f" ({meal.recipe_variant_name})" if meal.recipe_variant_name else ""
    return f"- {meal.date.isoformat()} {_format_slot(meal.meal_slot)}: {meal.dish_name}{recipe}"


def _format_item_line(item: ShoppingListItemPublic) -> str:
    prefix = "~" if item.approximate else ""
    line = f"- {prefix}{_format_quantity(item.quantity)} {item.unit_symbol} {item.display_name}"
    if item.optional:
        line += " (optional)"
    if item.approximate and len(item.raw_components) > 1:
        parts = " + ".join(
            f"{_format_quantity(component.quantity)} {component.unit_symbol}"
            for component in item.raw_components
        )
        line += f" (includes: {parts})"
    return line


def format_shopping_list_message(
    shopping_list: ShoppingListPublic,
    *,
    group_by_category: bool = True,
    heading: str = "MealRoulette reminder",
) -> str:
    lines = [heading]

    if not shopping_list.items:
        lines.append("No ingredients needed for this window.")
        if shopping_list.planned_meals:
            lines.append("")
            lines.append("Planned meals:")
            for meal in shopping_list.planned_meals:
                lines.append(_format_planned_meal(meal))
        return "\n".join(lines)

    window_label = f"For {shopping_list.from_date.isoformat()} → {shopping_list.to_date.isoformat()} you need:"
    lines.append(window_label)

    if group_by_category:
        grouped: dict[str, list[ShoppingListItemPublic]] = defaultdict(list)
        for item in shopping_list.items:
            grouped[item.category].append(item)
        for category in sorted(grouped):
            lines.append(category.title())
            for item in grouped[category]:
                lines.append(_format_item_line(item))
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()
    else:
        for item in shopping_list.items:
            lines.append(_format_item_line(item))

    if shopping_list.planned_meals:
        lines.append("")
        lines.append("Planned meals:")
        for meal in shopping_list.planned_meals:
            lines.append(_format_planned_meal(meal))

    message = "\n".join(lines)
    if len(message) <= TELEGRAM_MESSAGE_LIMIT:
        return message
    truncated = message[: TELEGRAM_MESSAGE_LIMIT - 40].rstrip()
    return f"{truncated}\n\n… (message truncated)"


def reminder_window_from_date(today: date, *, include_today: bool) -> date:
    if include_today:
        return today
    return today + timedelta(days=1)
