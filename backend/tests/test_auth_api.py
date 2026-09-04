from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def unique_email() -> str:
    return f"api_test_{uuid4().hex}@example.com"


def register_user(email: str, password: str = "TestPassword123!") -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )
    return response.json()


def login_user(email: str, password: str = "TestPassword123!"):
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_user():
    email = unique_email()

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == email
    assert "id" in body
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_register_user_normalizes_email():
    email = unique_email()

    response = client.post(
        "/auth/register",
        json={
            "email": f"  {email.upper()}  ",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == email


def test_register_duplicate_email_returns_conflict():
    email = unique_email()

    first_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "AnotherPassword123!",
        },
    )

    assert second_response.status_code == 409


def test_login_returns_access_and_refresh_tokens():
    email = unique_email()

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    response = login_user(email)

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] > 0


def test_login_rejects_invalid_password():
    email = unique_email()

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    response = login_user(
        email,
        "WrongPassword123!",
    )

    assert response.status_code == 401


def test_login_rejects_unknown_user():
    response = login_user(
        unique_email(),
        "TestPassword123!",
    )

    assert response.status_code == 401


def test_refresh_rotates_refresh_token():
    email = unique_email()

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    login_response = login_user(email)

    assert login_response.status_code == 200

    tokens = login_response.json()
    old_refresh_token = tokens["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    new_tokens = refresh_response.json()

    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
    assert new_tokens["refresh_token"] != old_refresh_token
    assert new_tokens["token_type"] == "bearer"


def test_refresh_rejects_reused_refresh_token():
    email = unique_email()

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    login_response = login_user(email)

    assert login_response.status_code == 200

    old_refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert first_refresh.status_code == 200

    second_refresh = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert second_refresh.status_code == 401


def test_refresh_rejects_invalid_refresh_token():
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token",
        },
    )

    assert response.status_code == 401