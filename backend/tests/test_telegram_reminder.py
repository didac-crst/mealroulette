from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.telegram import TelegramUserLink
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.telegram_client import TelegramClient
from mealroulette.services.telegram_reminder import TelegramReminderService
from mealroulette.services.telegram_settings import TelegramSettingsService


def _enable_and_link(db_session, user, chat_id: str = "12345") -> None:
    row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = True
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=user.id,
            chat_id=chat_id,
            username="household",
        )
    )
    HouseholdMembershipService(db_session).ensure_notification_subscription(user.id, DEFAULT_HOUSEHOLD_ID)
    db_session.commit()


@pytest.mark.integration
def test_send_test_message_broadcasts_to_linked_users(db_session, catalog_seed, admin_user):
    _enable_and_link(db_session, admin_user)

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    result = service.send_test_message(DEFAULT_HOUSEHOLD_ID)

    assert result.sent is True
    assert result.recipient_count == 1
    client.send_message.assert_called_once()
    args = client.send_message.call_args[0]
    assert args[0] == "123456:TEST-BOT-TOKEN"
    assert args[1] == "12345"

    refreshed = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    assert refreshed.last_sent_at is not None
    assert refreshed.last_error is None


@pytest.mark.integration
def test_send_daily_reminder_sends_html_reminder(db_session, catalog_seed, admin_user):
    _enable_and_link(db_session, admin_user)
    row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    row.shopping_window_days = 3
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    result = service.send_daily_reminder(DEFAULT_HOUSEHOLD_ID)

    assert result.sent is True
    client.send_message.assert_called_once()
    assert client.send_message.call_args.kwargs.get("parse_mode") == "HTML"
    message = client.send_message.call_args[0][2]
    assert "<b>Reminder</b>" in message
    assert "pantry included" in message


@pytest.mark.integration
def test_send_daily_reminder_disabled_raises_http_exception(db_session, catalog_seed):
    row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = False
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    with pytest.raises(HTTPException) as exc_info:
        service.send_daily_reminder(DEFAULT_HOUSEHOLD_ID)

    assert exc_info.value.status_code == 400
    client.send_message.assert_not_called()
