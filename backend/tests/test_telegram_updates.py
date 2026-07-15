from uuid import uuid4

import pytest
from unittest.mock import MagicMock

from mealroulette.models.telegram import TelegramUserLink
from mealroulette.services.telegram_updates import TelegramUpdateService

pytestmark = pytest.mark.integration


def test_help_lists_commands_without_deprecated_mentions(db_session):
    client = MagicMock()
    service = TelegramUpdateService(db_session, client=client)
    service._handle_update(
        "token",
        {
            "message": {
                "text": "/help",
                "chat": {"id": 4242},
                "from": {"id": 7, "username": "didac"},
            }
        },
    )
    reply = client.send_message.call_args.args[2]
    assert "/planning" in reply
    assert "/reminder" in reply
    assert "/shopping" in reply
    assert "subscribe" not in reply.lower()
    assert "unsubscribe" not in reply.lower()
    assert "deprecated" not in reply.lower()
    assert client.send_message.call_args.kwargs.get("parse_mode") == "HTML"


def test_subscribe_and_unsubscribe_are_deprecated(db_session):
    client = MagicMock()
    service = TelegramUpdateService(db_session, client=client)

    service._handle_update(
        "token",
        {
            "message": {
                "text": "/subscribe",
                "chat": {"id": 4242},
                "from": {"id": 7, "username": "didac", "first_name": "Didac"},
            }
        },
    )
    first_reply = client.send_message.call_args.args[2]
    assert "no longer uses /subscribe" in first_reply.lower()
    assert db_session.query(TelegramUserLink).count() == 0

    service._handle_update(
        "token",
        {
            "message": {
                "text": "/unsubscribe",
                "chat": {"id": 4242},
                "from": {"id": 7, "username": "didac"},
            }
        },
    )
    second_reply = client.send_message.call_args.args[2]
    assert "no longer uses /unsubscribe" in second_reply.lower()


def test_start_without_payload_points_to_app_link(db_session):
    client = MagicMock()
    service = TelegramUpdateService(db_session, client=client)
    service._handle_update(
        "token",
        {
            "message": {
                "text": "/start",
                "chat": {"id": 99},
                "from": {"id": 1, "username": "chef"},
            }
        },
    )
    reply = client.send_message.call_args.args[2]
    assert "settings → telegram" in reply.lower()


def test_start_with_link_token_links_user(db_session, admin_user, default_household):
    from mealroulette.services.telegram_link import TelegramLinkService

    link_service = TelegramLinkService(db_session)
    _row, raw = link_service.create_link_token(admin_user.id)

    client = MagicMock()
    service = TelegramUpdateService(db_session, client=client)
    service._handle_update(
        "token",
        {
            "message": {
                "text": f"/start link_{raw}",
                "chat": {"id": 555},
                "from": {"id": 12, "username": "chef", "first_name": "Chef"},
            }
        },
    )
    reply = client.send_message.call_args.args[2]
    assert "Welcome to MealRoulette" in reply
    assert "You're linked." in reply
    assert admin_user.username in reply
    assert default_household.name in reply
    assert str(admin_user.id) not in reply
    assert str(default_household.id) not in reply
    assert client.send_message.call_args.kwargs.get("parse_mode") == "HTML"
    linked = link_service.get_link_for_user(admin_user.id)
    assert linked is not None
    assert linked.chat_id == "555"
