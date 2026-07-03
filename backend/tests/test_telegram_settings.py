from datetime import time

import pytest
from fastapi import HTTPException

from mealroulette.models.telegram import TELEGRAM_SETTINGS_ID, TelegramSettings
from mealroulette.schemas.telegram import TelegramSettingsUpdateRequest
from mealroulette.services.telegram_settings import TelegramSettingsService
from mealroulette.services.telegram_subscribers import TelegramSubscriberService


@pytest.mark.integration
def test_telegram_settings_update_without_token_field(db_session):
    service = TelegramSettingsService(db_session)
    service.get_row()

    public = service.update(
        TelegramSettingsUpdateRequest(
            enabled=True,
            daily_reminder_time=time(7, 30),
            shopping_window_days=2,
        )
    )

    assert public.enabled is True
    assert public.has_bot_token is True
    assert public.daily_reminder_time == time(7, 30)
    assert public.subscriber_count == 0


@pytest.mark.integration
def test_require_send_config_needs_subscriber(db_session):
    service = TelegramSettingsService(db_session)
    row = service.get_row()
    row.enabled = True
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        service.require_send_config()

    assert exc_info.value.status_code == 400
    assert "subscriber" in exc_info.value.detail.lower()


@pytest.mark.integration
def test_require_send_config_with_subscriber(db_session):
    TelegramSubscriberService(db_session).subscribe(chat_id="123", username="tester")
    settings_row = TelegramSettingsService(db_session).get_row()
    settings_row.enabled = True
    db_session.commit()

    row, token, chat_ids = TelegramSettingsService(db_session).require_send_config()
    assert token == "123456:TEST-BOT-TOKEN"
    assert chat_ids == ["123"]
    assert row.id == TELEGRAM_SETTINGS_ID
