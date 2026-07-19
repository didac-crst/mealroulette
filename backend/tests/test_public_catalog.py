from __future__ import annotations

import uuid
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.models.catalog import Dish, Recipe
from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
from mealroulette.models.public_catalog import PublicRecipe, PublicRecipeStatus
from mealroulette.models.user import User, UserRole


def _create_dish_with_recipe(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    *,
    dish_extras: dict | None = None,
) -> tuple[dict, dict]:
    payload = {"name": name, "status": "active", "description": f"{name} description"}
    if dish_extras:
        payload.update(dish_extras)
    dish = client.post(
        "/api/dishes",
        headers=headers,
        json=payload,
    )
    assert dish.status_code == 201, dish.text
    dish_body = dish.json()
    recipe = client.post(
        f"/api/dishes/{dish_body['id']}/recipes",
        headers=headers,
        json={
            "variant_name": "Main",
            "is_main": True,
            "description": f"{name} recipe",
            "servings": 4,
        },
    )
    assert recipe.status_code == 201, recipe.text
    return dish_body, recipe.json()


def _add_ingredient_and_step(client: TestClient, headers: dict[str, str], recipe_id: int) -> None:
    ingredient = client.post(
        "/api/ingredients/confirm",
        headers=headers,
        json={
            "action": "create",
            "proposed_name": f"public-catalog-spice-{recipe_id}",
            "display_name": "Public catalog spice",
        },
    )
    assert ingredient.status_code == 201, ingredient.text
    units = client.get("/api/units", headers=headers)
    assert units.status_code == 200, units.text
    assert units.json(), "expected seeded units"
    unit_id = units.json()[0]["id"]
    added = client.post(
        f"/api/recipes/{recipe_id}/ingredients",
        headers=headers,
        json={"ingredient_id": ingredient.json()["id"], "quantity": "2", "unit_id": unit_id},
    )
    assert added.status_code == 201, added.text
    step = client.post(
        f"/api/recipes/{recipe_id}/steps",
        headers=headers,
        json={"step_number": 1, "instruction": "Cook gently"},
    )
    assert step.status_code == 201, step.text


@pytest.fixture
def second_household(db_session: Session) -> Household:
    household = Household(id=uuid.uuid4(), name="Second household")
    db_session.add(household)
    db_session.commit()
    db_session.refresh(household)
    return household


@pytest.fixture
def second_household_admin(db_session: Session, second_household: Household) -> User:
    user = User(
        username="second-admin",
        email="second-admin@example.com",
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
            role=HouseholdRole.household_admin,
            active=True,
        )
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_household_headers(client: TestClient, second_household_admin: User) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": second_household_admin.username, "password": "otherpassword"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_household_admin_can_submit_and_member_cannot_see_until_approved(
    client,
    admin_headers,
    user_headers,
    catalog_seed,
):
    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Public Pasta")
    _add_ingredient_and_step(client, admin_headers, recipe["id"])

    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    )
    assert submitted.status_code == 201, submitted.text
    body = submitted.json()
    assert body["status"] == "submitted"
    assert body["originating_recipe_id"] == recipe["id"]
    assert body["current_version_id"] is None
    public_id = body["id"]

    member_list = client.get("/api/public-recipes", headers=user_headers)
    assert member_list.status_code == 200
    assert all(item["id"] != public_id for item in member_list.json())

    member_get = client.get(f"/api/public-recipes/{public_id}", headers=user_headers)
    assert member_get.status_code == 404

    non_admin = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=user_headers,
    )
    assert non_admin.status_code == 403


def test_platform_approve_reject_delist_and_resubmit(
    client,
    admin_headers,
    user_headers,
    catalog_seed,
    db_session: Session,
):
    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Approve Flow Dish")
    _add_ingredient_and_step(client, admin_headers, recipe["id"])

    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()
    public_id = submitted["id"]

    rejected = client.post(
        f"/api/platform/public-recipes/{public_id}/reject",
        headers=admin_headers,
        json={"review_note": "Needs clearer steps"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    blank_note = client.post(
        f"/api/platform/public-recipes/{public_id}/reject",
        headers=admin_headers,
        json={"review_note": "   "},
    )
    assert blank_note.status_code == 422

    resubmitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    )
    assert resubmitted.status_code == 201, resubmitted.text
    assert resubmitted.json()["status"] == "submitted"
    assert resubmitted.json()["latest_version"]["version_number"] == 2

    approved = client.post(
        f"/api/platform/public-recipes/{public_id}/approve",
        headers=admin_headers,
        json={},
    )
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()
    assert approved_body["status"] == "public"
    assert approved_body["current_version_id"] is not None
    assert approved_body["current_version"]["published_at"] is not None

    listed = client.get("/api/public-recipes", headers=user_headers)
    assert listed.status_code == 200
    assert any(item["id"] == public_id for item in listed.json())

    detail = client.get(f"/api/public-recipes/{public_id}", headers=user_headers)
    assert detail.status_code == 200
    assert "originating_household_id" not in detail.json()
    assert detail.json()["title"]

    conflict = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["message"] == (
        "This recipe is already public. Updating an existing public recipe is not supported yet."
    )

    delisted = client.post(
        f"/api/platform/public-recipes/{public_id}/delist",
        headers=admin_headers,
        json={"review_note": "Quality issue"},
    )
    assert delisted.status_code == 200
    assert delisted.json()["status"] == "delisted"

    after_delist = client.get("/api/public-recipes", headers=user_headers)
    assert all(item["id"] != public_id for item in after_delist.json())

    blocked_resubmit = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    )
    assert blocked_resubmit.status_code == 409

    row = db_session.scalar(select(PublicRecipe).where(PublicRecipe.id == public_id))
    assert row is not None
    assert row.status == PublicRecipeStatus.delisted.value


def test_member_cannot_review_platform_queue(client, user_headers, admin_headers, catalog_seed):
    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Review Guard Dish")
    _add_ingredient_and_step(client, admin_headers, recipe["id"])
    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()
    forbidden = client.post(
        f"/api/platform/public-recipes/{submitted['id']}/approve",
        headers=user_headers,
        json={},
    )
    assert forbidden.status_code == 403


def test_withdraw_while_submitted(client, admin_headers, catalog_seed):
    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Withdraw Dish")
    _add_ingredient_and_step(client, admin_headers, recipe["id"])
    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()
    withdrawn = client.post(
        f"/api/household/publication-requests/{submitted['id']}/withdraw",
        headers=admin_headers,
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "withdrawn"

    again = client.post(
        f"/api/household/publication-requests/{submitted['id']}/withdraw",
        headers=admin_headers,
    )
    assert again.status_code == 409


def test_adopt_creates_independent_copy_with_provenance(
    client,
    admin_headers,
    second_household_headers,
    catalog_seed,
    db_session: Session,
):
    dish, recipe = _create_dish_with_recipe(
        client,
        admin_headers,
        "Adopt Source",
        dish_extras={
            "default_prep_time_minutes": 15,
            "default_cook_time_minutes": 30,
            "default_difficulty": "easy",
        },
    )
    source_dish = db_session.get(Dish, dish["id"])
    assert source_dish is not None
    assert source_dish.default_prep_time_minutes == 15
    assert source_dish.default_cook_time_minutes == 30
    assert source_dish.default_difficulty == "easy"

    _add_ingredient_and_step(client, admin_headers, recipe["id"])
    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()
    public_id = submitted["id"]
    approved = client.post(
        f"/api/platform/public-recipes/{public_id}/approve",
        headers=admin_headers,
        json={"review_note": "Looks good"},
    ).json()
    version_id = UUID(approved["current_version_id"])
    public_uuid = UUID(public_id)

    adopted = client.post(
        f"/api/public-recipes/{public_id}/adopt",
        headers=second_household_headers,
    )
    assert adopted.status_code == 201, adopted.text
    body = adopted.json()
    assert body["derived_from_public_recipe_id"] == public_id
    assert body["derived_from_public_version_id"] == str(version_id)

    adopted_recipe = db_session.get(Recipe, body["recipe_id"])
    assert adopted_recipe is not None
    assert adopted_recipe.derived_from_public_recipe_id == public_uuid
    assert adopted_recipe.derived_from_public_version_id == version_id

    adopted_dish = db_session.get(Dish, body["dish_id"])
    assert adopted_dish is not None
    assert adopted_dish.name.startswith("Adopt Source")
    assert adopted_dish.default_prep_time_minutes == 15
    assert adopted_dish.default_cook_time_minutes == 30
    assert adopted_dish.default_difficulty == "easy"

    renamed = client.put(
        f"/api/dishes/{dish['id']}",
        headers=admin_headers,
        json={"name": "Adopt Source Changed"},
    )
    assert renamed.status_code == 200, renamed.text
    public_detail = client.get(
        f"/api/public-recipes/{public_id}",
        headers=second_household_headers,
    ).json()
    assert public_detail["snapshot"]["dish"]["name"] == "Adopt Source"

    delisted = client.post(
        f"/api/platform/public-recipes/{public_id}/delist",
        headers=admin_headers,
        json={"review_note": "Retired"},
    )
    assert delisted.status_code == 200
    still_there = client.get(
        f"/api/dishes/{body['dish_id']}",
        headers=second_household_headers,
    )
    assert still_there.status_code == 200
    assert still_there.json()["name"].startswith("Adopt Source")


def test_cross_household_cannot_publish_foreign_recipe(
    client,
    admin_headers,
    second_household_headers,
    catalog_seed,
):
    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Foreign Recipe")
    response = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=second_household_headers,
    )
    assert response.status_code == 404


def test_submit_requires_ingredient_and_step(client, admin_headers, catalog_seed):
    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Incomplete Publish")
    no_content = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    )
    assert no_content.status_code == 422
    assert "ingredient" in no_content.json()["error"]["message"].lower()

    ingredient = client.post(
        "/api/ingredients/confirm",
        headers=admin_headers,
        json={
            "action": "create",
            "proposed_name": "incomplete-only-ingredient",
            "display_name": "Incomplete ingredient",
        },
    )
    assert ingredient.status_code == 201, ingredient.text
    units = client.get("/api/units", headers=admin_headers).json()
    added = client.post(
        f"/api/recipes/{recipe['id']}/ingredients",
        headers=admin_headers,
        json={"ingredient_id": ingredient.json()["id"], "quantity": "1", "unit_id": units[0]["id"]},
    )
    assert added.status_code == 201, added.text

    no_steps = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    )
    assert no_steps.status_code == 422
    assert "step" in no_steps.json()["error"]["message"].lower()


def test_cannot_delete_submitted_or_public_source(
    client,
    admin_headers,
    catalog_seed,
):
    dish, recipe = _create_dish_with_recipe(client, admin_headers, "Protected Source")
    _add_ingredient_and_step(client, admin_headers, recipe["id"])
    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()

    blocked_recipe = client.delete(f"/api/recipes/{recipe['id']}", headers=admin_headers)
    assert blocked_recipe.status_code == 409
    blocked_dish = client.delete(f"/api/dishes/{dish['id']}", headers=admin_headers)
    assert blocked_dish.status_code == 409

    approved = client.post(
        f"/api/platform/public-recipes/{submitted['id']}/approve",
        headers=admin_headers,
        json={},
    )
    assert approved.status_code == 200

    still_blocked_recipe = client.delete(f"/api/recipes/{recipe['id']}", headers=admin_headers)
    assert still_blocked_recipe.status_code == 409
    still_blocked_dish = client.delete(f"/api/dishes/{dish['id']}", headers=admin_headers)
    assert still_blocked_dish.status_code == 409

    delisted = client.post(
        f"/api/platform/public-recipes/{submitted['id']}/delist",
        headers=admin_headers,
        json={"review_note": "Allow cleanup"},
    )
    assert delisted.status_code == 200
    deleted = client.delete(f"/api/dishes/{dish['id']}", headers=admin_headers)
    assert deleted.status_code == 204


def test_adopt_rolls_back_when_ingredient_copy_fails(
    client,
    admin_headers,
    second_household,
    catalog_seed,
    db_session: Session,
    monkeypatch,
):
    from mealroulette.services.catalog import CatalogService
    from mealroulette.services.public_catalog import PublicCatalogService

    _dish, recipe = _create_dish_with_recipe(client, admin_headers, "Atomic Adopt Source")
    _add_ingredient_and_step(client, admin_headers, recipe["id"])
    submitted = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()
    public_id = UUID(
        client.post(
            f"/api/platform/public-recipes/{submitted['id']}/approve",
            headers=admin_headers,
            json={},
        ).json()["id"]
    )

    def fail_ingredient(self, recipe_id, payload, *, commit=True):
        raise RuntimeError("forced ingredient copy failure")

    monkeypatch.setattr(CatalogService, "add_recipe_ingredient", fail_ingredient)
    service = PublicCatalogService(db_session)

    with pytest.raises(RuntimeError, match="forced ingredient copy failure"):
        service.adopt(public_recipe_id=public_id, household_id=second_household.id)

    db_session.rollback()

    leftover = db_session.scalar(
        select(Dish).where(
            Dish.household_id == second_household.id,
            Dish.name.like("Atomic Adopt Source%"),
        )
    )
    assert leftover is None


def test_migration_tables_exist(db_session: Session, catalog_seed):
    from sqlalchemy import inspect

    assert db_session.execute(select(PublicRecipe).limit(1)).all() == []

    insp = inspect(db_session.get_bind())
    assert "public_recipes" in insp.get_table_names()
    assert "public_recipe_versions" in insp.get_table_names()

    recipe_columns = {column["name"] for column in insp.get_columns("recipes")}
    assert "derived_from_public_recipe_id" in recipe_columns
    assert "derived_from_public_version_id" in recipe_columns

    version_uniques = {
        tuple(constraint["column_names"])
        for constraint in insp.get_unique_constraints("public_recipe_versions")
    }
    assert ("public_recipe_id", "version_number") in version_uniques
    assert ("public_recipe_id", "id") in version_uniques

    public_recipe_fks = {
        (tuple(fk["constrained_columns"]), tuple(fk["referred_columns"]), fk["referred_table"])
        for fk in insp.get_foreign_keys("public_recipes")
    }
    assert (
        ("id", "current_version_id"),
        ("public_recipe_id", "id"),
        "public_recipe_versions",
    ) in public_recipe_fks

    recipe_fks = {
        (tuple(fk["constrained_columns"]), tuple(fk["referred_columns"]), fk["referred_table"])
        for fk in insp.get_foreign_keys("recipes")
    }
    assert (
        ("derived_from_public_recipe_id", "derived_from_public_version_id"),
        ("public_recipe_id", "id"),
        "public_recipe_versions",
    ) in recipe_fks

    check_names = {constraint["name"] for constraint in insp.get_check_constraints("recipes")}
    assert "ck_recipes_derived_from_public_pair" in check_names


def test_create_dish_persists_default_timing_fields(client, admin_headers, catalog_seed, db_session: Session):
    created = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={
            "name": "Timed Defaults Dish",
            "default_prep_time_minutes": 12,
            "default_cook_time_minutes": 24,
            "default_difficulty": "medium",
        },
    )
    assert created.status_code == 201, created.text
    dish = db_session.get(Dish, created.json()["id"])
    assert dish is not None
    assert dish.default_prep_time_minutes == 12
    assert dish.default_cook_time_minutes == 24
    assert dish.default_difficulty == "medium"


def test_adopt_truncates_long_dish_name_collisions(
    client,
    admin_headers,
    second_household_headers,
    catalog_seed,
    db_session: Session,
):
    long_name = "A" * 255
    dish, recipe = _create_dish_with_recipe(client, admin_headers, long_name)
    _add_ingredient_and_step(client, admin_headers, recipe["id"])
    public_id = client.post(
        f"/api/recipes/{recipe['id']}/publish-request",
        headers=admin_headers,
    ).json()["id"]
    client.post(
        f"/api/platform/public-recipes/{public_id}/approve",
        headers=admin_headers,
        json={},
    )

    # Occupying the truncated base name forces the “(adopted)” candidate path.
    occupy = client.post(
        "/api/dishes",
        headers=second_household_headers,
        json={"name": long_name},
    )
    assert occupy.status_code == 201, occupy.text

    adopted = client.post(
        f"/api/public-recipes/{public_id}/adopt",
        headers=second_household_headers,
    )
    assert adopted.status_code == 201, adopted.text
    adopted_dish = db_session.get(Dish, adopted.json()["dish_id"])
    assert adopted_dish is not None
    assert len(adopted_dish.name) <= 255
    assert adopted_dish.name.endswith("(adopted)")


def test_concurrent_first_submission_claims_lineage_once(db_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fastapi import HTTPException
    from sqlalchemy.orm import sessionmaker

    from mealroulette.auth.security import hash_password
    from mealroulette.data.seed_catalog import seed_catalog_data
    from mealroulette.data.seed_taxonomy import seed_taxonomy_data
    from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
    from mealroulette.models.user import User, UserRole
    from mealroulette.schemas.catalog import (
        DishCreateRequest,
        IngredientCreateRequest,
        RecipeCreateRequest,
        RecipeIngredientCreateRequest,
        RecipeStepCreateRequest,
    )
    from mealroulette.services.catalog import CatalogService
    from mealroulette.services.public_catalog import PublicCatalogService

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    household_id = uuid.uuid4()
    with SessionLocal() as setup:
        seed_catalog_data(setup)
        seed_taxonomy_data(setup, commit=False)
        household = Household(id=household_id, name="Submit Race Household")
        admin = User(
            username=f"submit-race-{household_id.hex[:8]}",
            email=f"submit-race-{household_id.hex[:8]}@example.com",
            password_hash=hash_password("adminpassword"),
            role=UserRole.admin,
            active=True,
        )
        setup.add_all([household, admin])
        setup.flush()
        setup.add(
            HouseholdMembership(
                household_id=household_id,
                user_id=admin.id,
                role=HouseholdRole.household_admin,
                active=True,
            )
        )
        catalog = CatalogService(setup, household_id=household_id)
        ingredient = catalog.create_ingredient(
            IngredientCreateRequest(
                canonical_name="submit_race_spice",
                display_name="Submit Race Spice",
                food_group="vegetable",
                family="tomato_family",
            )
        )
        dish = catalog.create_dish(DishCreateRequest(name="Submit Race Dish"))
        recipe = catalog.create_recipe(
            dish.id,
            RecipeCreateRequest(variant_name="Main", is_main=True),
        )
        catalog.add_recipe_ingredient(
            recipe.id,
            RecipeIngredientCreateRequest(ingredient_id=ingredient.id, quantity="1"),
        )
        catalog.create_step(
            recipe.id,
            RecipeStepCreateRequest(step_number=1, instruction="Cook"),
        )
        setup.commit()
        recipe_id = recipe.id
        admin_id = admin.id

    start = Barrier(2)

    def race(_unused):
        start.wait(timeout=5)
        with SessionLocal() as session:
            user = session.get(User, admin_id)
            assert user is not None
            try:
                PublicCatalogService(session).submit_publish_request(
                    user=user,
                    household_id=household_id,
                    recipe_id=recipe_id,
                )
                return 201
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(race, (1, 2)))

    assert sorted(results) == [201, 409]
    with SessionLocal() as verify:
        lineages = list(
            verify.scalars(select(PublicRecipe).where(PublicRecipe.originating_recipe_id == recipe_id))
        )
        assert len(lineages) == 1
        assert lineages[0].status == PublicRecipeStatus.submitted.value


def test_concurrent_submit_versus_delete_serializes(db_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fastapi import HTTPException
    from sqlalchemy.orm import sessionmaker

    from mealroulette.auth.security import hash_password
    from mealroulette.data.seed_catalog import seed_catalog_data
    from mealroulette.data.seed_taxonomy import seed_taxonomy_data
    from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
    from mealroulette.models.user import User, UserRole
    from mealroulette.schemas.catalog import (
        DishCreateRequest,
        IngredientCreateRequest,
        RecipeCreateRequest,
        RecipeIngredientCreateRequest,
        RecipeStepCreateRequest,
    )
    from mealroulette.services.catalog import CatalogService
    from mealroulette.services.public_catalog import PublicCatalogService

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    household_id = uuid.uuid4()
    with SessionLocal() as setup:
        seed_catalog_data(setup)
        seed_taxonomy_data(setup, commit=False)
        household = Household(id=household_id, name="Submit Delete Race")
        admin = User(
            username=f"submit-delete-{household_id.hex[:8]}",
            email=f"submit-delete-{household_id.hex[:8]}@example.com",
            password_hash=hash_password("adminpassword"),
            role=UserRole.admin,
            active=True,
        )
        setup.add_all([household, admin])
        setup.flush()
        setup.add(
            HouseholdMembership(
                household_id=household_id,
                user_id=admin.id,
                role=HouseholdRole.household_admin,
                active=True,
            )
        )
        catalog = CatalogService(setup, household_id=household_id)
        ingredient = catalog.create_ingredient(
            IngredientCreateRequest(
                canonical_name="submit_delete_spice",
                display_name="Submit Delete Spice",
                food_group="vegetable",
                family="tomato_family",
            )
        )
        dish = catalog.create_dish(DishCreateRequest(name="Submit Delete Dish"))
        recipe = catalog.create_recipe(
            dish.id,
            RecipeCreateRequest(variant_name="Main", is_main=True),
        )
        catalog.add_recipe_ingredient(
            recipe.id,
            RecipeIngredientCreateRequest(ingredient_id=ingredient.id, quantity="1"),
        )
        catalog.create_step(
            recipe.id,
            RecipeStepCreateRequest(step_number=1, instruction="Cook"),
        )
        setup.commit()
        recipe_id = recipe.id
        admin_id = admin.id

    barrier = Barrier(2)

    def submit_worker():
        with SessionLocal() as session:
            user = session.get(User, admin_id)
            assert user is not None
            barrier.wait(timeout=5)
            try:
                PublicCatalogService(session).submit_publish_request(
                    user=user,
                    household_id=household_id,
                    recipe_id=recipe_id,
                )
                return "submit-ok"
            except HTTPException as exc:
                return f"submit-{exc.status_code}"

    def delete_worker():
        with SessionLocal() as session:
            barrier.wait(timeout=5)
            try:
                CatalogService(session, household_id=household_id).delete_recipe(recipe_id)
                return "delete-ok"
            except HTTPException as exc:
                return f"delete-{exc.status_code}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        submit_future = pool.submit(submit_worker)
        delete_future = pool.submit(delete_worker)
        results = sorted([submit_future.result(timeout=10), delete_future.result(timeout=10)])

    assert results in (
        ["delete-409", "submit-ok"],
        ["delete-ok", "submit-404"],
    )
    with SessionLocal() as verify:
        lineages = list(
            verify.scalars(select(PublicRecipe).where(PublicRecipe.originating_recipe_id == recipe_id))
        )
        recipe_row = verify.get(Recipe, recipe_id)
        if "submit-ok" in results:
            assert len(lineages) == 1
            assert recipe_row is not None
        else:
            assert lineages == []
            assert recipe_row is None
