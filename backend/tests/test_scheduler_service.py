from datetime import date, timedelta

import pytest
from sqlalchemy import select

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.models.catalog import Dish
from mealroulette.models.enums import MealPlanItemStatus, MealSlot
from mealroulette.models.planning import MealPlanItem
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler.reroll_memory import load_reroll_history
from mealroulette.services.scheduler_service import SchedulerService

pytestmark = pytest.mark.integration


def _seed_dishes(db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)


def _future_week_start(planning: PlanningService, *, days_ahead: int = 7) -> date:
    return planning.week_start_for(date.today() + timedelta(days=days_ahead))


def test_generate_week_fills_future_plan(db_session, catalog_seed, scheduler_seed):
    _seed_dishes(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)

    service = SchedulerService(db_session)
    result, variety = service.generate_week(plan.id, today=reference_today)

    assert len(result.assignments) == 14
    dish_ids = [assignment.dish_id for assignment in result.assignments]
    assert len(dish_ids) == len(set(dish_ids))

    items = db_session.scalars(select(MealPlanItem).where(MealPlanItem.meal_plan_id == plan.id)).all()
    assigned = [item for item in items if item.dish_id is not None]
    assert len(assigned) == 14
    assert all(item.selection_reasons_json for item in assigned)
    assert len(variety["items"]) == 14
    db_session.refresh(plan)
    assert plan.last_roulette_undo_json is not None


def test_generate_week_preserves_locked_slots(db_session, catalog_seed, scheduler_seed):
    _seed_dishes(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)

    locked_item = next(
        item
        for item in plan.items
        if item.date >= reference_today and item.meal_slot == MealSlot.lunch
    )
    locked_dish = db_session.scalar(select(Dish).limit(1))
    locked_item.dish_id = locked_dish.id
    locked_item.recipe_id = locked_dish.recipes[0].id
    locked_item.is_locked = True
    locked_item.manually_selected = True
    db_session.commit()

    service = SchedulerService(db_session)
    result, _ = service.generate_week(plan.id, today=reference_today)

    db_session.refresh(locked_item)
    assert locked_item.dish_id == locked_dish.id
    assert locked_item.is_locked is True
    assert len(result.assignments) == 13


def test_reroll_and_undo_restore_previous_assignment(db_session, catalog_seed, scheduler_seed):
    _seed_dishes(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = _future_week_start(planning)
    plan = planning.get_or_create_plan(week_start)

    service = SchedulerService(db_session)
    service.generate_week(plan.id, today=reference_today)

    target_item = next(item for item in plan.items if item.date >= reference_today)
    db_session.refresh(target_item)
    previous_dish_id = target_item.dish_id
    previous_recipe_id = target_item.recipe_id
    assert previous_dish_id is not None

    service.reroll_item(target_item.id, today=reference_today)
    db_session.refresh(target_item)
    assert target_item.dish_id is not None
    assert target_item.dish_id != previous_dish_id
    assert len(load_reroll_history(target_item)) == 1

    service.undo_last_roulette(plan.id)
    db_session.refresh(target_item)
    assert target_item.dish_id == previous_dish_id
    assert target_item.recipe_id == previous_recipe_id
    assert len(load_reroll_history(target_item)) == 0

    with pytest.raises(Exception) as exc_info:
        service.undo_last_roulette(plan.id)
    assert exc_info.value.status_code == 400


def test_reroll_rejected_for_past_slot(db_session, catalog_seed, scheduler_seed):
    _seed_dishes(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = planning.week_start_for(reference_today - timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)
    past_item = next(item for item in plan.items if item.date < reference_today)

    service = SchedulerService(db_session)
    with pytest.raises(Exception) as exc_info:
        service.reroll_item(past_item.id, today=reference_today)
    assert exc_info.value.status_code == 400
