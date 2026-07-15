from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from mealroulette.models.telegram import TelegramUserLink
from mealroulette.services.telegram_otp import TelegramOtpService

pytestmark = pytest.mark.integration


def test_user_public_includes_household_name(admin_user, db_session, default_household):
    from mealroulette.services.auth import UserService

    payload = UserService(db_session).to_public(admin_user)
    assert payload.active_household_id == default_household.id
    assert payload.active_household_name == default_household.name


def test_telegram_otp_login_round_trip(client, admin_user, db_session, monkeypatch):
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="4242",
            username="admin_tg",
        )
    )
    db_session.commit()

    mock_client = MagicMock()
    monkeypatch.setattr(
        "mealroulette.api.routes.auth.TelegramOtpService",
        lambda db: TelegramOtpService(db, client=mock_client),
    )

    requested = client.post("/api/auth/telegram-otp/request", json={"username": "admin"})
    assert requested.status_code == 202
    assert "telegram" in requested.json()["detail"].lower()
    mock_client.send_message.assert_called_once()
    message = mock_client.send_message.call_args.args[2]
    # Extract 6-digit code from <code>NNNNNN</code>
    import re

    match = re.search(r"<code>(\d{6})</code>", message)
    assert match is not None
    code = match.group(1)

    verified = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": code},
    )
    assert verified.status_code == 200
    assert "access_token" in verified.json()

    reused = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": code},
    )
    assert reused.status_code == 401


def test_telegram_otp_request_is_generic_for_unknown_user(client):
    response = client.post("/api/auth/telegram-otp/request", json={"username": "nobody"})
    assert response.status_code == 202
    assert "if that account exists" in response.json()["detail"].lower()
