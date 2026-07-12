def test_food_groups_api(client, catalog_seed, user_headers):
    response = client.get("/api/food-groups", headers=user_headers)
    assert response.status_code == 200
    groups = response.json()
    assert len(groups) == 22
    assert groups[0]["id"] == "vegetable"


def test_food_group_families_api(client, catalog_seed, user_headers):
    response = client.get("/api/food-groups/vegetable/families", headers=user_headers)
    assert response.status_code == 200
    families = response.json()
    assert any(family["id"] == "tomato_family" for family in families)


def test_taxonomy_overview_api(client, catalog_seed, user_headers, db_session):
    response = client.get("/api/ingredient-taxonomy/overview", headers=user_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"]["food_groups"] == 22
    assert payload["totals"]["families"] >= 40


def test_classify_candidate_api(client, catalog_seed, user_headers):
    response = client.post(
        "/api/ingredients/classify-candidate",
        headers=user_headers,
        json={"name": "cherry tomato", "context": "small fresh tomatoes"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "cherry tomato"
    assert payload["status"] in {"exact", "guided_suggestions", "unknown"}


def test_resolve_v2_api(client, catalog_seed, user_headers, db_session):
    response = client.post(
        "/api/ingredients/resolve-v2",
        headers=user_headers,
        json={"proposed_name": "tomato"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"exact", "suggestions", "none"}
