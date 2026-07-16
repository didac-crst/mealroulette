import pytest
from uuid import UUID

from mealroulette.models.household import (
    DEFAULT_HOUSEHOLD_ID,
    HouseholdRole,
    PlatformRole,
)
from mealroulette.models.user import UserRole
from mealroulette.services.auth import UserService
from mealroulette.services.household import HouseholdService

pytestmark = pytest.mark.integration


def test_default_household_exists(default_household):
    assert default_household.id == DEFAULT_HOUSEHOLD_ID


def test_admin_user_gets_platform_and_household_admin_roles(admin_user, db_session):
    service = HouseholdService(db_session)
    membership = service.active_household_membership(admin_user.id)

    assert membership is not None
    assert membership.household_id == DEFAULT_HOUSEHOLD_ID
    assert membership.role == HouseholdRole.household_admin
    assert PlatformRole.platform_admin in service.list_platform_roles(admin_user.id)


def test_regular_user_gets_household_member_role(regular_user, db_session):
    service = HouseholdService(db_session)
    membership = service.active_household_membership(regular_user.id)

    assert membership is not None
    assert membership.role == HouseholdRole.household_member
    assert service.list_platform_roles(regular_user.id) == []


def test_user_public_includes_tenancy_fields(admin_user, db_session):
    payload = UserService(db_session).to_public(admin_user)

    assert payload.platform_roles == [PlatformRole.platform_admin]
    assert payload.active_household_id == DEFAULT_HOUSEHOLD_ID
    assert payload.household_role == HouseholdRole.household_admin


def test_create_user_provisions_default_household_membership(admin_user, admin_token, client, db_session):
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "member",
            "email": "member@example.com",
            "password": "memberpass",
            "role": "user",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["active_household_id"] == str(DEFAULT_HOUSEHOLD_ID)
    assert body["household_role"] == HouseholdRole.household_member.value

    membership = HouseholdService(db_session).active_household_membership(UUID(body["id"]))
    assert membership is not None
    assert membership.role == HouseholdRole.household_member
