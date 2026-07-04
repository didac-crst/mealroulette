"""Phase 8 acceptance criteria — API-level checks (see CURSOR_ROADMAP § Phase 8)."""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.models.catalog import Dish
from mealroulette.models.enums import MealSlot
from mealroulette.services.planning import PlanningService

pytestmark = pytest.mark.integration


def _seed(db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)


def test_generate_preserves_locked_slot_api(client, catalog_seed, scheduler_seed, user_headers, db_session):
    _seed(db_session)
    planning = PlanningService(db_session)
    reference_today = date(2026, 7, 1)
    week_start = planning.week_start_for(reference_today + timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)

    locked_item = next(
        item
        for item in plan.items
        if item.date > reference_today and item.meal_slot == MealSlot.lunch
    )
    locked_dish = db_session.scalar(select(Dish).limit(1))
    locked_item.dish_id = locked_dish.id
    locked_item.recipe_id = locked_dish.recipes[0].id
    locked_item.is_locked = True
    locked_item.manually_selected = True
    db_session.commit()

    response = client.post(f"/api/meal-plans/{plan.id}/generate", headers=user_headers)
    assert response.status_code == 200

    refreshed = client.get(f"/api/meal-plans/{week_start.isoformat()}", headers=user_headers)
    saved = next(item for item in refreshed.json()["items"] if item["id"] == locked_item.id)
    assert saved["dish_id"] == locked_dish.id
    assert saved["is_locked"] is True


def test_manually_assigned_slot_skipped_on_generate_api(
    client, catalog_seed, scheduler_seed, user_headers, db_session
):
    _seed(db_session)
    planning = PlanningService(db_session)
    reference_today = date(2026, 7, 1)
    week_start = planning.week_start_for(reference_today + timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)
    target_item = next(
        item for item in plan.items if item.date > reference_today and item.meal_slot == MealSlot.dinner
    )
    dish = db_session.scalar(select(Dish).offset(1).limit(1))

    assign = client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": target_item.date.isoformat(),
            "meal_slot": "dinner",
            "dish_id": dish.id,
        },
    )
    assert assign.status_code == 200
    manual_dish_id = assign.json()["dish_id"]

    generate = client.post(f"/api/meal-plans/{plan.id}/generate", headers=user_headers)
    assert generate.status_code == 200

    refreshed = client.get(f"/api/meal-plans/{week_start.isoformat()}", headers=user_headers)
    saved = next(item for item in refreshed.json()["items"] if item["id"] == target_item.id)
    assert saved["dish_id"] == manual_dish_id
    assert saved["manually_selected"] is True


def test_reroll_blocked_for_past_date_api(client, catalog_seed, scheduler_seed, user_headers, db_session):
    _seed(db_session)
    planning = PlanningService(db_session)
    reference_today = date.today()
    week_start = planning.week_start_for(reference_today - timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)
    past_items = [item for item in plan.items if item.date < reference_today]
    assert past_items, "expected a past slot in the previous week"
    past_item = past_items[0]

    response = client.post(f"/api/meal-plan-items/{past_item.id}/reroll", headers=user_headers)
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "This meal slot cannot be rerolled"


def test_auto_assignments_include_selection_reasons_api(
    client, catalog_seed, scheduler_seed, user_headers, db_session
):
    _seed(db_session)
    planning = PlanningService(db_session)
    week_start = planning.week_start_for(date(2026, 7, 1) + timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)

    response = client.post(f"/api/meal-plans/{plan.id}/generate", headers=user_headers)
    assert response.status_code == 200

    auto_items = [
        item
        for item in response.json()["items"]
        if item["dish_id"] is not None and not item["manually_selected"]
    ]
    assert len(auto_items) == 14
    for item in auto_items:
        reasons = item["selection_reasons_json"]
        assert reasons is not None
        assert isinstance(reasons.get("reasons"), list)
        assert len(reasons["reasons"]) >= 1
        assert reasons.get("score") is not None
