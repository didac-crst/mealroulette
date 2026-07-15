from uuid import uuid4

import pytest

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, HouseholdNotificationSubscription
from mealroulette.models.telegram import TelegramUserLink


@pytest.mark.integration
def test_telegram_settings_admin_only(client, catalog_seed, user_headers):
    response = client.get("/api/telegram/settings", headers=user_headers)
    assert response.status_code == 403


@pytest.mark.integration
def test_telegram_settings_and_send_test(client, catalog_seed, admin_headers, admin_user, db_session):
    empty = client.get("/api/telegram/settings", headers=admin_headers)
    assert empty.status_code == 200
    assert empty.json()["enabled"] is False
    assert empty.json()["has_bot_token"] is True
    assert empty.json()["subscriber_count"] == 0

    updated = client.put(
        "/api/telegram/settings",
        headers=admin_headers,
        json={
            "enabled": True,
            "shopping_window_days": 3,
            "include_today": True,
            "include_pantry_items": False,
            "timezone": "Europe/Paris",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["enabled"] is True
    assert "bot_token" not in body
    assert "chat_id" not in body

    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="42",
            username="tester",
        )
    )
    existing = (
        db_session.query(HouseholdNotificationSubscription)
        .filter_by(user_id=admin_user.id, household_id=DEFAULT_HOUSEHOLD_ID)
        .one_or_none()
    )
    if existing is None:
        db_session.add(
            HouseholdNotificationSubscription(
                id=uuid4(),
                user_id=admin_user.id,
                household_id=DEFAULT_HOUSEHOLD_ID,
                notify_daily_reminder=True,
            )
        )
    else:
        existing.notify_daily_reminder = True
    db_session.commit()

    from unittest.mock import patch

    with patch("mealroulette.services.telegram_client.httpx.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        test = client.post("/api/telegram/test", headers=admin_headers)
        assert test.status_code == 200
        assert test.json()["sent"] is True
        assert test.json()["recipient_count"] == 1
        mock_post.assert_called_once()
