from datetime import date, timedelta

import pytest

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.services.planning import PlanningService

pytestmark = pytest.mark.integration


def _seed(db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)


def test_generate_week_api(client, catalog_seed, scheduler_seed, user_headers, db_session):
    _seed(db_session)
    planning = PlanningService(db_session)
    week_start = planning.week_start_for(date(2026, 7, 1) + timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)

    response = client.post(f"/api/meal-plans/{plan.id}/generate/details", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["assignments_count"] == 14
    assert body["can_undo"] is True
    assert len(body["variety"]["items"]) == 14


def test_reroll_and_undo_api(client, catalog_seed, scheduler_seed, user_headers, db_session):
    _seed(db_session)
    planning = PlanningService(db_session)
    reference_today = date(2026, 7, 1)
    week_start = planning.week_start_for(reference_today + timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)

    generate = client.post(f"/api/meal-plans/{plan.id}/generate", headers=user_headers)
    assert generate.status_code == 200
    plan_body = generate.json()
    target = next(item for item in plan_body["items"] if item["date"] > reference_today.isoformat())
    previous_dish_id = target["dish_id"]

    reroll = client.post(f"/api/meal-plan-items/{target['id']}/reroll", headers=user_headers)
    assert reroll.status_code == 200

    undo = client.post(f"/api/meal-plans/{plan.id}/undo-roulette", headers=user_headers)
    assert undo.status_code == 200
    assert undo.json()["restored"] is True

    refreshed = client.get(f"/api/meal-plans/{week_start.isoformat()}", headers=user_headers)
    restored_item = next(item for item in refreshed.json()["items"] if item["id"] == target["id"])
    assert restored_item["dish_id"] == previous_dish_id


def test_swap_meals_api(client, catalog_seed, user_headers, db_session):
    _seed(db_session)
    from sqlalchemy import select

    from mealroulette.models.catalog import Dish

    planning = PlanningService(db_session)
    reference_today = date(2026, 7, 1)
    week_start = planning.week_start_for(reference_today + timedelta(days=7))
    plan = planning.get_or_create_plan(week_start)

    dishes = db_session.scalars(select(Dish).limit(2)).all()
    items = sorted(
        [item for item in plan.items if item.date >= reference_today],
        key=lambda item: (item.date, item.meal_slot.value),
    )
    source = items[0]
    target = items[3]
    source.dish_id = dishes[0].id
    source.recipe_id = dishes[0].recipes[0].id
    target.dish_id = dishes[1].id
    target.recipe_id = dishes[1].recipes[0].id
    db_session.commit()

    response = client.post(
        f"/api/meal-plan-items/{source.id}/swap",
        headers=user_headers,
        json={"target_item_id": target.id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"]["dish_id"] == 2
    assert body["target"]["dish_id"] == 1
