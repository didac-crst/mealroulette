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


from datetime import UTC, datetime, time

from mealroulette.models.household import HouseholdNotificationSubscription
from mealroulette.services.telegram_client import TelegramApiError
from sqlalchemy import select


def _subscription(db_session, user):
    return db_session.scalar(
        select(HouseholdNotificationSubscription).where(
            HouseholdNotificationSubscription.user_id == user.id,
            HouseholdNotificationSubscription.household_id == DEFAULT_HOUSEHOLD_ID,
        )
    )


@pytest.mark.integration
def test_should_send_personal_scheduled_minute_and_suppression(db_session, admin_user):
    _enable_and_link(db_session, admin_user)
    sub = _subscription(db_session, admin_user)
    assert sub is not None
    sub.daily_reminder_time = time(8, 0)
    sub.timezone = "UTC"
    sub.notify_daily_reminder = True
    sub.last_reminder_sent_at = None
    db_session.commit()

    now = datetime(2026, 7, 16, 8, 0, tzinfo=UTC)
    assert TelegramReminderService.should_send_personal_scheduled(sub, now=now) is True
    assert TelegramReminderService.should_send_personal_scheduled(sub, now=datetime(2026, 7, 16, 8, 1, tzinfo=UTC)) is False

    sub.notify_daily_reminder = False
    db_session.commit()
    assert TelegramReminderService.should_send_personal_scheduled(sub, now=now) is False

    sub.notify_daily_reminder = True
    sub.last_reminder_sent_at = datetime(2026, 7, 16, 8, 0, tzinfo=UTC)
    db_session.commit()
    assert TelegramReminderService.should_send_personal_scheduled(sub, now=now) is False

    sub.timezone = "Not/AZone"
    sub.last_reminder_sent_at = None
    db_session.commit()
    # Invalid timezone falls back to UTC; still matches 08:00 UTC.
    assert TelegramReminderService.should_send_personal_scheduled(sub, now=now) is True


@pytest.mark.integration
def test_run_scheduled_reminder_skips_missing_link_and_disabled_household(db_session, admin_user):
    row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = True
    HouseholdMembershipService(db_session).ensure_notification_subscription(admin_user.id, DEFAULT_HOUSEHOLD_ID)
    sub = _subscription(db_session, admin_user)
    assert sub is not None
    sub.daily_reminder_time = time(8, 0)
    sub.timezone = "UTC"
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)
    now = datetime(2026, 7, 16, 8, 0, tzinfo=UTC)
    assert service.run_scheduled_reminder(now=now) == []
    client.send_message.assert_not_called()

    _enable_and_link(db_session, admin_user)
    row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = False
    db_session.commit()
    assert service.run_scheduled_reminder(now=now) == []


@pytest.mark.integration
def test_run_scheduled_reminder_releases_claim_on_send_failure(db_session, admin_user):
    _enable_and_link(db_session, admin_user)
    sub = _subscription(db_session, admin_user)
    assert sub is not None
    sub.daily_reminder_time = time(8, 0)
    sub.timezone = "UTC"
    sub.last_reminder_sent_at = None
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    client.send_message.side_effect = TelegramApiError("boom")
    service = TelegramReminderService(db_session, client=client)
    now = datetime(2026, 7, 16, 8, 0, tzinfo=UTC)
    assert service.run_scheduled_reminder(now=now) == []
    db_session.refresh(sub)
    assert sub.last_reminder_sent_at is None
