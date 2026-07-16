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


def test_change_password_enforces_bcrypt_byte_limit(client, admin_token):
    exactly_72 = "a" * 72
    too_long = "a" * 73
    # Two-byte UTF-8 characters: 36 * 2 = 72 bytes.
    multibyte_ok = "é" * 36
    multibyte_too_long = "é" * 37

    ok = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"current_password": "adminpassword", "new_password": exactly_72},
    )
    assert ok.status_code == 204

    login = client.post("/api/auth/login", json={"username": "admin", "password": exactly_72})
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    rejected = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": exactly_72, "new_password": too_long},
    )
    assert rejected.status_code == 422

    multibyte = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": exactly_72, "new_password": multibyte_ok},
    )
    assert multibyte.status_code == 204

    login = client.post("/api/auth/login", json={"username": "admin", "password": multibyte_ok})
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    multibyte_rejected = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": multibyte_ok, "new_password": multibyte_too_long},
    )
    assert multibyte_rejected.status_code == 422
