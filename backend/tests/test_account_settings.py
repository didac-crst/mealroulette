from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def test_change_password_requires_current_password(client, admin_token):
    bad = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"current_password": "wrongpassword", "new_password": "brandnewpass"},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["message"] == "Current password is incorrect"

    same = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"current_password": "adminpassword", "new_password": "adminpassword"},
    )
    assert same.status_code == 400
    assert same.json()["error"]["message"] == "New password must be different from the current password"

    ok = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"current_password": "adminpassword", "new_password": "brandnewpass"},
    )
    assert ok.status_code == 204

    old_login = client.post("/api/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert old_login.status_code == 401

    login = client.post("/api/auth/login", json={"username": "admin", "password": "brandnewpass"})
    assert login.status_code == 200


def test_change_password_revokes_refresh_tokens(client, admin_user):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert login.status_code == 200
    tokens = login.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    changed = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": "adminpassword", "new_password": f"rotated-{uuid4().hex[:8]}"},
    )
    assert changed.status_code == 204

    refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 401
