import hashlib
import re
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from mealroulette.models.telegram import TelegramLoginOtp, TelegramUserLink
from mealroulette.services.telegram_otp import TelegramOtpService, _hash_code

pytestmark = pytest.mark.integration

TEST_SECRET = "test-secret-key-for-hs256-at-least-32-bytes"


def _settings_mock(**overrides):
    defaults = {
        "telegram_bot_token": "test-bot-token",
        "secret_key": TEST_SECRET,
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


def _link_admin(db_session, admin_user):
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="4242",
            username="admin_tg",
        )
    )
    db_session.commit()


def _patch_otp(monkeypatch, mock_client):
    monkeypatch.setattr(
        "mealroulette.api.routes.auth.TelegramOtpService",
        lambda db: TelegramOtpService(db, client=mock_client),
    )
    monkeypatch.setattr(
        "mealroulette.services.telegram_otp.get_settings",
        lambda: _settings_mock(),
    )


def test_otp_hash_uses_hmac_not_plain_sha256(monkeypatch):
    monkeypatch.setattr(
        "mealroulette.services.telegram_otp.get_settings",
        lambda: _settings_mock(),
    )
    code = "123456"
    hmac_digest = _hash_code(code)
    plain = hashlib.sha256(code.encode("utf-8")).hexdigest()
    assert hmac_digest != plain
    assert len(hmac_digest) == 64


def test_telegram_otp_login_round_trip(client, admin_user, db_session, monkeypatch):
    _link_admin(db_session, admin_user)
    mock_client = MagicMock()
    _patch_otp(monkeypatch, mock_client)

    requested = client.post("/api/auth/telegram-otp/request", json={"username": "admin"})
    assert requested.status_code == 202
    assert "telegram" in requested.json()["detail"].lower()
    mock_client.send_message.assert_called_once()
    message = mock_client.send_message.call_args.args[2]

    match = re.search(r"<code>(\d{6})</code>", message)
    assert match is not None
    code = match.group(1)

    verified = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": code},
    )
    assert verified.status_code == 200
    assert "access_token" in verified.json()

    row = db_session.scalar(select(TelegramLoginOtp).where(TelegramLoginOtp.user_id == admin_user.id))
    assert row is not None
    assert row.used_at is not None

    reused = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": code},
    )
    assert reused.status_code == 401
    assert reused.json()["error"]["message"] == "Invalid username or code"


def test_telegram_otp_request_is_generic_for_unknown_user(client):
    response = client.post("/api/auth/telegram-otp/request", json={"username": "nobody"})
    assert response.status_code == 202
    assert "if that account exists" in response.json()["detail"].lower()


def test_telegram_otp_cooldown_skips_resend(client, admin_user, db_session, monkeypatch):
    _link_admin(db_session, admin_user)
    mock_client = MagicMock()
    _patch_otp(monkeypatch, mock_client)

    first = client.post("/api/auth/telegram-otp/request", json={"username": "admin"})
    assert first.status_code == 202
    mock_client.send_message.assert_called_once()
    first_code = re.search(r"<code>(\d{6})</code>", mock_client.send_message.call_args.args[2]).group(1)

    otp_before = db_session.scalar(select(TelegramLoginOtp).where(TelegramLoginOtp.user_id == admin_user.id))
    assert otp_before is not None
    hash_before = otp_before.code_hash
    created_before = otp_before.created_at

    second = client.post("/api/auth/telegram-otp/request", json={"username": "admin"})
    assert second.status_code == 202
    assert mock_client.send_message.call_count == 1

    db_session.refresh(otp_before)
    assert otp_before.code_hash == hash_before
    assert otp_before.created_at == created_before

    verified = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": first_code},
    )
    assert verified.status_code == 200


def test_telegram_otp_verify_consumes_atomically(client, admin_user, db_session, monkeypatch):
    _link_admin(db_session, admin_user)
    mock_client = MagicMock()
    _patch_otp(monkeypatch, mock_client)

    client.post("/api/auth/telegram-otp/request", json={"username": "admin"})
    code = re.search(r"<code>(\d{6})</code>", mock_client.send_message.call_args.args[2]).group(1)

    ok = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": code},
    )
    assert ok.status_code == 200

    row = db_session.scalar(select(TelegramLoginOtp).where(TelegramLoginOtp.user_id == admin_user.id))
    assert row is not None
    assert row.used_at is not None

    again = client.post(
        "/api/auth/telegram-otp/verify",
        json={"username": "admin", "code": code},
    )
    assert again.status_code == 401
