from datetime import date, timedelta

import pytest
from sqlalchemy import select

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.models.catalog import Dish
from mealroulette.models.enums import MealPlanDishLineSource
from mealroulette.models.planning import MealPlanItem
from mealroulette.schemas.planning import MealPlanDishLineCreateRequest
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler_service import SchedulerService

pytestmark = pytest.mark.integration


def _seed_dishes(db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)


def _future_week_start(planning: PlanningService, *, days_ahead: int = 7) -> date:
    return planning.week_start_for(date.today() + timedelta(days=days_ahead))


def test_generate_week_creates_roulette_lines(db_session, catalog_seed, scheduler_seed):
    _seed_dishes(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)

    service = SchedulerService(db_session)
    service.generate_week(plan.id, today=reference_today)

    items = db_session.scalars(select(MealPlanItem).where(MealPlanItem.meal_plan_id == plan.id)).all()
    assigned = [item for item in items if item.dish_id is not None]
    assert len(assigned) == 14
    assert all(item.lines for item in assigned)
    assert all(
        any(line.source == MealPlanDishLineSource.roulette for line in item.lines)
        for item in assigned
    )


def test_reroll_preserves_manual_lines(db_session, catalog_seed, scheduler_seed):
    _seed_dishes(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)

    service = SchedulerService(db_session)
    service.generate_week(plan.id, today=reference_today)

    target_item = next(item for item in plan.items if item.date >= reference_today)
    db_session.refresh(target_item)
    manual_dish = db_session.scalar(select(Dish).where(Dish.name == "Mushroom Risotto"))
    assert manual_dish is not None

    planning.add_line(target_item.id, MealPlanDishLineCreateRequest(dish_id=manual_dish.id))
    db_session.commit()
    db_session.refresh(target_item)
    manual_line = next(line for line in target_item.lines if line.source == MealPlanDishLineSource.manual)
    manual_dish_id = manual_line.dish_id

    service.reroll_item(target_item.id, today=reference_today)
    db_session.refresh(target_item)

    assert any(line.dish_id == manual_dish_id and line.source == MealPlanDishLineSource.manual for line in target_item.lines)
    assert any(line.source == MealPlanDishLineSource.roulette for line in target_item.lines)
