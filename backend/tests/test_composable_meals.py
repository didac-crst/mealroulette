from datetime import date, timedelta

import pytest

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.services.planning import PlanningService


def _future_item(plan: dict, *, client=None, user_headers=None) -> dict:
    today = date.today()
    for item in plan["items"]:
        if date.fromisoformat(item["date"]) > today:
            return item
    if client is not None and user_headers is not None:
        week_start = date.fromisoformat(plan["week_start_date"])
        response = client.get(
            f"/api/meal-plans/{(week_start + timedelta(days=7)).isoformat()}",
            headers=user_headers,
        )
        if response.status_code == 200:
            next_plan = response.json()
            for item in next_plan["items"]:
                if date.fromisoformat(item["date"]) > today:
                    return item
    raise AssertionError("expected at least one future meal slot")


def _create_dish(client, admin_headers, name: str) -> dict:
    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": name, "status": "active"},
    ).json()
    recipe = client.post(
        f"/api/dishes/{dish['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Main", "is_main": True},
    ).json()
    dish["main_recipe_id"] = recipe["id"]
    return dish


def test_meal_slot_supports_multiple_manual_lines(client, catalog_seed, admin_headers, user_headers):
    first = _create_dish(client, admin_headers, "Composable Main")
    second = _create_dish(client, admin_headers, "Composable Side")

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    assigned = client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": first["id"],
            "mode": "replace_all",
        },
    )
    assert assigned.status_code == 200, assigned.text
    body = assigned.json()
    assert len(body["lines"]) == 1
    assert body["lines"][0]["source"] == "manual"
    assert body["title"] == "Composable Main"

    added = client.post(
        f"/api/meal-plan-items/{item['id']}/lines",
        headers=user_headers,
        json={"dish_id": second["id"]},
    )
    assert added.status_code == 200
    added_body = added.json()
    assert len(added_body["lines"]) == 2
    assert added_body["computed_traits_json"] is not None
    assert "food_group_weights" in added_body["computed_traits_json"]
    assert "food_group_grams" in added_body["computed_traits_json"]
    assert "total_trait_grams" in added_body["computed_traits_json"]
    assert added_body["title"] == "Composable Main + Composable Side"

    line_id = added_body["lines"][1]["id"]
    removed = client.delete(f"/api/meal-plan-item-lines/{line_id}", headers=user_headers)
    assert removed.status_code == 200
    assert len(removed.json()["lines"]) == 1


def test_do_not_plan_clears_lines_and_blocks_add(client, catalog_seed, admin_headers, user_headers):
    dish = _create_dish(client, admin_headers, "Do Not Plan Dish")
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": dish["id"],
            "mode": "replace_all",
        },
    )

    marked = client.post(
        f"/api/meal-plan-items/{item['id']}/do-not-plan",
        headers=user_headers,
        json={"remove_existing_lines": True},
    )
    assert marked.status_code == 200
    body = marked.json()
    assert body["planning_state"] == "do_not_plan"
    assert body["title"] == "Not planning"
    assert body["lines"] == []

    blocked = client.post(
        f"/api/meal-plan-items/{item['id']}/lines",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    assert blocked.status_code == 400

    reopened = client.post(f"/api/meal-plan-items/{item['id']}/reopen", headers=user_headers)
    assert reopened.status_code == 200
    assert reopened.json()["planning_state"] == "open"


def test_assign_add_mode_appends_line(client, catalog_seed, admin_headers, user_headers):
    first = _create_dish(client, admin_headers, "Add Mode Main")
    second = _create_dish(client, admin_headers, "Add Mode Extra")
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": first["id"],
            "mode": "replace_all",
        },
    )
    added = client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": second["id"],
            "mode": "add",
        },
    )
    assert added.status_code == 200
    assert len(added.json()["lines"]) == 2


def test_do_not_plan_rejects_locked_slot(client, catalog_seed, admin_headers, user_headers):
    dish = _create_dish(client, admin_headers, "Locked Do Not Plan Dish")
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": dish["id"],
            "mode": "replace_all",
        },
    )
    locked = client.post(f"/api/meal-plan-items/{item['id']}/lock", headers=user_headers)
    assert locked.status_code == 200

    blocked = client.post(
        f"/api/meal-plan-items/{item['id']}/do-not-plan",
        headers=user_headers,
        json={"remove_existing_lines": True},
    )
    assert blocked.status_code == 400


def test_add_line_rejects_duplicate_position(client, catalog_seed, admin_headers, user_headers):
    first = _create_dish(client, admin_headers, "Position Main")
    second = _create_dish(client, admin_headers, "Position Extra")
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": first["id"],
            "mode": "replace_all",
        },
    )
    conflict = client.post(
        f"/api/meal-plan-items/{item['id']}/lines",
        headers=user_headers,
        json={"dish_id": second["id"], "position": 0},
    )
    assert conflict.status_code == 409


def test_update_line_resolves_default_recipe_when_dish_changes(client, catalog_seed, admin_headers, user_headers):
    first = _create_dish(client, admin_headers, "Line Update First")
    second = _create_dish(client, admin_headers, "Line Update Second")
    second_recipe = client.post(
        f"/api/dishes/{second['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "Alt", "is_main": False},
    ).json()
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    assigned = client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": first["id"],
            "mode": "replace_all",
        },
    )
    assert assigned.status_code == 200
    line_id = assigned.json()["lines"][0]["id"]

    updated = client.put(
        f"/api/meal-plan-item-lines/{line_id}",
        headers=user_headers,
        json={"dish_id": second["id"]},
    )
    assert updated.status_code == 200, updated.text
    updated_line = updated.json()["lines"][0]
    assert updated_line["dish_id"] == second["id"]
    assert updated_line["recipe_id"] == second["main_recipe_id"]
    assert updated_line["recipe_id"] != second_recipe["id"]


def test_delete_line_reindexes_remaining_positions(client, catalog_seed, admin_headers, user_headers):
    first = _create_dish(client, admin_headers, "Delete Line First")
    second = _create_dish(client, admin_headers, "Delete Line Second")
    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": first["id"],
            "mode": "replace_all",
        },
    )
    added = client.post(
        f"/api/meal-plan-items/{item['id']}/lines",
        headers=user_headers,
        json={"dish_id": second["id"]},
    )
    assert added.status_code == 200
    lines = added.json()["lines"]
    assert [line["position"] for line in lines] == [0, 1]

    removed = client.delete(f"/api/meal-plan-item-lines/{lines[0]['id']}", headers=user_headers)
    assert removed.status_code == 200
    remaining = removed.json()["lines"]
    assert len(remaining) == 1
    assert remaining[0]["dish_id"] == second["id"]
    assert remaining[0]["position"] == 0


@pytest.mark.integration
def test_meal_traits_aggregate_across_fixture_dishes(client, catalog_seed, admin_headers, user_headers, db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)
    dishes = client.get("/api/dishes", headers=admin_headers).json()
    risotto = next(d for d in dishes if d["name"] == "Mushroom Risotto")
    puttanesca = next(d for d in dishes if d["name"] == "Spaghetti Puttanesca")

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_item(plan, client=client, user_headers=user_headers)

    assigned = client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": risotto["id"],
            "mode": "replace_all",
        },
    )
    assert assigned.status_code == 200
    single_total = assigned.json()["computed_traits_json"]["total_trait_grams"]

    added = client.post(
        f"/api/meal-plan-items/{item['id']}/lines",
        headers=user_headers,
        json={"dish_id": puttanesca["id"]},
    )
    assert added.status_code == 200
    traits = added.json()["computed_traits_json"]
    assert traits is not None
    assert traits["total_trait_grams"] > single_total
    assert traits["food_group_grams"]

    public = PlanningService(db_session).to_item_public(PlanningService(db_session)._load_item(item["id"]))
    assert public.computed_traits_json is not None
    assert public.computed_traits_json["total_trait_grams"] == traits["total_trait_grams"]
