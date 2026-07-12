from __future__ import annotations

from collections import defaultdict
from datetime import date

from mealroulette.models.enums import MealSlot
from mealroulette.schemas.planning import MealPlanItemPublic
from mealroulette.schemas.shopping import ShoppingListItemPublic, ShoppingListPublic
from mealroulette.services.telegram_format import _format_quantity
from mealroulette.services.telegram_html_utils import esc as _esc, truncate_message as _truncate_message
from mealroulette.services.telegram_recipe import format_meal_assignment_html

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_INDENT = "  "


def _format_plan_date(value: date) -> str:
    return f"{value.strftime('%A')}, {_MONTHS[value.month - 1]} {value.day}"


def _format_slot_label(meal_slot: MealSlot) -> str:
    return "Lunch" if meal_slot == MealSlot.lunch else "Dinner"


def _format_meal_time(prep_time_minutes: int | None, cook_time_minutes: int | None) -> str:
    if prep_time_minutes is None and cook_time_minutes is None:
        return ""
    prep = "—" if prep_time_minutes is None else str(prep_time_minutes)
    cook = "—" if cook_time_minutes is None else str(cook_time_minutes)
    return f" · <i>{prep} / {cook} min</i>"


def _append_planning_days(
    lines: list[str],
    items: list[MealPlanItemPublic],
    *,
    bot_username: str | None = None,
) -> None:
    if not items:
        lines.append("")
        lines.append("<i>No meals in this window.</i>")
        return

    grouped: dict[date, list[MealPlanItemPublic]] = defaultdict(list)
    for item in items:
        grouped[item.date].append(item)

    for day in sorted(grouped):
        lines.append("")
        lines.append(f"<b>{_esc(_format_plan_date(day))}</b>")
        for item in grouped[day]:
            slot = _format_slot_label(item.meal_slot)
            if item.dish_name:
                assignment = format_meal_assignment_html(
                    dish_name=item.dish_name,
                    recipe_variant_name=item.recipe_variant_name,
                    recipe_id=item.recipe_id,
                    bot_username=bot_username,
                )
            else:
                assignment = "<i>Not assigned</i>"
            time_suffix = _format_meal_time(item.prep_time_minutes, item.cook_time_minutes)
            lines.append(f"{_INDENT}• <b>{slot}</b>: {assignment}{time_suffix}")


def _category_label(category: str) -> str | None:
    label = category.strip().replace("_", " ")
    if not label or label.lower() == "other":
        return None
    return label.title()


def _append_shopping_totals(lines: list[str], items: list[ShoppingListItemPublic]) -> None:
    grouped: dict[str | None, list[ShoppingListItemPublic]] = defaultdict(list)
    for item in items:
        grouped[_category_label(item.category)].append(item)

    sections: list[tuple[str | None, list[ShoppingListItemPublic]]] = [
        (label, grouped[label])
        for label in sorted((key for key in grouped if key is not None), key=str.casefold)
    ]
    if None in grouped:
        sections.append((None, grouped[None]))

    for index, (label, section_items) in enumerate(sections):
        if index > 0:
            lines.append("")
        if label:
            lines.append(f"<b>{_esc(label)}</b>")
        for item in sorted(section_items, key=lambda row: row.display_name.casefold()):
            lines.append(_format_shopping_totals_line(item))


def _format_shopping_totals_line(item: ShoppingListItemPublic) -> str:
    prefix = "~" if item.approximate else ""
    quantity = _format_quantity(item.quantity)
    qty_label = f"{prefix}{quantity} {_esc(item.unit_symbol)}"
    optional = " <i>(optional)</i>" if item.optional else ""
    return f"{_INDENT}• <b>{_esc(item.display_name)} — {qty_label}</b>{optional}"


def _format_ingredient_item_lines(item: ShoppingListItemPublic) -> list[str]:
    prefix = "~" if item.approximate else ""
    quantity = _format_quantity(item.quantity)
    qty_label = f"{prefix}{quantity} {_esc(item.unit_symbol)}"
    optional = " (optional)" if item.optional else ""
    lines = [f"{_INDENT}• <b>{_esc(item.display_name)} — {qty_label}</b>{optional}"]

    if item.approximate and len(item.raw_components) > 1:
        parts = " + ".join(
            f"{_format_quantity(component.quantity)} {_esc(component.unit_symbol)}"
            for component in item.raw_components
        )
        lines.append(f"{_INDENT}{_INDENT}includes: {parts}")

    for contribution in item.source_contributions:
        qty = _format_quantity(contribution.quantity)
        lines.append(
            f"{_INDENT}{_INDENT}↳ {_esc(contribution.dish_name)} — "
            f"{qty} {_esc(contribution.unit_symbol)}"
        )

    return lines


def format_planning_message_html(
    items: list[MealPlanItemPublic],
    *,
    from_date: date,
    to_date: date,
    days: int,
    bot_username: str | None = None,
    heading: str = "Planning",
) -> str:
    lines = [
        f"<b>{_esc(heading)}</b>",
        f"{_INDENT}<i>{_esc(_format_plan_date(from_date))} → {_esc(_format_plan_date(to_date))} "
        f"({days} day{'s' if days != 1 else ''})</i>",
    ]
    _append_planning_days(lines, items, bot_username=bot_username)
    return _truncate_message("\n".join(lines))


def format_reminder_message_html(
    shopping_list: ShoppingListPublic,
    planning_items: list[MealPlanItemPublic],
    *,
    from_date: date,
    to_date: date,
    days: int,
    pantry_note: str = "pantry included",
    bot_username: str | None = None,
) -> str:
    lines = [
        "<b>Reminder</b>",
        f"{_INDENT}<i>{_esc(_format_plan_date(from_date))} → {_esc(_format_plan_date(to_date))} "
        f"({days} day{'s' if days != 1 else ''}) · {pantry_note}</i>",
    ]
    _append_planning_days(lines, planning_items, bot_username=bot_username)

    if not shopping_list.items:
        lines.append("")
        lines.append("<i>No ingredients needed for planned meals in this window.</i>")
        return _truncate_message("\n".join(lines))

    lines.append("")
    lines.append("<b>Ingredients list:</b>")
    for item in sorted(shopping_list.items, key=lambda row: row.display_name.casefold()):
        lines.extend(_format_ingredient_item_lines(item))

    return _truncate_message("\n".join(lines))


def format_shopping_message_html(
    shopping_list: ShoppingListPublic,
    *,
    from_date: date,
    to_date: date,
    days: int,
    pantry_note: str = "pantry included",
) -> str:
    lines = [
        "<b>Shopping</b>",
        f"{_INDENT}<i>{_esc(_format_plan_date(from_date))} → {_esc(_format_plan_date(to_date))} "
        f"({days} day{'s' if days != 1 else ''}) · {pantry_note}</i>",
    ]

    if not shopping_list.items:
        lines.append("")
        lines.append("<i>Nothing to buy for planned meals in this window.</i>")
        return _truncate_message("\n".join(lines))

    lines.append("")
    _append_shopping_totals(lines, shopping_list.items)

    count = len(shopping_list.items)
    lines.append("")
    lines.append(f"<i>{count} ingredient{'s' if count != 1 else ''}</i>")

    return _truncate_message("\n".join(lines))
