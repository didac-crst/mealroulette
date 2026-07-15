"""Legacy nullable meal_reviews.user_id semantics (ADR 003)."""

from datetime import date

import pytest

from mealroulette.models.catalog import Dish, DishStatus, Recipe
from mealroulette.models.enums import MealPlanItemStatus, MealSlot
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.planning import MealPlan, MealPlanItem, MealReview
from mealroulette.services.planning import PlanningService
from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key
from mealroulette.services.scheduler.catalog import load_average_ratings

pytestmark = pytest.mark.integration


def test_null_user_meal_review_is_not_attributed_but_counts_in_averages(
    db_session,
    catalog_seed,
    default_household,
    regular_user,
):
    dish = Dish(
        name="Legacy Rated Stew",
        status=DishStatus.active,
        household_id=DEFAULT_HOUSEHOLD_ID,
        public_key=generate_dish_public_key("Legacy Rated Stew"),
    )
    db_session.add(dish)
    db_session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        variant_name="Main",
        is_main=True,
        public_key=generate_recipe_public_key(dish.public_key, 1),
        sequence_number=1,
    )
    db_session.add(recipe)
    db_session.flush()

    plan = MealPlan(household_id=DEFAULT_HOUSEHOLD_ID, week_start_date=date(2026, 7, 13))
    db_session.add(plan)
    db_session.flush()
    item = MealPlanItem(
        meal_plan_id=plan.id,
        date=plan.week_start_date,
        meal_slot=MealSlot.lunch,
        status=MealPlanItemStatus.eaten,
        dish_id=dish.id,
        recipe_id=recipe.id,
    )
    db_session.add(item)
    db_session.flush()

    db_session.add(
        MealReview(
            household_id=DEFAULT_HOUSEHOLD_ID,
            meal_plan_item_id=item.id,
            user_id=None,
            dish_id=dish.id,
            recipe_id=recipe.id,
            rating=5,
            comment="pre-tenancy anonymous review",
        )
    )
    db_session.commit()

    planning = PlanningService(db_session, DEFAULT_HOUSEHOLD_ID)
    assert planning.get_meal_rating(item.id, user_id=regular_user.id) is None

    averages = load_average_ratings(db_session, household_id=DEFAULT_HOUSEHOLD_ID)
    assert dish.id in averages
    assert averages[dish.id] == pytest.approx(5.0)
