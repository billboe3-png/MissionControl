"""
Mission Control Auth Tests

Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
Tests for authentication and user management.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.auth_dependency import get_current_user
from app.main import app
from app.services.auth_service import AuthService


@pytest.fixture()
def raw_client(db_session):
    """Client without auth override — for testing auth rejection."""
    from app.db import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    saved = app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
    if saved is not None:
        app.dependency_overrides[get_current_user] = saved

# ------------------------------------------------------------------ #
# Login                                                                #
# ------------------------------------------------------------------ #


def test_login_success(client: TestClient, db_session) -> None:
    AuthService.create_user(
        db_session,
        email="test@example.com",
        display_name="Test User",
        password="password123",
        role="global_admin",
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "global_admin"


def test_login_wrong_password(client: TestClient, db_session) -> None:
    AuthService.create_user(
        db_session,
        email="wrong@example.com",
        display_name="Wrong User",
        password="password123",
        role="readonly",
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


# ------------------------------------------------------------------ #
# Get Me                                                               #
# ------------------------------------------------------------------ #


def test_get_me(client: TestClient, db_session) -> None:
    AuthService.create_user(
        db_session,
        email="me@example.com",
        display_name="Me User",
        password="password123",
        role="operator",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "operator"


def test_get_me_no_auth(raw_client: TestClient) -> None:
    response = raw_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(raw_client: TestClient) -> None:
    response = raw_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401


# ------------------------------------------------------------------ #
# User Management                                                      #
# ------------------------------------------------------------------ #


def test_create_user(client: TestClient, db_session) -> None:
    AuthService.create_user(
        db_session,
        email="admin@example.com",
        display_name="Admin",
        password="password123",
        role="global_admin",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/auth/users",
        json={
            "email": "newuser@example.com",
            "display_name": "New User",
            "password": "password123",
            "role": "operator",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "operator"


def test_create_user_duplicate_email(client: TestClient, db_session) -> None:
    AuthService.create_user(
        db_session,
        email="dupadmin@example.com",
        display_name="Dup Admin",
        password="password123",
        role="global_admin",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "dupadmin@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    client.post(
        "/api/v1/auth/users",
        json={
            "email": "dup@example.com",
            "display_name": "Dup",
            "password": "password123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.post(
        "/api/v1/auth/users",
        json={
            "email": "dup@example.com",
            "display_name": "Dup 2",
            "password": "password123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


def test_create_user_readonly_cannot_create(
    client: TestClient, db_session
) -> None:
    AuthService.create_user(
        db_session,
        email="readonly@example.com",
        display_name="Readonly",
        password="password123",
        role="readonly",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "readonly@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/auth/users",
        json={
            "email": "shouldnot@example.com",
            "display_name": "Should Not",
            "password": "password123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_list_users(client: TestClient, db_session) -> None:
    AuthService.create_user(
        db_session,
        email="listadmin@example.com",
        display_name="List Admin",
        password="password123",
        role="global_admin",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "listadmin@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    emails = [u["email"] for u in data]
    assert "listadmin@example.com" in emails
