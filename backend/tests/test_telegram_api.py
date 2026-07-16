from uuid import uuid4

import pytest

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.telegram import TelegramUserLink
from mealroulette.services.household_membership import HouseholdMembershipService


def _link_user(db_session, user, chat_id: str) -> None:
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=user.id,
            chat_id=chat_id,
            username="tester",
        )
    )
    HouseholdMembershipService(db_session).ensure_notification_subscription(user.id, DEFAULT_HOUSEHOLD_ID)
    db_session.commit()


@pytest.mark.integration
def test_telegram_settings_household_admin_only(client, catalog_seed, user_headers):
    response = client.get("/api/telegram/settings", headers=user_headers)
    assert response.status_code == 403


@pytest.mark.integration
def test_telegram_settings_and_linked_recipients(client, catalog_seed, admin_headers, admin_user, db_session):
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

    _link_user(db_session, admin_user, "42")

    recipients = client.get("/api/telegram/subscribers", headers=admin_headers)
    assert recipients.status_code == 200
    assert len(recipients.json()) == 1
    assert recipients.json()[0]["chat_id"] == "42"

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


@pytest.mark.integration
def test_personal_telegram_link_token_and_subscription(client, catalog_seed, user_headers, regular_user, db_session):
    token_response = client.post("/api/household/telegram/link-token", headers=user_headers)
    assert token_response.status_code == 200
    payload = token_response.json()
    assert payload["token"]
    assert payload["expires_at"]

    link_status = client.get("/api/household/telegram/link", headers=user_headers)
    assert link_status.status_code == 200
    assert link_status.json()["linked"] is False

    from mealroulette.services.telegram_link import TelegramLinkService

    TelegramLinkService(db_session).link_chat(
        payload["token"],
        chat_id="777",
        telegram_user_id="1",
        username="member",
        display_name="Member",
    )

    linked = client.get("/api/household/telegram/link", headers=user_headers)
    assert linked.status_code == 200
    assert linked.json()["linked"] is True
    assert linked.json()["username"] == "member"

    sub = client.get("/api/household/notification-subscription", headers=user_headers)
    assert sub.status_code == 200
    assert sub.json()["notify_daily_reminder"] is True

    updated = client.put(
        "/api/household/notification-subscription",
        headers=user_headers,
        json={"notify_roulette": False, "shopping_window_days": 5},
    )
    assert updated.status_code == 200
    assert updated.json()["notify_roulette"] is False
    assert updated.json()["shopping_window_days"] == 5

    unlink = client.delete("/api/household/telegram/link", headers=user_headers)
    assert unlink.status_code == 204
    assert client.get("/api/household/telegram/link", headers=user_headers).json()["linked"] is False


@pytest.mark.integration
def test_notification_subscription_rejects_explicit_null(client, catalog_seed, user_headers):
    response = client.put(
        "/api/household/notification-subscription",
        headers=user_headers,
        json={"notify_roulette": None},
    )
    assert response.status_code == 422
