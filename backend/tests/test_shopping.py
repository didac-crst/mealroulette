from datetime import date, timedelta

import pytest

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures


def _past_or_today_item(plan):
    today = date.today()
    for item in plan["items"]:
        if date.fromisoformat(item["date"]) <= today:
            return item
    pytest.fail("expected at least one past or today meal slot")


def _future_items(plan, count: int = 2):
    today = date.today()
    items = [item for item in plan["items"] if date.fromisoformat(item["date"]) > today]
    if len(items) < count:
        pytest.skip("need future meal slots")
    return items[:count]


def _assign_dish(client, user_headers, admin_headers, item_id: int, dish_name: str):
    dishes = client.get("/api/dishes", headers=admin_headers).json()
    dish = next(d for d in dishes if d["name"] == dish_name)
    response = client.put(
        f"/api/meal-plan-items/{item_id}",
        headers=user_headers,
        json={"dish_id": dish["id"]},
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.integration
def test_preview_shopping_list_from_planned_meals(client, catalog_seed, admin_headers, user_headers, db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    slots = _future_items(plan, 2)
    _assign_dish(client, user_headers, admin_headers, slots[0]["id"], "Mushroom Risotto")
    _assign_dish(client, user_headers, admin_headers, slots[1]["id"], "Spaghetti Puttanesca")

    from_date = date.fromisoformat(slots[0]["date"])
    preview = client.get(
        "/api/shopping-list",
        headers=user_headers,
        params={"from": from_date.isoformat(), "days": 3, "exclude_pantry": True},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["from_date"] == from_date.isoformat()
    assert body["to_date"] == (from_date + timedelta(days=2)).isoformat()
    assert len(body["items"]) > 0
    first_item = body["items"][0]
    assert first_item["source_contributions"]
    assert first_item["source_contributions"][0]["quantity"]
    assert first_item["source_contributions"][0]["dish_name"]
    assert body["planned_meals"]
    assert body["planned_meals"][0]["date"] <= body["planned_meals"][-1]["date"]
    categories = {item["category"] for item in body["items"]}
    assert len(categories) >= 1


@pytest.mark.integration
def test_create_and_check_off_shopping_list(client, catalog_seed, admin_headers, user_headers, db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    slot = _future_items(plan, 1)[0]
    _assign_dish(client, user_headers, admin_headers, slot["id"], "Mushroom Risotto")

    from_date = date.fromisoformat(slot["date"])
    created = client.post(
        "/api/shopping-lists",
        headers=user_headers,
        json={"from_date": from_date.isoformat(), "days": 2, "exclude_pantry": True},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["id"] is not None
    assert len(body["items"]) > 0

    item_id = body["items"][0]["id"]
    updated = client.put(
        f"/api/shopping-list-items/{item_id}",
        headers=user_headers,
        json={"checked": True},
    )
    assert updated.status_code == 200
    assert updated.json()["checked"] is True

    loaded = client.get(f"/api/shopping-lists/{body['id']}", headers=user_headers)
    assert loaded.status_code == 200
    assert loaded.json()["items"][0]["checked"] is True


@pytest.mark.integration
def test_skipped_meals_excluded_from_shopping_list(client, catalog_seed, admin_headers, user_headers, db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    slot = _past_or_today_item(plan)
    _assign_dish(client, user_headers, admin_headers, slot["id"], "Mushroom Risotto")
    client.post(f"/api/meal-plan-items/{slot['id']}/skip", headers=user_headers, json={})

    from_date = date.fromisoformat(slot["date"])
    preview = client.get(
        "/api/shopping-list",
        headers=user_headers,
        params={"from": from_date.isoformat(), "days": 1},
    )
    assert preview.status_code == 200
    assert preview.json()["items"] == []


@pytest.mark.integration
def test_carrot_mass_and_count_merge_with_conversion(client, catalog_seed, admin_headers, user_headers, db_session):
    from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH, import_ingredient_seed

    import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    slots = _future_items(plan, 2)
    _assign_dish(client, user_headers, admin_headers, slots[0]["id"], "Dukkah Carrot Strudel")
    _assign_dish(client, user_headers, admin_headers, slots[1]["id"], "Pan-Fried Hake with Lentils and Leeks")

    from_date = date.fromisoformat(slots[0]["date"])
    preview = client.get(
        "/api/shopping-list",
        headers=user_headers,
        params={"from": from_date.isoformat(), "days": 3},
    )
    assert preview.status_code == 200
    carrot_lines = [item for item in preview.json()["items"] if item["display_name"].lower() == "carrot"]
    assert len(carrot_lines) == 1
    carrot = carrot_lines[0]
    assert carrot["unit_symbol"] == "g"
    assert carrot["approximate"] is True
    assert float(carrot["quantity"]) == 860
    assert len(carrot["raw_components"]) == 2
