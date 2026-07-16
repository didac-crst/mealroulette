from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.telegram import TelegramUserLink
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.telegram_link import TelegramLinkService
from mealroulette.services.telegram_updates import TelegramUpdateService


@pytest.mark.integration
def test_subscribe_and_unsubscribe_are_deprecated(db_session):
    client = MagicMock()
    update_service = TelegramUpdateService(db_session, client=client)

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 1,
            "message": {
                "text": "/subscribe",
                "chat": {"id": 4242},
                "from": {"id": 99, "username": "didac", "first_name": "Didac"},
            },
        },
    )
    assert handled is True
    assert "no longer uses /subscribe" in client.send_message.call_args[0][2].lower()

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 3,
            "message": {
                "text": "/unsubscribe",
                "chat": {"id": 4242},
                "from": {"id": 99},
            },
        },
    )
    assert handled is True
    assert "no longer uses /unsubscribe" in client.send_message.call_args[0][2].lower()


@pytest.mark.integration
def test_start_with_link_token_links_user(db_session, admin_user):
    _, raw_token = TelegramLinkService(db_session).create_link_token(admin_user.id)
    client = MagicMock()
    update_service = TelegramUpdateService(db_session, client=client)

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 5,
            "message": {
                "text": f"/start link_{raw_token}",
                "chat": {"id": 555},
                "from": {"id": 9, "username": "admin_tg", "first_name": "Admin"},
            },
        },
    )
    assert handled is True
    link = TelegramLinkService(db_session).get_link_for_user(admin_user.id)
    assert link is not None
    assert link.chat_id == "555"
    assert "linked" in client.send_message.call_args[0][2].lower()


@pytest.mark.integration
def test_planning_requires_linked_chat(db_session, catalog_seed, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "mealroulette_bot")
    client = MagicMock()
    update_service = TelegramUpdateService(db_session, client=client)

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 10,
            "message": {
                "text": "/planning 3",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )
    assert handled is True
    assert "link your mealroulette account" in client.send_message.call_args[0][2].lower()


@pytest.mark.integration
def test_planning_and_reminder_commands_send_html(db_session, catalog_seed, admin_user, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "mealroulette_bot")
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="9001",
            telegram_user_id="1",
            username="admin_tg",
        )
    )
    HouseholdMembershipService(db_session).ensure_notification_subscription(
        admin_user.id, DEFAULT_HOUSEHOLD_ID
    )
    db_session.commit()

    client = MagicMock()
    update_service = TelegramUpdateService(db_session, client=client)

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 10,
            "message": {
                "text": "/planning 3",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )
    assert handled is True
    planning_call = client.send_message.call_args
    assert planning_call.kwargs.get("parse_mode") == "HTML"
    planning_message = planning_call.args[2]
    assert "Planning" in planning_message

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 11,
            "message": {
                "text": "/reminder",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )
    assert handled is True
    reminder_call = client.send_message.call_args
    assert reminder_call.kwargs.get("parse_mode") == "HTML"
    reminder_message = reminder_call.args[2]
    assert "Reminder" in reminder_message


@pytest.mark.integration
def test_on_demand_fails_closed_without_matching_telegram_identity(db_session, catalog_seed, admin_user):
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="9001",
            telegram_user_id="99",
            username="admin_tg",
        )
    )
    db_session.commit()
    client = MagicMock()
    update_service = TelegramUpdateService(db_session, client=client)
    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 12,
            "message": {
                "text": "/planning 3",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )
    assert handled is True
    assert "link your mealroulette account" in client.send_message.call_args[0][2].lower()
