from unittest.mock import MagicMock

import pytest

from mealroulette.services.telegram_subscribers import TelegramSubscriberService
from mealroulette.services.telegram_updates import TelegramUpdateService


@pytest.mark.integration
def test_subscribe_and_unsubscribe_commands(db_session):
    subscriber_service = TelegramSubscriberService(db_session)
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
    subscribers = subscriber_service.list_subscribers()
    assert len(subscribers) == 1
    assert subscribers[0].chat_id == "4242"
    assert subscribers[0].username == "didac"
    first_reply = client.send_message.call_args[0][2]
    assert "now subscribed" in first_reply.lower()
    assert "daily shopping reminders" in first_reply.lower()

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 2,
            "message": {
                "text": "/subscribe",
                "chat": {"id": 4242},
                "from": {"id": 99},
            },
        },
    )
    assert handled is True
    assert len(subscriber_service.list_subscribers()) == 1
    second_reply = client.send_message.call_args[0][2]
    assert "already subscribed" in second_reply.lower()

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
    assert subscriber_service.list_subscribers() == []
    third_reply = client.send_message.call_args[0][2]
    assert "unsubscribed" in third_reply.lower()


@pytest.mark.integration
def test_planning_and_reminder_commands_send_html(db_session, catalog_seed, monkeypatch):
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
    planning_call = client.send_message.call_args
    assert planning_call.kwargs.get("parse_mode") == "HTML"
    planning_message = planning_call.args[2]
    assert "Planning" in planning_message
    assert "MealRoulette" not in planning_message

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

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 12,
            "message": {
                "text": "/planning 0",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )
    assert handled is True
    invalid_reply = client.send_message.call_args.args[2]
    assert "between 1 and" in invalid_reply

    handled = update_service._handle_update(
        "fake-token",
        {
            "update_id": 13,
            "message": {
                "text": "/shopping",
                "chat": {"id": 9001},
                "from": {"id": 1},
            },
        },
    )
    assert handled is True
    shopping_call = client.send_message.call_args
    assert shopping_call.kwargs.get("parse_mode") == "HTML"
    shopping_message = shopping_call.args[2]
    assert "Shopping" in shopping_message
