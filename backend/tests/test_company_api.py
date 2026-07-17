"""
Mission Control Company API Tests

Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
Tests for Company CRUD endpoints.
"""

from fastapi.testclient import TestClient

# ------------------------------------------------------------------ #
# List                                                                 #
# ------------------------------------------------------------------ #


def test_list_companies_empty(client: TestClient) -> None:
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_companies(client: TestClient) -> None:
    client.post(
        "/api/v1/companies",
        json={"name": "acme", "display_name": "Acme Corp"},
    )
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names = [c["name"] for c in data]
    assert "acme" in names


# ------------------------------------------------------------------ #
# Create                                                               #
# ------------------------------------------------------------------ #


def test_create_company(client: TestClient) -> None:
    response = client.post(
        "/api/v1/companies",
        json={
            "name": "globex",
            "display_name": "Globex Corporation",
            "status": "active",
            "license_type": "enterprise",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "globex"
    assert data["display_name"] == "Globex Corporation"
    assert data["status"] == "active"
    assert data["license_type"] == "enterprise"
    assert data["enabled"] is True
    assert data["is_global"] is False
    assert "id" in data
    assert "uuid" in data


def test_create_company_minimal(client: TestClient) -> None:
    response = client.post(
        "/api/v1/companies",
        json={"name": "minimal", "display_name": "Minimal Co"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "minimal"
    assert data["status"] == "active"
    assert data["max_sites"] == 10
    assert data["max_agents"] == 100
    assert data["max_users"] == 50


def test_create_company_duplicate_name(client: TestClient) -> None:
    client.post(
        "/api/v1/companies",
        json={"name": "dup", "display_name": "Dup Co"},
    )
    response = client.post(
        "/api/v1/companies",
        json={"name": "dup", "display_name": "Dup Co 2"},
    )
    assert response.status_code == 409


def test_create_company_empty_name(client: TestClient) -> None:
    response = client.post(
        "/api/v1/companies",
        json={"name": "", "display_name": "Empty"},
    )
    assert response.status_code == 422


# ------------------------------------------------------------------ #
# Get                                                                  #
# ------------------------------------------------------------------ #


def test_get_company(client: TestClient) -> None:
    create = client.post(
        "/api/v1/companies",
        json={"name": "getco", "display_name": "Get Co"},
    )
    company_id = create.json()["id"]
    response = client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "getco"
    assert data["site_count"] == 0
    assert data["agent_count"] == 0
    assert data["integration_count"] == 0


def test_get_company_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/companies/99999")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Update                                                               #
# ------------------------------------------------------------------ #


def test_update_company(client: TestClient) -> None:
    create = client.post(
        "/api/v1/companies",
        json={"name": "upco", "display_name": "Up Co"},
    )
    company_id = create.json()["id"]
    response = client.put(
        f"/api/v1/companies/{company_id}",
        json={"display_name": "Updated Co", "license_type": "pro"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Co"
    assert data["license_type"] == "pro"
    assert data["name"] == "upco"


def test_update_company_not_found(client: TestClient) -> None:
    response = client.put(
        "/api/v1/companies/99999",
        json={"display_name": "Ghost"},
    )
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Delete                                                               #
# ------------------------------------------------------------------ #


def test_delete_company(client: TestClient) -> None:
    create = client.post(
        "/api/v1/companies",
        json={"name": "delco", "display_name": "Del Co"},
    )
    company_id = create.json()["id"]
    response = client.delete(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    get_response = client.get(f"/api/v1/companies/{company_id}")
    assert get_response.status_code == 404


def test_delete_company_not_found(client: TestClient) -> None:
    response = client.delete("/api/v1/companies/99999")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Summary                                                              #
# ------------------------------------------------------------------ #


def test_company_summary(client: TestClient) -> None:
    client.post(
        "/api/v1/companies",
        json={"name": "sumco", "display_name": "Sum Co"},
    )
    response = client.get("/api/v1/companies/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names = [c["name"] for c in data]
    assert "sumco" in names
