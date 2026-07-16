"""Tenant isolation tests for household-owned aggregates."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
from mealroulette.models.user import User, UserRole
from mealroulette.schemas.catalog import DishCreateRequest
from mealroulette.services.catalog import CatalogService
from mealroulette.services.planning import PlanningService


@pytest.fixture
def second_household(db_session: Session) -> Household:
    household = Household(id=uuid.uuid4(), name="Second household")
    db_session.add(household)
    db_session.commit()
    db_session.refresh(household)
    return household


@pytest.fixture
def second_household_user(db_session: Session, second_household: Household) -> User:
    user = User(
        username="other-household",
        email="other@example.com",
        password_hash=hash_password("otherpassword"),
        role=UserRole.user,
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        HouseholdMembership(
            household_id=second_household.id,
            user_id=user.id,
            role=HouseholdRole.household_member,
            active=True,
        )
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_household_token(client: TestClient, second_household_user: User) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": second_household_user.username, "password": "otherpassword"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def second_household_headers(second_household_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {second_household_token}"}


@pytest.mark.integration
def test_dish_isolation_between_households(
    db_session: Session,
    default_household: Household,
    second_household: Household,
):
    default_service = CatalogService(db_session, default_household.id)
    dish = default_service.create_dish(DishCreateRequest(name="Default household only dish"))

    other_service = CatalogService(db_session, second_household.id)
    with pytest.raises(HTTPException) as exc_info:
        other_service.get_dish(dish.id)
    assert exc_info.value.status_code == 404

    assert other_service.list_dishes() == []


@pytest.mark.integration
def test_meal_plan_isolation_between_households(
    db_session: Session,
    default_household: Household,
    second_household: Household,
):
    default_planning = PlanningService(db_session, default_household.id)
    other_planning = PlanningService(db_session, second_household.id)

    from datetime import date

    week_start = date(2026, 7, 7)
    default_plan = default_planning.get_or_create_plan(week_start)
    other_plan = other_planning.get_or_create_plan(week_start)

    assert default_plan.id != other_plan.id
    assert default_plan.household_id == default_household.id
    assert other_plan.household_id == second_household.id

    with pytest.raises(HTTPException) as exc_info:
        other_planning._load_plan(default_plan.id)
    assert exc_info.value.status_code == 404


@pytest.mark.integration
def test_api_dish_isolation(
    client: TestClient,
    db_session: Session,
    default_household: Household,
    admin_headers: dict[str, str],
    second_household_headers: dict[str, str],
):
    create = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Tenant scoped dish", "status": "active"},
    )
    assert create.status_code == 201
    dish_id = create.json()["id"]

    assert client.get(f"/api/dishes/{dish_id}", headers=admin_headers).status_code == 200
    assert client.get(f"/api/dishes/{dish_id}", headers=second_household_headers).status_code == 404
