import pytest

pytestmark = pytest.mark.integration


def test_list_units_requires_auth(client):
    response = client.get("/api/units")
    assert response.status_code == 401


def test_list_units_returns_seed_data(client, catalog_seed, admin_headers):
    response = client.get("/api/units", headers=admin_headers)
    assert response.status_code == 200
    symbols = {unit["symbol"] for unit in response.json()}
    assert {"g", "kg", "ml", "l", "tsp", "tbsp", "unit"}.issubset(symbols)


def test_regular_user_can_read_catalog(client, catalog_seed, user_headers):
    response = client.get("/api/tags", headers=user_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_non_admin_cannot_create_tag(client, catalog_seed, user_headers):
    response = client.post(
        "/api/tags",
        headers=user_headers,
        json={"name": "test", "family": "style"},
    )
    assert response.status_code == 403


def test_ingredient_resolve_confirm_create_flow(client, catalog_seed, admin_headers):
    resolve = client.post(
        "/api/ingredients/resolve",
        headers=admin_headers,
        json={"proposed_name": "Cherry Tomatoes"},
    )
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "none"

    confirm = client.post(
        "/api/ingredients/confirm",
        headers=admin_headers,
        json={
            "action": "create",
            "proposed_name": "Cherry Tomatoes",
            "display_name": "Cherry Tomatoes",
            "category": "vegetable",
        },
    )
    assert confirm.status_code == 201
    ingredient = confirm.json()
    assert ingredient["canonical_name"] == "cherry tomatoes"

    resolve_again = client.post(
        "/api/ingredients/resolve",
        headers=admin_headers,
        json={"proposed_name": "cherry tomatoes"},
    )
    assert resolve_again.status_code == 200
    assert resolve_again.json()["status"] == "exact"
    assert resolve_again.json()["ingredient"]["id"] == ingredient["id"]


def test_ingredient_confirm_map_alias(client, catalog_seed, admin_headers):
    tomato = client.post(
        "/api/ingredients/confirm",
        headers=admin_headers,
        json={"action": "create", "proposed_name": "Tomato", "display_name": "Tomato"},
    ).json()

    alias = client.post(
        "/api/ingredients/confirm",
        headers=admin_headers,
        json={
            "action": "alias",
            "proposed_name": "Tomatoes",
            "ingredient_id": tomato["id"],
        },
    )
    assert alias.status_code == 201

    resolve = client.post(
        "/api/ingredients/resolve",
        headers=admin_headers,
        json={"proposed_name": "Tomatoes"},
    )
    assert resolve.json()["status"] == "exact"
    assert resolve.json()["ingredient"]["id"] == tomato["id"]


def test_full_dish_recipe_flow(client, catalog_seed, admin_headers):
    tags = client.get("/api/tags?family=protein", headers=admin_headers).json()
    fish_tag = next(tag for tag in tags if tag["name"] == "fish")
    units = client.get("/api/units", headers=admin_headers).json()
    gram = next(unit for unit in units if unit["symbol"] == "g")

    salmon = client.post(
        "/api/ingredients/confirm",
        headers=admin_headers,
        json={"action": "create", "proposed_name": "Salmon", "display_name": "Salmon"},
    ).json()

    dish = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={
            "name": "Baked Salmon",
            "description": "Simple oven salmon",
            "default_servings": 2,
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "difficulty": "easy",
            "tag_ids": [fish_tag["id"]],
            "seasonality": {
                "seasonality_mode": "seasonal",
                "preferred_months": [3, 4, 5, 9, 10],
                "seasonality_strength": "medium",
            },
        },
    )
    assert dish.status_code == 201
    dish_body = dish.json()
    assert dish_body["name"] == "Baked Salmon"
    assert fish_tag["id"] in dish_body["tag_ids"]
    assert dish_body["seasonality"]["seasonality_mode"] == "seasonal"
    assert dish_body["seasonality"]["preferred_months"] == [3, 4, 5, 9, 10]

    recipe = client.post(
        f"/api/dishes/{dish_body['id']}/recipes",
        headers=admin_headers,
        json={"variant_name": "default", "servings": 2, "is_thermomix": False},
    )
    assert recipe.status_code == 201
    recipe_id = recipe.json()["id"]

    step = client.post(
        f"/api/recipes/{recipe_id}/steps",
        headers=admin_headers,
        json={"step_number": 1, "instruction": "Bake salmon at 200C for 20 minutes."},
    )
    assert step.status_code == 201

    unresolved = client.post(
        f"/api/recipes/{recipe_id}/ingredients",
        headers=admin_headers,
        json={"proposed_name": "Mystery Spice", "quantity": "1"},
    )
    assert unresolved.status_code == 409

    ingredient = client.post(
        f"/api/recipes/{recipe_id}/ingredients",
        headers=admin_headers,
        json={
            "ingredient_id": salmon["id"],
            "quantity": "400",
            "unit_id": gram["id"],
        },
    )
    assert ingredient.status_code == 201
    assert ingredient.json()["ingredient_id"] == salmon["id"]

    recipes = client.get(f"/api/dishes/{dish_body['id']}/recipes", headers=admin_headers)
    assert recipes.status_code == 200
    assert len(recipes.json()) == 1

    detail = client.get(f"/api/dishes/{dish_body['id']}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Baked Salmon"

    steps = client.get(f"/api/recipes/{recipe_id}/steps", headers=admin_headers)
    assert steps.status_code == 200
    assert len(steps.json()) == 1

    ingredients = client.get(f"/api/recipes/{recipe_id}/ingredients", headers=admin_headers)
    assert ingredients.status_code == 200
    assert len(ingredients.json()) == 1
