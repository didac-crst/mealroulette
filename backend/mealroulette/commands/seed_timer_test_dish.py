"""Create the Timer Test Dish in the catalog if it is missing."""

from __future__ import annotations

import argparse

from sqlalchemy import func, select

from mealroulette.db.session import SessionLocal
from mealroulette.models.catalog import Dish
from mealroulette.models.enums import DifficultyLevel, DishCourse, DishStatus, RecipeType
from mealroulette.schemas.catalog import DishCreateRequest, RecipeCreateRequest, RecipeStepCreateRequest
from mealroulette.services.catalog import CatalogService

DISH_NAME = "Timer Test Dish"


def seed_timer_test_dish() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(Dish).where(func.lower(Dish.name) == DISH_NAME.lower()))
        if existing is not None:
            print(f"{DISH_NAME} already exists (id={existing.id})")
            return

        service = CatalogService(db)
        dish = service.create_dish(
            DishCreateRequest(
                name=DISH_NAME,
                description="Dummy recipe for testing cooking timers and Telegram alerts (10 second step).",
                course=DishCourse.main,
                status=DishStatus.active,
                suitable_for_lunch=True,
                suitable_for_dinner=True,
                weekday_friendly=True,
            )
        )
        recipe = service.create_recipe(
            dish.id,
            RecipeCreateRequest(
                variant_name="Quick test",
                description="Start the timer and wait 10 seconds to test Telegram cooking alerts.",
                recipe_type=RecipeType.standard,
                is_main=True,
                servings=1,
                prep_time_minutes=0,
                cook_time_minutes=1,
                difficulty=DifficultyLevel.easy,
            ),
        )
        service.create_step(
            recipe.id,
            RecipeStepCreateRequest(
                step_number=1,
                instruction=(
                    "Wait ten seconds. When the timer finishes, subscribed Telegram chats "
                    "should receive an alert."
                ),
                timer_seconds=10,
            ),
        )
        print(f"Created {DISH_NAME} (dish_id={dish.id}, recipe_id={recipe.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Timer Test Dish for cooking timer QA")
    parser.parse_args()
    seed_timer_test_dish()


if __name__ == "__main__":
    main()
