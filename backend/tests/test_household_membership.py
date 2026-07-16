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


def test_invitation_token_rejected_after_first_use_register(client, admin_token):
    created = client.post("/api/household/invitations", headers={"Authorization": f"Bearer {admin_token}"})
    assert created.status_code == 201
    token = created.json()["invite_url"].split("token=")[1]

    first = client.post(
        "/api/auth/register-with-invitation",
        json={
            "token": token,
            "username": "firstinvite",
            "email": "firstinvite@example.com",
            "password": "firstpass1",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/auth/register-with-invitation",
        json={
            "token": token,
            "username": "secondinvite",
            "email": "secondinvite@example.com",
            "password": "secondpass1",
        },
    )
    assert second.status_code == 410


def test_invitation_token_rejected_after_first_use_accept(client, admin_token):
    created = client.post("/api/household/invitations", headers={"Authorization": f"Bearer {admin_token}"})
    assert created.status_code == 201
    token = created.json()["invite_url"].split("token=")[1]

    invitee = client.post(
        "/api/auth/register-with-invitation",
        json={
            "token": token,
            "username": "accepteer",
            "email": "accepteer@example.com",
            "password": "acceptpass2",
        },
    )
    assert invitee.status_code == 201

    other = client.post(
        "/api/auth/register",
        json={
            "username": "accepttwo",
            "email": "accepttwo@example.com",
            "password": "acceptpass3",
            "household_name": "Temp Two",
        },
    )
    assert other.status_code == 201
    reuse = client.post(
        "/api/household/invitations/accept",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
        json={"token": token},
    )
    assert reuse.status_code == 410


def test_concurrent_register_with_invitation_claims_token_once(db_engine):
    from concurrent.futures import ThreadPoolExecutor
    from uuid import uuid4

    from fastapi import HTTPException
    from sqlalchemy.orm import sessionmaker

    from mealroulette.auth.security import hash_password
    from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
    from mealroulette.models.user import User, UserRole
    from mealroulette.services.household_membership import HouseholdMembershipService

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    household_id = uuid4()
    with SessionLocal() as setup:
        household = Household(id=household_id, name="Race Household")
        admin = User(
            username=f"race-admin-{household_id.hex[:8]}",
            email=f"race-admin-{household_id.hex[:8]}@example.com",
            password_hash=hash_password("adminpassword"),
            role=UserRole.user,
            active=True,
        )
        setup.add(household)
        setup.add(admin)
        setup.flush()
        setup.add(
            HouseholdMembership(
                household_id=household_id,
                user_id=admin.id,
                role=HouseholdRole.household_admin,
                active=True,
            )
        )
        setup.commit()
        _invitation, token = HouseholdMembershipService(setup).create_invitation(household_id, admin.id)

    barrier = __import__("threading").Barrier(2)

    def race(index: int) -> int:
        barrier.wait(timeout=5)
        with SessionLocal() as session:
            try:
                HouseholdMembershipService(session).register_with_invitation(
                    token=token,
                    username=f"race-user-{index}-{household_id.hex[:8]}",
                    email=f"race-user-{index}-{household_id.hex[:8]}@example.com",
                    password="racepass12",
                )
                return 201
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(race, (1, 2)))

    assert sorted(results) == [201, 410]


def test_concurrent_accept_invitation_claims_token_once(db_engine):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from uuid import uuid4

    from fastapi import HTTPException
    from sqlalchemy.orm import sessionmaker

    from mealroulette.auth.security import hash_password
    from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
    from mealroulette.models.user import User, UserRole
    from mealroulette.services.household_membership import HouseholdMembershipService

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    household_id = uuid4()
    with SessionLocal() as setup:
        household = Household(id=household_id, name="Accept Race Household")
        admin = User(
            username=f"accept-admin-{household_id.hex[:8]}",
            email=f"accept-admin-{household_id.hex[:8]}@example.com",
            password_hash=hash_password("adminpassword"),
            role=UserRole.user,
            active=True,
        )
        users = []
        for index in (1, 2):
            users.append(
                User(
                    username=f"accept-user-{index}-{household_id.hex[:8]}",
                    email=f"accept-user-{index}-{household_id.hex[:8]}@example.com",
                    password_hash=hash_password("userpassword"),
                    role=UserRole.user,
                    active=True,
                )
            )
        setup.add(household)
        setup.add(admin)
        setup.add_all(users)
        setup.flush()
        setup.add(
            HouseholdMembership(
                household_id=household_id,
                user_id=admin.id,
                role=HouseholdRole.household_admin,
                active=True,
            )
        )
        setup.commit()
        _invitation, token = HouseholdMembershipService(setup).create_invitation(household_id, admin.id)
        user_ids = [user.id for user in users]

    barrier = __import__("threading").Barrier(2)

    def race(user_id) -> int:
        barrier.wait(timeout=5)
        with SessionLocal() as session:
            user = session.get(User, user_id)
            assert user is not None
            try:
                HouseholdMembershipService(session).accept_invitation_for_user(token, user)
                return 201
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(race, user_id) for user_id in user_ids]
        results = [future.result() for future in as_completed(futures)]

    assert sorted(results) == [201, 410]


def test_concurrent_last_admin_removal_keeps_one_admin(db_engine):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from uuid import uuid4

    from fastapi import HTTPException
    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from mealroulette.auth.security import hash_password
    from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
    from mealroulette.models.user import User, UserRole
    from mealroulette.services.household_membership import HouseholdMembershipService

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    household_id = uuid4()
    with SessionLocal() as setup:
        household = Household(id=household_id, name="Admin Race Household")
        admins = [
            User(
                username=f"admin-race-{index}-{household_id.hex[:8]}",
                email=f"admin-race-{index}-{household_id.hex[:8]}@example.com",
                password_hash=hash_password("adminpassword"),
                role=UserRole.user,
                active=True,
            )
            for index in (1, 2)
        ]
        setup.add(household)
        setup.add_all(admins)
        setup.flush()
        memberships = [
            HouseholdMembership(
                household_id=household_id,
                user_id=admin.id,
                role=HouseholdRole.household_admin,
                active=True,
            )
            for admin in admins
        ]
        setup.add_all(memberships)
        setup.commit()
        membership_ids = [membership.id for membership in memberships]

    barrier = __import__("threading").Barrier(2)

    def race(membership_id) -> int:
        barrier.wait(timeout=5)
        with SessionLocal() as session:
            try:
                HouseholdMembershipService(session).remove_member(membership_id, household_id)
                return 204
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(race, membership_id) for membership_id in membership_ids]
        results = [future.result() for future in as_completed(futures)]

    assert sorted(results) == [204, 409]

    with SessionLocal() as verify:
        active_admins = verify.scalar(
            select(func.count())
            .select_from(HouseholdMembership)
            .where(
                HouseholdMembership.household_id == household_id,
                HouseholdMembership.active.is_(True),
                HouseholdMembership.role == HouseholdRole.household_admin,
            )
        )
        assert active_admins == 1
