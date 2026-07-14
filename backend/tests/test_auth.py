import pytest

from mealroulette.auth.security import hash_password, verify_password

pytestmark = pytest.mark.integration


def test_hash_and_verify_password():
    password_hash = hash_password("strong-password")
    assert verify_password("strong-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_token_endpoint_returns_tokens(client, admin_user):
    response = client.post(
        "/api/auth/token",
        data={"username": "admin", "password": "adminpassword"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_login_returns_tokens(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_login_rejects_invalid_password(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_returns_public_user_fields_only(client, admin_token, admin_user):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == admin_user.username
    assert payload["email"] == admin_user.email
    assert payload["role"] == "admin"
    assert "platform_admin" in payload["platform_roles"]
    assert payload["active_household_id"] is not None
    assert "password_hash" not in payload


def test_refresh_issues_new_tokens(client, admin_user):
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["refresh_token"] != refresh_token


def test_logout_revokes_refresh_token(client, admin_user):
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 401
