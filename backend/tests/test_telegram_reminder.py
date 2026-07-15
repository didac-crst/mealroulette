from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, HouseholdNotificationSubscription
from mealroulette.models.telegram import TelegramSettings, TelegramUserLink
from mealroulette.services.telegram_client import TelegramClient
from mealroulette.services.telegram_reminder import TelegramReminderService


def _link_user_for_reminders(db_session, user) -> None:
    existing = db_session.query(HouseholdNotificationSubscription).filter_by(
        user_id=user.id, household_id=DEFAULT_HOUSEHOLD_ID
    ).one_or_none()
    if existing is None:
        db_session.add(
            HouseholdNotificationSubscription(
                id=uuid4(),
                user_id=user.id,
                household_id=DEFAULT_HOUSEHOLD_ID,
                notify_daily_reminder=True,
            )
        )
    else:
        existing.notify_daily_reminder = True
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=user.id,
            chat_id="12345",
            username="household",
        )
    )
    db_session.commit()


@pytest.mark.integration
def test_send_test_message_broadcasts_to_linked_users(db_session, catalog_seed, default_household, admin_user):
    row = TelegramSettings(household_id=DEFAULT_HOUSEHOLD_ID, enabled=True)
    db_session.merge(row)
    _link_user_for_reminders(db_session, admin_user)

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    result = service.send_test_message(DEFAULT_HOUSEHOLD_ID)

    assert result.sent is True
    assert result.recipient_count == 1
    client.send_message.assert_called_once()
    args = client.send_message.call_args[0]
    assert args[0] == "123456:TEST-BOT-TOKEN"
    assert args[1] == "12345"

    refreshed = service.settings_service.get_row(DEFAULT_HOUSEHOLD_ID)
    assert refreshed.last_sent_at is not None
    assert refreshed.last_error is None


@pytest.mark.integration
def test_send_daily_reminder_sends_html_reminder(db_session, catalog_seed, default_household, admin_user):
    row = TelegramSettings(household_id=DEFAULT_HOUSEHOLD_ID, enabled=True, shopping_window_days=3)
    db_session.merge(row)
    _link_user_for_reminders(db_session, admin_user)

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
def test_send_personal_test_and_reminder(db_session, catalog_seed, default_household, admin_user):
    _link_user_for_reminders(db_session, admin_user)

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    test = service.send_personal_test_message(admin_user.id, DEFAULT_HOUSEHOLD_ID)
    assert test.sent is True
    assert test.recipient_count == 1

    reminder = service.send_personal_daily_reminder(admin_user.id, DEFAULT_HOUSEHOLD_ID)
    assert reminder.sent is True
    assert client.send_message.call_count == 2
    assert client.send_message.call_args.kwargs.get("parse_mode") == "HTML"

    sub = (
        db_session.query(HouseholdNotificationSubscription)
        .filter_by(user_id=admin_user.id, household_id=DEFAULT_HOUSEHOLD_ID)
        .one()
    )
    assert sub.last_reminder_sent_at is not None
