from uuid import uuid4

import pytest
from sqlalchemy import select

from mealroulette.auth.security import hash_password
from mealroulette.models.household import (
    DEFAULT_HOUSEHOLD_ID,
    Household,
    HouseholdMembership,
    HouseholdNotificationSubscription,
    HouseholdRole,
)
from mealroulette.models.telegram import TelegramUserLink
from mealroulette.models.user import User, UserRole
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.telegram_link import TelegramLinkService
from mealroulette.services.telegram_settings import TelegramSettingsService

pytestmark = pytest.mark.integration


def _make_household_user(db_session, *, username: str, household: Household, role: HouseholdRole) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.user,
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        HouseholdMembership(
            household_id=household.id,
            user_id=user.id,
            role=role,
            active=True,
        )
    )
    HouseholdMembershipService(db_session).ensure_notification_subscription(user.id, household.id)
    db_session.commit()
    db_session.refresh(user)
    return user


def _link(db_session, user: User, chat_id: str) -> TelegramUserLink:
    link = TelegramUserLink(id=uuid4(), user_id=user.id, chat_id=chat_id, username=user.username)
    db_session.add(link)
    db_session.commit()
    return link


def test_telegram_chat_can_link_multiple_users(db_session, admin_user, regular_user):
    service = TelegramLinkService(db_session)
    _, token_a = service.create_link_token(admin_user.id)
    _, token_b = service.create_link_token(regular_user.id)

    link_a = service.link_chat(token_a, chat_id="shared", telegram_user_id="1", username="a", display_name="A")
    link_b = service.link_chat(token_b, chat_id="shared", telegram_user_id="2", username="b", display_name="B")

    assert link_a.chat_id == "shared"
    assert link_b.chat_id == "shared"
    assert link_a.user_id != link_b.user_id


def test_link_token_cannot_be_reused(db_session, admin_user):
    service = TelegramLinkService(db_session)
    _, token = service.create_link_token(admin_user.id)
    service.link_chat(token, chat_id="1", telegram_user_id="1", username="a", display_name="A")
    with pytest.raises(ValueError):
        service.link_chat(token, chat_id="2", telegram_user_id="1", username="a", display_name="A")


def test_recipient_lists_are_household_scoped(db_session, default_household):
    other = Household(id=uuid4(), name="Other household")
    db_session.add(other)
    db_session.flush()

    user_h1 = _make_household_user(
        db_session, username="h1admin", household=default_household, role=HouseholdRole.household_admin
    )
    user_h2 = _make_household_user(
        db_session, username="h2admin", household=other, role=HouseholdRole.household_admin
    )
    _link(db_session, user_h1, "chat-h1")
    _link(db_session, user_h2, "chat-h2")

    links = TelegramLinkService(db_session)
    assert links.list_subscribed_chat_ids(default_household.id) == ["chat-h1"]
    assert links.list_subscribed_chat_ids(other.id) == ["chat-h2"]
    assert links.list_roulette_chat_ids(default_household.id) == ["chat-h1"]
    assert links.list_shopping_chat_ids(other.id) == ["chat-h2"]


def test_toggle_off_excludes_channel(db_session, admin_user):
    _link(db_session, admin_user, "chat-1")
    HouseholdMembershipService(db_session).ensure_notification_subscription(
        admin_user.id, DEFAULT_HOUSEHOLD_ID
    )
    sub = db_session.scalar(
        select(HouseholdNotificationSubscription).where(
            HouseholdNotificationSubscription.user_id == admin_user.id,
            HouseholdNotificationSubscription.household_id == DEFAULT_HOUSEHOLD_ID,
        )
    )
    assert sub is not None
    sub.notify_roulette = False
    sub.notify_shopping = False
    db_session.commit()

    links = TelegramLinkService(db_session)
    assert links.list_subscribed_chat_ids(DEFAULT_HOUSEHOLD_ID) == ["chat-1"]
    assert links.list_roulette_chat_ids(DEFAULT_HOUSEHOLD_ID) == []
    assert links.list_shopping_chat_ids(DEFAULT_HOUSEHOLD_ID) == []


def test_unlink_stops_delivery(db_session, admin_user):
    _link(db_session, admin_user, "chat-1")
    HouseholdMembershipService(db_session).ensure_notification_subscription(
        admin_user.id, DEFAULT_HOUSEHOLD_ID
    )
    service = TelegramLinkService(db_session)
    assert service.list_subscribed_chat_ids(DEFAULT_HOUSEHOLD_ID) == ["chat-1"]
    assert service.unlink_user(admin_user.id) is True
    assert service.list_subscribed_chat_ids(DEFAULT_HOUSEHOLD_ID) == []


def test_household_settings_rows_are_isolated(db_session, default_household):
    other = Household(id=uuid4(), name="Other")
    db_session.add(other)
    db_session.commit()

    service = TelegramSettingsService(db_session)
    row1 = service.get_row(default_household.id)
    row2 = service.get_row(other.id)
    row1.enabled = True
    row2.enabled = False
    db_session.commit()

    assert service.get_row(default_household.id).enabled is True
    assert service.get_row(other.id).enabled is False
