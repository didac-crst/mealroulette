import pytest

pytestmark = pytest.mark.integration


def test_export_full_includes_taxonomy_tables(client, catalog_seed, admin_headers):
    response = client.get("/api/export/full", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["format"] == "mealroulette.full_export"
    assert "food_groups" in payload["tables"]
    assert "ingredient_families" in payload["tables"]
    assert len(payload["tables"]["food_groups"]) >= 20
    assert len(payload["tables"]["ingredient_families"]) >= 60


def test_non_admin_cannot_export(client, catalog_seed, user_headers):
    response = client.get("/api/export/full", headers=user_headers)
    assert response.status_code == 403


def test_import_rejects_nonempty_database(client, catalog_seed, admin_headers):
    export = client.get("/api/export/full", headers=admin_headers).json()
    response = client.post("/api/import/full", headers=admin_headers, json=export)
    assert response.status_code == 409


def test_ingredient_unknown_family_rejected(client, catalog_seed, admin_headers):
    response = client.post(
        "/api/ingredients",
        headers=admin_headers,
        json={
            "canonical_name": "mystery herb",
            "display_name": "Mystery Herb",
            "family": "not_a_real_family",
        },
    )
    assert response.status_code == 422


def test_backup_settings_round_trip(client, catalog_seed, admin_headers):
    updated = client.put(
        "/api/backups/settings",
        headers=admin_headers,
        json={"enabled": True, "retention_days": 14, "run_time": "04:30:00"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["enabled"] is True
    assert body["retention_days"] == 14
    assert body["run_time"].startswith("04:30")


def test_export_omits_incomplete_backup_runs(client, catalog_seed, admin_headers, db_session, tmp_path, monkeypatch):
    from mealroulette.models.backup import BackupRun
    from mealroulette.models.enums import BackupRunStatus, BackupType
    from mealroulette.services.backup_service import BackupService

    incomplete = BackupRun(backup_type=BackupType.json_export, status=BackupRunStatus.running)
    db_session.add(incomplete)
    db_session.commit()

    payload = client.get("/api/export/full", headers=admin_headers).json()
    run_ids = {row["id"] for row in payload["tables"]["backup_runs"]}
    assert incomplete.id not in run_ids


def test_json_backup_snapshot_excludes_current_run(client, catalog_seed, admin_headers, db_session, tmp_path):
    from mealroulette.services.backup_service import BackupService

    service = BackupService(db_session)
    settings_row = service.get_settings_row()
    settings_row.backup_path = str(tmp_path)
    settings_row.include_json_export = True
    settings_row.include_pg_dump = False
    db_session.commit()

    run = service._run_json_export(settings_row)
    assert run.status == "succeeded"
    assert run.file_path is not None

    backup_path = tmp_path / run.file_path
    payload = __import__("json").loads(backup_path.read_text(encoding="utf-8"))
    run_ids = {row["id"] for row in payload["tables"]["backup_runs"]}
    assert run.id not in run_ids
    assert all(row.get("file_path") for row in payload["tables"]["backup_runs"])
