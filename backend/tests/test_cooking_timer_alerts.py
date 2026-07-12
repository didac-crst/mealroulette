import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from mealroulette.models.cooking import CookingTimerAlert, CookingTimerAlertStatus
from mealroulette.schemas.cooking import CookingTimerAlertCreateRequest
from mealroulette.services.cooking_timer_alerts import CookingTimerAlertService

pytestmark = pytest.mark.integration


def _create_dish_with_timed_step(client, admin_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Timer Test Dish", "course": "main", "status": "active"},
    ).json()
    recipe = client.post(
        f"/api/dishes/{dish['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Quick test", "recipe_type": "standard", "is_main": True},
    ).json()
    step = client.post(
        f"/api/recipes/{recipe['id']}/steps",
        headers=admin_headers,
        json={"step_number": 1, "instruction": "Wait ten seconds.", "timer_seconds": 10},
    ).json()
    return dish, recipe, step


def test_schedule_and_cancel_cooking_timer_alert(client, catalog_seed, admin_headers, user_headers):
    dish, recipe, step = _create_dish_with_timed_step(client, admin_headers)
    response = client.post(
        "/api/cooking-timer-alerts",
        headers=user_headers,
        json={
            "recipe_id": recipe["id"],
            "recipe_step_id": step["id"],
            "step_number": 1,
            "remaining_seconds": 10,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dish_name"] == dish["name"]
    assert body["status"] == "pending"

    alert_id = body["id"]
    cancel = client.delete(f"/api/cooking-timer-alerts/{alert_id}", headers=user_headers)
    assert cancel.status_code == 200
    assert cancel.json()["cancelled"] is True


def test_process_due_sends_telegram(db_session, catalog_seed, client, admin_headers, admin_user):
    _, recipe, step = _create_dish_with_timed_step(client, admin_headers)
    from mealroulette.models.telegram import TelegramSubscriber

    db_session.add(TelegramSubscriber(chat_id="12345", telegram_user_id="99"))
    db_session.commit()

    mock_client = MagicMock()
    service = CookingTimerAlertService(db_session, client=mock_client)
    alert = service.schedule(
        admin_user,
        CookingTimerAlertCreateRequest(
            recipe_id=recipe["id"],
            recipe_step_id=step["id"],
            step_number=1,
            remaining_seconds=5,
        ),
    )
    row = db_session.get(CookingTimerAlert, alert.id)
    assert row is not None
    row.fire_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    processed = service.process_due()
    assert processed == 1
    mock_client.send_message.assert_called_once()
    assert row.status == CookingTimerAlertStatus.sent.value
