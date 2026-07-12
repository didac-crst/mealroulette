import pytest


@pytest.mark.integration
def test_scheduler_settings_admin_only(client, catalog_seed, user_headers):
    response = client.get("/api/scheduler/settings", headers=user_headers)
    assert response.status_code == 403


@pytest.mark.integration
def test_scheduler_settings_and_planning_rules(client, catalog_seed, scheduler_seed, admin_headers):
    settings = client.get("/api/scheduler/settings", headers=admin_headers)
    assert settings.status_code == 200
    body = settings.json()
    assert body["enabled"] is False
    assert body["run_weekday"] == 4
    assert body["notify_planning_days"] == 7

    updated = client.put(
        "/api/scheduler/settings",
        headers=admin_headers,
        json={
            "enabled": True,
            "run_weekday": 4,
            "run_time": "17:30:00",
            "timezone": "Europe/Paris",
            "target_week_offset": 1,
            "notify_telegram": True,
            "notify_planning_days": 7,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is True
    assert updated.json()["run_time"].startswith("17:30")

    rules = client.get("/api/planning-rules/active", headers=admin_headers)
    assert rules.status_code == 200
    rules_body = rules.json()
    assert rules_body["name"] == "default"
    assert rules_body["rules"]["default_grams_per_count"] == 100
    assert rules_body["rules"]["vector_min_grams"] == 5

    rules_updated = client.put(
        "/api/planning-rules/active",
        headers=admin_headers,
        json={"rules": {**rules_body["rules"], "default_grams_per_count": 90}},
    )
    assert rules_updated.status_code == 200
    assert rules_updated.json()["rules"]["default_grams_per_count"] == 90
