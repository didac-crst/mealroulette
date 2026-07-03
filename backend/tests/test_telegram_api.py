import pytest

from mealroulette.services.telegram_subscribers import TelegramSubscriberService


@pytest.mark.integration
def test_telegram_settings_admin_only(client, catalog_seed, user_headers):
    response = client.get("/api/telegram/settings", headers=user_headers)
    assert response.status_code == 403


@pytest.mark.integration
def test_telegram_settings_and_subscribers(client, catalog_seed, admin_headers, db_session):
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

    TelegramSubscriberService(db_session).subscribe(chat_id="42", username="tester")

    subs = client.get("/api/telegram/subscribers", headers=admin_headers)
    assert subs.status_code == 200
    assert len(subs.json()) == 1
    assert subs.json()[0]["chat_id"] == "42"

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
