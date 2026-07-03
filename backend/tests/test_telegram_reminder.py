from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from mealroulette.models.telegram import TELEGRAM_SETTINGS_ID, TelegramSettings
from mealroulette.services.telegram_client import TelegramClient
from mealroulette.services.telegram_reminder import TelegramReminderService
from mealroulette.services.telegram_subscribers import TelegramSubscriberService


@pytest.mark.integration
def test_send_test_message_broadcasts_to_subscribers(db_session, catalog_seed):
    row = TelegramSettings(id=TELEGRAM_SETTINGS_ID, enabled=True)
    db_session.merge(row)
    TelegramSubscriberService(db_session).subscribe(chat_id="12345", username="household")
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    result = service.send_test_message()

    assert result.sent is True
    assert result.recipient_count == 1
    client.send_message.assert_called_once()
    args = client.send_message.call_args[0]
    assert args[0] == "123456:TEST-BOT-TOKEN"
    assert args[1] == "12345"

    refreshed = db_session.get(TelegramSettings, TELEGRAM_SETTINGS_ID)
    assert refreshed.last_sent_at is not None
    assert refreshed.last_error is None


@pytest.mark.integration
def test_send_daily_reminder_sends_html_reminder(db_session, catalog_seed):
    row = TelegramSettings(id=TELEGRAM_SETTINGS_ID, enabled=True, shopping_window_days=3)
    db_session.merge(row)
    TelegramSubscriberService(db_session).subscribe(chat_id="12345", username="household")
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    result = service.send_daily_reminder()

    assert result.sent is True
    client.send_message.assert_called_once()
    assert client.send_message.call_args.kwargs.get("parse_mode") == "HTML"
    message = client.send_message.call_args[0][2]
    assert "<b>Reminder</b>" in message
    assert "pantry included" in message


@pytest.mark.integration
def test_send_daily_reminder_disabled_raises_http_exception(db_session, catalog_seed):
    row = TelegramSettings(id=TELEGRAM_SETTINGS_ID, enabled=False)
    db_session.merge(row)
    db_session.commit()

    client = MagicMock(spec=TelegramClient)
    service = TelegramReminderService(db_session, client=client)

    with pytest.raises(HTTPException) as exc_info:
        service.send_daily_reminder()

    assert exc_info.value.status_code == 400
    client.send_message.assert_not_called()
