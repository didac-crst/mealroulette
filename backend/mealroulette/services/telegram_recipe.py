from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Dish, Recipe, RecipeIngredient, RecipeStep
from mealroulette.services.telegram_format import _format_quantity
from mealroulette.services.telegram_html_utils import esc as _esc, truncate_message as _truncate_message

_RECIPE_PAYLOAD_RE = re.compile(r"^recipe_(\d+)$", re.IGNORECASE)
_INDENT = "  "


@dataclass(frozen=True)
class TelegramRecipeDetail:
    dish: Dish
    recipe: Recipe
    ingredients: list[RecipeIngredient]
    steps: list[RecipeStep]


def parse_recipe_start_payload(payload: str) -> int | None:
    match = _RECIPE_PAYLOAD_RE.match(payload.strip())
    if not match:
        return None
    return int(match.group(1))


def recipe_deep_link(bot_username: str, recipe_id: int) -> str:
    username = bot_username.strip().lstrip("@")
    return f"https://t.me/{username}?start=recipe_{recipe_id}"


def load_recipe_detail(db: Session, recipe_id: int) -> TelegramRecipeDetail | None:
    recipe = db.scalar(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.dish),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
            selectinload(Recipe.steps),
        )
    )
    if recipe is None or recipe.dish is None:
        return None

    ingredients = sorted(
        recipe.ingredients,
        key=lambda row: row.ingredient.display_name.casefold(),
    )
    steps = sorted(recipe.steps, key=lambda step: step.step_number)
    return TelegramRecipeDetail(
        dish=recipe.dish,
        recipe=recipe,
        ingredients=ingredients,
        steps=steps,
    )


def _format_meta_value(label: str, value: str) -> str:
    return f"{label} {value}"


def _format_recipe_meta(recipe: Recipe) -> str:
    parts: list[str] = []
    if recipe.prep_time_minutes is not None:
        parts.append(_format_meta_value("Prep", f"{recipe.prep_time_minutes} min"))
    if recipe.cook_time_minutes is not None:
        parts.append(_format_meta_value("Cook", f"{recipe.cook_time_minutes} min"))
    if recipe.servings is not None:
        parts.append(_format_meta_value("Serves", str(recipe.servings)))
    if recipe.difficulty:
        parts.append(_format_meta_value("Level", str(recipe.difficulty)))
    return " · ".join(parts)


def _format_ingredient_line(row: RecipeIngredient) -> str:
    name = _esc(row.ingredient.display_name)
    optional = " <i>(optional)</i>" if row.optional else ""
    notes = f" — <i>{_esc(row.notes)}</i>" if row.notes else ""
    if row.quantity is None:
        qty = ""
    else:
        unit_symbol = _esc(row.unit.symbol) if row.unit else ""
        qty = f" — {_format_quantity(row.quantity)} {unit_symbol}".rstrip()
    return f"{_INDENT}• <b>{name}{qty}</b>{optional}{notes}"


def _format_step_line(step: RecipeStep) -> str:
    meta_parts: list[str] = []
    if step.timer_seconds:
        minutes = max(1, round(step.timer_seconds / 60))
        meta_parts.append(f"{minutes} min timer")
    if step.duration_seconds and not step.timer_seconds:
        minutes = max(1, round(step.duration_seconds / 60))
        meta_parts.append(f"{minutes} min")
    if step.temperature:
        meta_parts.append(step.temperature)
    meta = f" <i>({', '.join(_esc(part) for part in meta_parts)})</i>" if meta_parts else ""
    thermomix = " ⚙" if step.is_thermomix_step else ""
    instruction = _esc(step.instruction).replace("\n", f"\n{_INDENT}{_INDENT}")
    return f"<b>{step.step_number}.</b>{thermomix} {instruction}{meta}"


def format_recipe_message_html(detail: TelegramRecipeDetail) -> str:
    recipe = detail.recipe
    dish = detail.dish
    lines = [f"<b>{_esc(dish.name)}</b>"]

    if recipe.variant_name:
        lines.append(f"{_INDENT}<i>{_esc(recipe.variant_name)}</i>")

    meta = _format_recipe_meta(recipe)
    if meta:
        lines.append(f"{_INDENT}<i>{_esc(meta)}</i>")

    if recipe.description:
        lines.append("")
        lines.append(_esc(recipe.description))

    lines.append("")
    lines.append("<b>Ingredients</b>")
    if detail.ingredients:
        lines.extend(_format_ingredient_line(row) for row in detail.ingredients)
    else:
        lines.append(f"{_INDENT}<i>No ingredients listed.</i>")

    lines.append("")
    lines.append("<b>Steps</b>")
    if detail.steps:
        for step in detail.steps:
            lines.append("")
            lines.append(_format_step_line(step))
    else:
        lines.append(f"{_INDENT}<i>No steps listed.</i>")

    if recipe.notes:
        lines.append("")
        lines.append(f"<b>Notes</b>\n{_esc(recipe.notes)}")

    return _truncate_message("\n".join(lines))


def format_meal_assignment_html(
    *,
    dish_name: str,
    recipe_variant_name: str | None,
    recipe_id: int | None,
    bot_username: str | None,
) -> str:
    label = dish_name
    if recipe_variant_name:
        label = f"{dish_name} ({recipe_variant_name})"
    text = _esc(label)
    if recipe_id and bot_username:
        url = recipe_deep_link(bot_username, recipe_id)
        return f'<a href="{_esc(url, quote=True)}">{text}</a>'
    return text
