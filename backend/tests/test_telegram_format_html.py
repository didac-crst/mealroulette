from datetime import date, datetime
from decimal import Decimal

from mealroulette.models.enums import MealPlanItemStatus, MealSlot, ShoppingListStatus
from mealroulette.schemas.planning import MealPlanItemPublic
from mealroulette.schemas.shopping import (
    ShoppingListItemPublic,
    ShoppingListPublic,
    ShoppingQuantityComponent,
    ShoppingSourceContribution,
)
from mealroulette.services.telegram_format_html import (
    format_planning_message_html,
    format_reminder_message_html,
    format_shopping_message_html,
)
from mealroulette.services.telegram_on_demand import parse_days_arg


def test_parse_days_arg_defaults_and_validates():
    assert parse_days_arg([]) == 3
    assert parse_days_arg(["7"]) == 7
    assert parse_days_arg(["0"]) is None
    assert parse_days_arg(["99"]) is None
    assert parse_days_arg(["abc"]) is None


def test_format_planning_message_html_groups_by_day():
    items = [
        MealPlanItemPublic(
            id=1,
            meal_plan_id=1,
            date=date(2026, 7, 3),
            meal_slot=MealSlot.lunch,
            dish_id=1,
            recipe_id=1,
            dish_name="Carrot soup",
            recipe_variant_name="main",
            prep_time_minutes=10,
            cook_time_minutes=25,
            status=MealPlanItemStatus.planned,
            is_locked=True,
            manually_selected=False,
            skip_reason=None,
            skip_comment=None,
            leftover_source_item_id=None,
            selection_reasons_json=None,
            review_saved_at=None,
            created_at=datetime(2026, 7, 1),
            updated_at=datetime(2026, 7, 1),
        ),
        MealPlanItemPublic(
            id=2,
            meal_plan_id=1,
            date=date(2026, 7, 3),
            meal_slot=MealSlot.dinner,
            dish_id=None,
            recipe_id=None,
            dish_name=None,
            recipe_variant_name=None,
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
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        days=3,
        bot_username="mealroulette_bot",
    )

    assert "<b>Planning</b>" in message
    assert "  <i>Friday, Jul 3" in message or "  <i>" in message
    assert "<b>Friday, Jul 3</b>" in message
    assert '<a href="https://t.me/mealroulette_bot?start=recipe_1">' in message
    assert "Carrot soup (main)" in message
    assert "  • <b>Lunch</b>: " in message
    assert "10 / 25 min" in message
    assert "Planned" not in message
    assert "locked" not in message
    assert "  • <b>Dinner</b>: <i>Not assigned</i>" in message


def test_format_reminder_message_html_uses_planning_then_ingredients():
    planning_items = [
        MealPlanItemPublic(
            id=1,
            meal_plan_id=1,
            date=date(2026, 7, 3),
            meal_slot=MealSlot.lunch,
            dish_id=1,
            recipe_id=1,
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
    shopping_list = ShoppingListPublic(
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        status=ShoppingListStatus.active,
        exclude_pantry=False,
        items=[
            ShoppingListItemPublic(
                id=1,
                ingredient_id=1,
                display_name="Carrot",
                quantity=Decimal("2"),
                unit_id=1,
                unit_symbol="unit",
                category="vegetable",
                approximate=True,
                raw_components=[
                    ShoppingQuantityComponent(
                        quantity=Decimal("700"),
                        unit_id=2,
                        unit_symbol="g",
                    ),
                    ShoppingQuantityComponent(
                        quantity=Decimal("2"),
                        unit_id=1,
                        unit_symbol="unit",
                    ),
                ],
                source_contributions=[
                    ShoppingSourceContribution(
                        meal_plan_item_id=10,
                        date=date(2026, 7, 3),
                        meal_slot=MealSlot.lunch,
                        dish_name="Carrot soup",
                        recipe_variant_name="main",
                        quantity=Decimal("1"),
                        unit_symbol="unit",
                    ),
                    ShoppingSourceContribution(
                        meal_plan_item_id=11,
                        date=date(2026, 7, 4),
                        meal_slot=MealSlot.dinner,
                        dish_name="Garden salad",
                        quantity=Decimal("1"),
                        unit_symbol="unit",
                    ),
                ],
            ),
        ],
    )

    message = format_reminder_message_html(
        shopping_list,
        planning_items,
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        days=3,
    )

    assert "<b>Reminder</b>" in message
    assert "  • <b>Lunch</b>: Carrot soup (main)" in message
    assert "<b>Ingredients list:</b>" in message
    assert "<b>Carrot — ~2 unit</b>" in message
    assert "includes: 700 g + 2 unit" in message
    assert "↳ Carrot soup — 1 unit" in message
    assert "↳ Garden salad — 1 unit" in message
    assert "(main)" not in message.split("<b>Ingredients list:</b>")[1]
    assert "<b>vegetable</b>" not in message
    assert "Planned meals in window" not in message


def test_truncate_message_closes_unclosed_html_tags():
    from mealroulette.services.telegram_html_utils import truncate_message

    long_message = "<b>Title</b>\n" + ("  • <i>line with open tag\n" * 500)
    truncated = truncate_message(long_message)
    assert truncated.endswith("… (message truncated)")
    assert truncated.count("<i>") == truncated.count("</i>")


def test_truncate_message_closes_unclosed_anchor_tags():
    from mealroulette.services.telegram_html_utils import close_unclosed_html_tags, truncate_message

    assert close_unclosed_html_tags('<a href="https://example.com">link') == (
        '<a href="https://example.com">link</a>'
    )
    long_message = '<a href="https://example.com/recipe/1">Dish name</a>\n' + ("x" * 5000)
    truncated = truncate_message(long_message)
    assert truncated.count("<a") == truncated.count("</a>")


def test_format_shopping_message_html_totals_only_by_category():
    shopping_list = ShoppingListPublic(
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        exclude_pantry=False,
        items=[
            ShoppingListItemPublic(
                id=1,
                ingredient_id=1,
                display_name="Carrot",
                quantity=Decimal("2"),
                unit_id=1,
                unit_symbol="unit",
                category="vegetable",
                source_contributions=[
                    ShoppingSourceContribution(
                        meal_plan_item_id=10,
                        date=date(2026, 7, 3),
                        meal_slot=MealSlot.lunch,
                        dish_name="Carrot soup",
                        quantity=Decimal("1"),
                        unit_symbol="unit",
                    ),
                ],
            ),
            ShoppingListItemPublic(
                id=2,
                ingredient_id=2,
                display_name="Milk",
                quantity=Decimal("1"),
                unit_id=3,
                unit_symbol="L",
                category="dairy",
            ),
        ],
    )

    message = format_shopping_message_html(
        shopping_list,
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        days=3,
    )

    assert "<b>Shopping</b>" in message
    assert "Shopping list::" not in message
    assert "general" not in message.lower()
    assert "<b>Vegetable</b>" in message
    assert "<b>Dairy</b>" in message
    assert "<b>Carrot — 2 unit</b>" in message
    assert "<b>Milk — 1 L</b>" in message
    assert "↳" not in message
    assert "2 ingredients" in message


def test_format_shopping_message_html_omits_header_for_uncategorized():
    shopping_list = ShoppingListPublic(
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        exclude_pantry=False,
        items=[
            ShoppingListItemPublic(
                id=1,
                ingredient_id=1,
                display_name="Salt",
                quantity=Decimal("1"),
                unit_id=1,
                unit_symbol="pinch",
                category="Other",
            ),
        ],
    )

    message = format_shopping_message_html(
        shopping_list,
        from_date=date(2026, 7, 3),
        to_date=date(2026, 7, 5),
        days=3,
    )

    assert "<b>Salt — 1 pinch</b>" in message
    assert "Other" not in message
    assert "general" not in message.lower()
