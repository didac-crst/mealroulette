from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, RecipeStep, Unit
from mealroulette.models.enums import DifficultyLevel, DishCourse, DishStatus, MealPlanItemStatus, MealSlot, RecipeType
from mealroulette.schemas.planning import MealPlanItemPublic
from mealroulette.services.telegram_format_html import format_planning_message_html
from mealroulette.services.telegram_recipe import (
    format_recipe_message_html,
    load_recipe_detail,
    parse_recipe_start_payload,
    recipe_deep_link,
)
from mealroulette.services.telegram_updates import TelegramUpdateService


def test_parse_recipe_start_payload():
    assert parse_recipe_start_payload("recipe_12") == 12
    assert parse_recipe_start_payload("RECIPE_7") == 7
    assert parse_recipe_start_payload("subscribe") is None


def test_format_planning_message_html_links_assigned_recipes():
    items = [
        MealPlanItemPublic(
            id=1,
            meal_plan_id=1,
            date=datetime(2026, 7, 3).date(),
            meal_slot=MealSlot.lunch,
            dish_id=1,
            recipe_id=42,
            dish_name="Carrot soup",
            recipe_variant_name="main",
            prep_time_minutes=10,
            cook_time_minutes=25,
            status=MealPlanItemStatus.planned,
            is_locked=False,
            manually_selected=False,
            skip_reason=None,
            skip_comment=None,
            leftover_source_item_id=None,
            selection_reasons_json=None,
            review_saved_at=None,
            created_at=datetime(2026, 7, 1),
            updated_at=datetime(2026, 7, 1),
        ),
    ]

    message = format_planning_message_html(
        items,
        from_date=datetime(2026, 7, 3).date(),
        to_date=datetime(2026, 7, 5).date(),
        days=3,
        bot_username="mealroulette_bot",
    )

    assert recipe_deep_link("mealroulette_bot", 42) in message
    assert '<a href="https://t.me/mealroulette_bot?start=recipe_42">' in message
    assert "Carrot soup (main)" in message


@pytest.mark.integration
def test_format_recipe_message_html_from_catalog(db_session, catalog_seed):
    dish = Dish(name="Telegram Soup", course=DishCourse.main, status=DishStatus.active)
    db_session.add(dish)
    db_session.flush()

    unit = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    ingredient = Ingredient(
        canonical_name="telegram_carrot",
        display_name="Carrot",
        category="vegetable",
    )
    db_session.add(ingredient)
    db_session.flush()

    recipe = Recipe(
        dish_id=dish.id,
        variant_name="main",
        recipe_type=RecipeType.standard,
        is_main=True,
        servings=2,
        prep_time_minutes=5,
        cook_time_minutes=15,
        difficulty=DifficultyLevel.easy,
        description="A test soup.",
    )
    db_session.add(recipe)
    db_session.flush()

    db_session.add(
        RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=Decimal("200"),
            unit_id=unit.id,
        )
    )
    db_session.add(
        RecipeStep(
            recipe_id=recipe.id,
            step_number=1,
            instruction="Chop the carrots.",
            timer_seconds=300,
        )
    )
    db_session.commit()

    detail = load_recipe_detail(db_session, recipe.id)
    assert detail is not None
    message = format_recipe_message_html(detail)

    assert "<b>Telegram Soup</b>" in message
    assert "<b>Ingredients</b>" in message
    assert "<b>Carrot — 200 g</b>" in message
    assert "<b>Steps</b>" in message
    assert "<b>1.</b> Chop the carrots." in message
    assert "5 min timer" in message


@pytest.mark.integration
def test_start_recipe_link_sends_html_recipe(db_session, catalog_seed, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "mealroulette_bot")

    dish = Dish(name="Link Soup", course=DishCourse.main, status=DishStatus.active)
    db_session.add(dish)
    db_session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        variant_name="main",
        recipe_type=RecipeType.standard,
        is_main=True,
    )
    db_session.add(recipe)
    db_session.flush()
    db_session.add(
        RecipeStep(
            recipe_id=recipe.id,
            step_number=1,
            instruction="Simmer.",
        )
    )
    db_session.commit()

    client = MagicMock()
    update_service = TelegramUpdateService(db_session, client=client)

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 20,
            "message": {
                "text": f"/start recipe_{recipe.id}",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )

    assert handled is True
    call = client.send_message.call_args
    assert call.kwargs.get("parse_mode") == "HTML"
    message = call.args[2]
    assert "<b>Ingredients</b>" in message
    assert "<b>Steps</b>" in message
