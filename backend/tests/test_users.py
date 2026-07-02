import pytest

pytestmark = pytest.mark.integration


def test_users_list_requires_authentication(client):
    response = client.get("/api/users")

    assert response.status_code == 401


def test_users_list_rejects_non_admin(client, user_token):
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


def test_admin_can_list_users(client, admin_token, admin_user, regular_user):
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    usernames = {user["username"] for user in payload}
    assert usernames == {"admin", "household"}
    assert all("password_hash" not in user for user in payload)


def test_admin_can_create_user(client, admin_token):
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newuserpass",
            "role": "user",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["username"] == "newuser"
    assert payload["email"] == "newuser@example.com"
    assert payload["role"] == "user"
    assert "password_hash" not in payload


def test_created_user_can_log_in(client, admin_token):
    client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "loginme",
            "email": "loginme@example.com",
            "password": "loginmepass",
            "role": "user",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={"username": "loginme", "password": "loginmepass"},
    )

    assert response.status_code == 200
