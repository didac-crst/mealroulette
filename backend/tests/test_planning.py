from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.integration


def test_current_meal_plan_requires_auth(client):
    response = client.get("/api/meal-plans/current")
    assert response.status_code == 401


def test_current_meal_plan_scaffolds_week(client, catalog_seed, user_headers):
    response = client.get("/api/meal-plans/current", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert len(body["items"]) == 14
    slots = {(item["date"], item["meal_slot"]) for item in body["items"]}
    assert len(slots) == 14
    assert all(item["status"] == "planned" for item in body["items"])


def _item_on_date(plan, target_date: date, meal_slot: str):
    return next(
        item for item in plan["items"]
        if item["date"] == target_date.isoformat() and item["meal_slot"] == meal_slot
    )


def _past_or_today_item(plan):
    today = date.today()
    for item in plan["items"]:
        if date.fromisoformat(item["date"]) <= today:
            return item
    pytest.fail("expected at least one past or today meal slot")


def _future_item(plan):
    today = date.today()
    for item in plan["items"]:
        if date.fromisoformat(item["date"]) > today:
            return item
    pytest.fail("expected at least one future meal slot")


def _other_past_dinner(plan, exclude_id: int):
    today = date.today()
    candidates = [
        item
        for item in plan["items"]
        if item["meal_slot"] == "dinner"
        and item["id"] != exclude_id
        and date.fromisoformat(item["date"]) <= today
    ]
    if not candidates:
        pytest.skip("need another past or today dinner slot")
    return candidates[0]


def test_assign_dish_sets_main_recipe_and_mark_eaten(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Weeknight Pasta", "status": "active"},
    ).json()
    client.post(
        f"/api/dishes/{dish['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Classic", "is_main": True},
    )

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)

    assigned = client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    assert assigned.status_code == 200
    body = assigned.json()
    assert body["dish_name"] == "Weeknight Pasta"
    assert body["recipe_variant_name"] == "Classic"
    assert body["recipe_id"] is not None
    assert body["manually_selected"] is True

    eaten = client.post(
        f"/api/meal-plan-items/{item['id']}/mark-eaten",
        headers=user_headers,
    )
    assert eaten.status_code == 200
    assert eaten.json()["status"] == "eaten"

    history = client.get("/api/meal-history", headers=user_headers)
    assert history.status_code == 200
    assert any(entry["id"] == item["id"] for entry in history.json())


def test_recipe_must_belong_to_dish(client, catalog_seed, admin_headers, user_headers):
    dish_a = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Dish A", "status": "active"},
    ).json()
    dish_b = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Dish B", "status": "active"},
    ).json()
    recipe_b = client.post(
        f"/api/dishes/{dish_b['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "B-main", "is_main": True},
    ).json()

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)

    invalid = client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": dish_a["id"], "recipe_id": recipe_b["id"]},
    )
    assert invalid.status_code == 400


def test_future_date_status_rejected(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Future Dish", "status": "active"},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    future = _future_item(plan)

    client.put(
        f"/api/meal-plan-items/{future['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )

    for path in ("mark-eaten", "skip", "ate-leftovers"):
        response = client.post(f"/api/meal-plan-items/{future['id']}/{path}", headers=user_headers, json={})
        assert response.status_code == 400, path


def test_locked_item_rejects_assignment_but_allows_execution(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Locked Soup", "status": "active"},
    ).json()
    other = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Other Dish", "status": "active"},
    ).json()

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)

    client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    locked = client.post(f"/api/meal-plan-items/{item['id']}/lock", headers=user_headers)
    assert locked.status_code == 200
    assert locked.json()["is_locked"] is True

    rejected = client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": other["id"]},
    )
    assert rejected.status_code == 400

    eaten = client.post(f"/api/meal-plan-items/{item['id']}/mark-eaten", headers=user_headers)
    assert eaten.status_code == 200
    assert eaten.json()["status"] == "eaten"


def test_lock_requires_dish(client, catalog_seed, user_headers):
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)
    response = client.post(f"/api/meal-plan-items/{item['id']}/lock", headers=user_headers)
    assert response.status_code == 400


def test_skip_lock_and_ate_leftovers(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Soup", "status": "active"},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    week_start = date.fromisoformat(plan["week_start_date"])
    monday_dinner = _item_on_date(plan, week_start, "dinner")
    tuesday_lunch = _item_on_date(plan, week_start + timedelta(days=1), "lunch")
    if date.fromisoformat(tuesday_lunch["date"]) > date.today():
        pytest.skip("need tuesday lunch on or before today")
    other_dinner = _other_past_dinner(plan, monday_dinner["id"])

    client.put(
        f"/api/meal-plan-items/{monday_dinner['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    eaten = client.post(f"/api/meal-plan-items/{monday_dinner['id']}/mark-eaten", headers=user_headers)
    assert eaten.status_code == 200

    ate_leftovers = client.post(
        f"/api/meal-plan-items/{tuesday_lunch['id']}/ate-leftovers",
        headers=user_headers,
        json={"leftover_source_item_id": monday_dinner["id"]},
    )
    assert ate_leftovers.status_code == 200
    assert ate_leftovers.json()["status"] == "ate_leftovers"
    assert ate_leftovers.json()["dish_name"] == "Soup"
    assert ate_leftovers.json()["review_saved_at"] is None

    skipped = client.post(
        f"/api/meal-plan-items/{other_dinner['id']}/skip",
        headers=user_headers,
        json={"skip_reason": "ate_outside", "skip_comment": "Restaurant"},
    )
    assert skipped.status_code == 200
    assert skipped.json()["status"] == "skipped"
    assert skipped.json()["review_saved_at"] is not None

    invalid_leftovers = client.post(
        f"/api/meal-plan-items/{tuesday_lunch['id']}/ate-leftovers",
        headers=user_headers,
        json={"leftover_source_item_id": other_dinner["id"]},
    )
    assert invalid_leftovers.status_code == 400


def test_ate_leftovers_meal_not_valid_as_leftover_source(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Chain Dish", "status": "active"},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    week_start = date.fromisoformat(plan["week_start_date"])
    monday_dinner = _item_on_date(plan, week_start, "dinner")
    tuesday_lunch = _item_on_date(plan, week_start + timedelta(days=1), "lunch")
    wednesday_lunch = _item_on_date(plan, week_start + timedelta(days=2), "lunch")

    if date.fromisoformat(wednesday_lunch["date"]) > date.today():
        pytest.skip("need wednesday lunch on or before today")

    client.put(
        f"/api/meal-plan-items/{monday_dinner['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    client.post(f"/api/meal-plan-items/{monday_dinner['id']}/mark-eaten", headers=user_headers)
    client.post(
        f"/api/meal-plan-items/{tuesday_lunch['id']}/ate-leftovers",
        headers=user_headers,
        json={"leftover_source_item_id": monday_dinner["id"]},
    )

    chain = client.post(
        f"/api/meal-plan-items/{wednesday_lunch['id']}/ate-leftovers",
        headers=user_headers,
        json={"leftover_source_item_id": tuesday_lunch["id"]},
    )
    assert chain.status_code == 400
    assert "eaten" in chain.json()["error"]["message"].lower()


def test_meal_rating_upsert(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Ratings Dish", "status": "active"},
    ).json()
    client.post(
        f"/api/dishes/{dish['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Default", "is_main": True},
    )

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)
    client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    client.post(f"/api/meal-plan-items/{item['id']}/mark-eaten", headers=user_headers)

    created = client.post(
        f"/api/meal-plan-items/{item['id']}/rating",
        headers=user_headers,
        json={"rating": 4, "comment": "Great"},
    )
    assert created.status_code == 200
    assert created.json()["rating"]["rating"] == 4
    assert created.json()["rating"]["dish_id"] == dish["id"]
    assert created.json()["rating"]["recipe_id"] is not None
    assert created.json()["item"]["review_saved_at"] is not None

    updated = client.post(
        f"/api/meal-plan-items/{item['id']}/rating",
        headers=user_headers,
        json={"rating": 5},
    )
    assert updated.status_code == 200
    assert updated.json()["rating"]["rating"] == 5

    listed = client.get(f"/api/meal-plan-items/{item['id']}/rating", headers=user_headers)
    assert listed.status_code == 200
    assert listed.json()["rating"] == 5


def test_update_item_rejects_status_change(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Status Guard Dish", "status": "active"},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)
    client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )

    response = client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"status": "eaten"},
    )
    assert response.status_code == 400


def test_reset_status_to_planned(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Reset Dish", "status": "active"},
    ).json()
    client.post(
        f"/api/dishes/{dish['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Default", "is_main": True},
    )

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _past_or_today_item(plan)
    client.put(
        f"/api/meal-plan-items/{item['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    client.post(f"/api/meal-plan-items/{item['id']}/mark-eaten", headers=user_headers)
    client.post(
        f"/api/meal-plan-items/{item['id']}/rating",
        headers=user_headers,
        json={"rating": 4, "comment": "Nice"},
    )

    reset = client.post(f"/api/meal-plan-items/{item['id']}/reset-status", headers=user_headers)
    assert reset.status_code == 200
    body = reset.json()
    assert body["status"] == "planned"
    assert body["dish_id"] == dish["id"]
    assert body["recipe_id"] is not None
    assert body["is_locked"] is False
    assert body["leftover_source_item_id"] is None
    assert body["skip_reason"] is None

    rating = client.get(f"/api/meal-plan-items/{item['id']}/rating", headers=user_headers)
    assert rating.status_code == 200
    assert rating.json() is None

    no_op = client.post(f"/api/meal-plan-items/{item['id']}/reset-status", headers=user_headers)
    assert no_op.status_code == 200
    assert no_op.json()["status"] == "planned"


def test_review_saved_after_rating(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Review Saved Dish", "status": "active"},
    ).json()
    client.post(
        f"/api/dishes/{dish['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Default", "is_main": True},
    )

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    meal_item = _past_or_today_item(plan)
    client.put(
        f"/api/meal-plan-items/{meal_item['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    eaten = client.post(f"/api/meal-plan-items/{meal_item['id']}/mark-eaten", headers=user_headers)
    assert eaten.status_code == 200
    assert eaten.json()["review_saved_at"] is None

    rated = client.post(
        f"/api/meal-plan-items/{meal_item['id']}/rating",
        headers=user_headers,
        json={"rating": 4},
    )
    assert rated.status_code == 200

    refreshed = client.get("/api/meal-plans/current", headers=user_headers).json()
    saved_item = next(item for item in refreshed["items"] if item["id"] == meal_item["id"])
    assert saved_item["review_saved_at"] is not None


def test_ate_leftovers_review_saved_on_source_confirm(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Leftover Confirm", "status": "active"},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    week_start = date.fromisoformat(plan["week_start_date"])
    monday_dinner = _item_on_date(plan, week_start, "dinner")
    tuesday_lunch = _item_on_date(plan, week_start + timedelta(days=1), "lunch")

    if date.fromisoformat(tuesday_lunch["date"]) > date.today():
        pytest.skip("need tuesday lunch on or before today")

    client.put(
        f"/api/meal-plan-items/{monday_dinner['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    client.post(f"/api/meal-plan-items/{monday_dinner['id']}/mark-eaten", headers=user_headers)
    ate = client.post(
        f"/api/meal-plan-items/{tuesday_lunch['id']}/ate-leftovers",
        headers=user_headers,
        json={},
    )
    assert ate.status_code == 200
    assert ate.json()["review_saved_at"] is None

    confirmed = client.put(
        f"/api/meal-plan-items/{tuesday_lunch['id']}",
        headers=user_headers,
        json={"leftover_source_item_id": monday_dinner["id"]},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["review_saved_at"] is not None
    assert confirmed.json()["leftover_source_item_id"] == monday_dinner["id"]


def test_future_meal_rating_rejected(client, catalog_seed, admin_headers, user_headers):
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Future Rated", "status": "active"},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    future = _future_item(plan)
    client.put(
        f"/api/meal-plan-items/{future['id']}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )

    response = client.post(
        f"/api/meal-plan-items/{future['id']}/rating",
        headers=user_headers,
        json={"rating": 5},
    )
    assert response.status_code == 400
