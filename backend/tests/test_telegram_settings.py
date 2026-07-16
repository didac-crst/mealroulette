from datetime import time
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, HouseholdNotificationSubscription
from mealroulette.models.telegram import TelegramUserLink
from mealroulette.schemas.telegram import TelegramSettingsUpdateRequest
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.telegram_settings import TelegramSettingsService


def _link_user(db_session, user, chat_id: str, *, household_id=DEFAULT_HOUSEHOLD_ID) -> TelegramUserLink:
    link = TelegramUserLink(
        id=uuid4(),
        user_id=user.id,
        chat_id=chat_id,
        username="tester",
        display_name="Tester",
    )
    db_session.add(link)
    HouseholdMembershipService(db_session).ensure_notification_subscription(user.id, household_id)
    db_session.commit()
    return link


@pytest.mark.integration
def test_telegram_settings_update_without_token_field(db_session, admin_user):
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


@pytest.mark.integration
def test_require_send_config_needs_linked_user(db_session):
    service = TelegramSettingsService(db_session)
    row = service.get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = True
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        service.require_send_config(household_id=DEFAULT_HOUSEHOLD_ID)

    assert exc_info.value.status_code == 400
    assert "linked" in exc_info.value.detail.lower()


@pytest.mark.integration
def test_require_send_config_with_linked_user(db_session, admin_user):
    _link_user(db_session, admin_user, "123")
    settings_row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    settings_row.enabled = True
    db_session.commit()

    row, token, chat_ids = TelegramSettingsService(db_session).require_send_config(
        household_id=DEFAULT_HOUSEHOLD_ID
    )
    assert token == "123456:TEST-BOT-TOKEN"
    assert chat_ids == ["123"]
    assert row.household_id == DEFAULT_HOUSEHOLD_ID


@pytest.mark.integration
def test_shopping_channel_respects_notify_shopping(db_session, admin_user):
    _link_user(db_session, admin_user, "123")
    sub = db_session.scalar(
        select(HouseholdNotificationSubscription).where(
            HouseholdNotificationSubscription.user_id == admin_user.id,
            HouseholdNotificationSubscription.household_id == DEFAULT_HOUSEHOLD_ID,
        )
    )
    assert sub is not None
    sub.notify_shopping = False
    settings_row = TelegramSettingsService(db_session).get_row(DEFAULT_HOUSEHOLD_ID)
    settings_row.enabled = True
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        TelegramSettingsService(db_session).require_send_config(
            household_id=DEFAULT_HOUSEHOLD_ID,
            channel="shopping",
        )
    assert "shopping" in exc_info.value.detail.lower()
