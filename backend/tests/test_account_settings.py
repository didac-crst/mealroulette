from uuid import uuid4

import pytest

from mealroulette.models.telegram import TelegramUserLink
from mealroulette.services.telegram_link import TelegramLinkService

pytestmark = pytest.mark.integration


def test_change_password_requires_current_password(client, admin_token):
    bad = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"current_password": "wrongpassword", "new_password": "brandnewpass"},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"current_password": "adminpassword", "new_password": "brandnewpass"},
    )
    assert ok.status_code == 204

    login = client.post("/api/auth/login", json={"username": "admin", "password": "brandnewpass"})
    assert login.status_code == 200


def test_telegram_chat_can_link_multiple_users(db_session, admin_user, regular_user):
    service = TelegramLinkService(db_session)
    chat_id = "123456789"

    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id=chat_id,
            username="chef",
            display_name="Chef",
        )
    )
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=regular_user.id,
            chat_id=chat_id,
            username="chef",
            display_name="Chef",
        )
    )
    db_session.commit()

    assert service.get_link_for_user(admin_user.id) is not None
    assert service.get_link_for_user(regular_user.id) is not None
    assert service.get_link_for_user(admin_user.id).chat_id == chat_id
    assert service.get_link_for_user(regular_user.id).chat_id == chat_id


def test_telegram_link_status_and_unlink(client, admin_token, admin_user, db_session):
    status = client.get("/api/household/telegram/link", headers={"Authorization": f"Bearer {admin_token}"})
    assert status.status_code == 200
    assert status.json()["linked"] is False

    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="987654321",
            username="admin_tg",
            display_name="Admin TG",
        )
    )
    db_session.commit()

    linked = client.get("/api/household/telegram/link", headers={"Authorization": f"Bearer {admin_token}"})
    assert linked.status_code == 200
    body = linked.json()
    assert body["linked"] is True
    assert body["username"] == "admin_tg"

    unlink = client.delete("/api/household/telegram/link", headers={"Authorization": f"Bearer {admin_token}"})
    assert unlink.status_code == 204

    after = client.get("/api/household/telegram/link", headers={"Authorization": f"Bearer {admin_token}"})
    assert after.json()["linked"] is False
