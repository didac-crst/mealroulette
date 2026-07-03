from datetime import date
from decimal import Decimal

from mealroulette.models.enums import MealSlot, ShoppingListStatus
from mealroulette.schemas.shopping import ShoppingListItemPublic, ShoppingListPublic, ShoppingPlannedMeal
from mealroulette.services.telegram_format import format_shopping_list_message, reminder_window_from_date


def test_reminder_window_include_today():
    assert reminder_window_from_date(date(2026, 7, 3), include_today=True) == date(2026, 7, 3)


def test_reminder_window_starts_tomorrow():
    assert reminder_window_from_date(date(2026, 7, 3), include_today=False) == date(2026, 7, 4)


def test_format_shopping_list_message_groups_categories_and_planned_meals():
    shopping_list = ShoppingListPublic(
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        status=ShoppingListStatus.active,
        exclude_pantry=True,
        items=[
            ShoppingListItemPublic(
                id=1,
                ingredient_id=1,
                display_name="Carrot",
                quantity=Decimal("2"),
                unit_id=1,
                unit_symbol="unit",
                category="vegetable",
            ),
            ShoppingListItemPublic(
                id=2,
                ingredient_id=2,
                display_name="Chicken",
                quantity=Decimal("400"),
                unit_id=2,
                unit_symbol="g",
                category="protein",
            ),
        ],
        planned_meals=[
            ShoppingPlannedMeal(
                meal_plan_item_id=10,
                date=date(2026, 7, 3),
                meal_slot=MealSlot.lunch,
                dish_name="Carrot soup",
            )
        ],
    )

    message = format_shopping_list_message(shopping_list)

    assert "MealRoulette reminder" in message
    assert "Vegetable" in message
    assert "- 2 unit Carrot" in message
    assert "Protein" in message
    assert "- 400 g Chicken" in message
    assert "Planned meals:" in message
    assert "Carrot soup" in message
