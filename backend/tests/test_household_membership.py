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
    assert payload.active_household_name == "Default household"
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


def test_register_new_household_and_login(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "owner",
            "email": "owner@example.com",
            "password": "ownerpass1",
            "household_name": "Owner Home",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    profile = me.json()
    assert profile["household_role"] == HouseholdRole.household_admin.value
    assert profile["active_household_name"] == "Owner Home"
    assert profile["active_household_id"] is not None


def test_household_invitation_flow(client, admin_token):
    created = client.post("/api/household/invitations", headers={"Authorization": f"Bearer {admin_token}"})
    assert created.status_code == 201
    invite_url = created.json()["invite_url"]
    token = invite_url.split("token=")[1]

    registered = client.post(
        "/api/auth/register-with-invitation",
        json={
            "token": token,
            "username": "invited",
            "email": "invited@example.com",
            "password": "invitedpass",
        },
    )
    assert registered.status_code == 201

    members = client.get("/api/household/members", headers={"Authorization": f"Bearer {admin_token}"})
    assert members.status_code == 200
    usernames = {row["username"] for row in members.json()}
    assert "invited" in usernames


def test_regular_user_cannot_create_invitation(client, user_token):
    response = client.post("/api/household/invitations", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


def test_household_admin_can_rename_household(client, admin_token, db_session, default_household):
    response = client.patch(
        "/api/household",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Casa Didac"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Casa Didac"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert me.status_code == 200
    assert me.json()["active_household_name"] == "Casa Didac"

    db_session.refresh(default_household)
    assert default_household.name == "Casa Didac"


def test_regular_user_cannot_rename_household(client, user_token):
    response = client.patch(
        "/api/household",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "Nope"},
    )
    assert response.status_code == 403


def test_user_cannot_join_second_household(client, admin_token):
    first = client.post(
        "/api/auth/register",
        json={
            "username": "solo",
            "email": "solo@example.com",
            "password": "solopass1",
            "household_name": "Solo Home",
        },
    )
    assert first.status_code == 201
    solo_token = first.json()["access_token"]

    created = client.post("/api/household/invitations", headers={"Authorization": f"Bearer {admin_token}"})
    assert created.status_code == 201
    token = created.json()["invite_url"].split("token=")[1]

    conflict = client.post(
        "/api/household/invitations/accept",
        headers={"Authorization": f"Bearer {solo_token}"},
        json={"token": token},
    )
    assert conflict.status_code == 409
    assert "active household" in conflict.json()["error"]["message"].lower()


def test_cannot_remove_last_household_admin(client, admin_token):
    members = client.get("/api/household/members", headers={"Authorization": f"Bearer {admin_token}"})
    assert members.status_code == 200
    admin_membership_id = members.json()[0]["membership_id"]

    response = client.delete(
        f"/api/household/members/{admin_membership_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
