"""Greenfield signup creates a product household, not the migration placeholder."""

from sqlalchemy import select

import pytest

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, Household
from mealroulette.models.user import User
from mealroulette.services.household import HouseholdService

pytestmark = pytest.mark.integration


def test_greenfield_signup_creates_non_default_household(client, db_session):
    existing = db_session.get(Household, DEFAULT_HOUSEHOLD_ID)
    if existing is not None:
        db_session.delete(existing)
        db_session.commit()

    assert db_session.get(Household, DEFAULT_HOUSEHOLD_ID) is None

    response = client.post(
        "/api/auth/register",
        json={
            "username": "greenfield",
            "email": "greenfield@example.com",
            "password": "greenpass1",
            "household_name": "Greenfield Home",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    assert token

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "greenfield"
    assert body["active_household_id"] is not None
    assert body["active_household_id"] != str(DEFAULT_HOUSEHOLD_ID)
    assert body["active_household_name"] == "Greenfield Home"
    assert body["household_role"] == "household_admin"

    households = list(db_session.scalars(select(Household)))
    assert len(households) == 1
    assert households[0].id != DEFAULT_HOUSEHOLD_ID
    assert households[0].name == "Greenfield Home"

    user = db_session.scalar(select(User).where(User.username == "greenfield"))
    assert user is not None
    membership = HouseholdService(db_session).active_household_membership(user.id)
    assert membership is not None
    assert membership.household_id == households[0].id
