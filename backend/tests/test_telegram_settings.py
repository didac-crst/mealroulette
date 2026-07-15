from datetime import time
from uuid import uuid4

import pytest
from fastapi import HTTPException

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, HouseholdNotificationSubscription
from mealroulette.models.telegram import TelegramUserLink
from mealroulette.schemas.telegram import TelegramSettingsUpdateRequest
from mealroulette.services.telegram_settings import TelegramSettingsService

pytestmark = pytest.mark.integration


def test_telegram_settings_update_without_token_field(db_session, default_household):
    service = TelegramSettingsService(db_session)
    service.get_row(DEFAULT_HOUSEHOLD_ID)

    public = service.update(
        DEFAULT_HOUSEHOLD_ID,
        TelegramSettingsUpdateRequest(
            enabled=True,
            daily_reminder_time=time(7, 30),
            shopping_window_days=2,
        ),
    )

    assert public.enabled is True
    assert public.has_bot_token is True
    assert public.daily_reminder_time == time(7, 30)
    assert public.subscriber_count == 0


def test_require_send_config_needs_linked_user(db_session, default_household):
    service = TelegramSettingsService(db_session)
    row = service.get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = True
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        service.require_send_config(household_id=DEFAULT_HOUSEHOLD_ID)

    assert exc_info.value.status_code == 400
    assert "linked" in exc_info.value.detail.lower()


def test_require_send_config_with_linked_user(db_session, default_household, admin_user):
    db_session.add(
        TelegramUserLink(
            id=uuid4(),
            user_id=admin_user.id,
            chat_id="123",
            username="tester",
        )
    )
    db_session.add(
        HouseholdNotificationSubscription(
            id=uuid4(),
            user_id=admin_user.id,
            household_id=DEFAULT_HOUSEHOLD_ID,
            notify_daily_reminder=True,
        )
    )
    settings_row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    settings_row.enabled = True
    db_session.commit()

    row, token, chat_ids = TelegramSettingsService(db_session).require_send_config(
        household_id=DEFAULT_HOUSEHOLD_ID
    )
    assert token == "123456:TEST-BOT-TOKEN"
    assert chat_ids == ["123"]
    assert row.household_id == DEFAULT_HOUSEHOLD_ID
