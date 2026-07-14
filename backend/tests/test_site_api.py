"""
Tests for Site API endpoints.

Sprint 2.9 - Multi-Site Management.
"""

import pytest


# ------------------------------------------------------------------ #
# List                                                                #
# ------------------------------------------------------------------ #


def test_list_sites_empty(client):
    response = client.get("/api/v1/sites")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["items"] == []


def test_list_sites(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    client.post(
        "/api/v1/sites",
        json={"name": "Branch", "code": "branch"},
    )

    response = client.get("/api/v1/sites")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    names = [s["name"] for s in data["items"]]
    assert "HQ" in names
    assert "Branch" in names


# ------------------------------------------------------------------ #
# Summary                                                             #
# ------------------------------------------------------------------ #


def test_list_site_summaries(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq", "color": "#ff0000"},
    )

    response = client.get("/api/v1/sites/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "HQ"
    assert data[0]["color"] == "#ff0000"
    assert "description" not in data[0]


# ------------------------------------------------------------------ #
# Create                                                              #
# ------------------------------------------------------------------ #


def test_create_site(client):
    response = client.post(
        "/api/v1/sites",
        json={
            "name": "New York Office",
            "code": "nyc",
            "description": "NYC headquarters",
            "color": "#3b82f6",
            "icon": "🏢",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New York Office"
    assert data["code"] == "nyc"
    assert data["description"] == "NYC headquarters"
    assert data["color"] == "#3b82f6"
    assert data["icon"] == "🏢"
    assert data["enabled"] is True
    assert data["is_default"] is False
    assert data["id"] is not None


def test_create_site_minimal(client):
    response = client.post(
        "/api/v1/sites",
        json={"name": "Minimal Site", "code": "minimal"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Site"
    assert data["code"] == "minimal"
    assert data["color"] is None
    assert data["description"] is None


def test_create_site_duplicate_name(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    response = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq2"},
    )
    assert response.status_code == 409
    assert "name already exists" in response.json()["detail"]


def test_create_site_duplicate_code(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    response = client.post(
        "/api/v1/sites",
        json={"name": "Branch", "code": "hq"},
    )
    assert response.status_code == 409
    assert "code already exists" in response.json()["detail"]


def test_create_site_empty_name(client):
    response = client.post(
        "/api/v1/sites",
        json={"name": "", "code": "empty"},
    )
    assert response.status_code == 422


def test_create_site_empty_code(client):
    response = client.post(
        "/api/v1/sites",
        json={"name": "No Code", "code": ""},
    )
    assert response.status_code == 422


def test_create_site_code_is_lowercased(client):
    response = client.post(
        "/api/v1/sites",
        json={"name": "Upper", "code": "UPPER"},
    )
    assert response.status_code == 201
    assert response.json()["code"] == "upper"


# ------------------------------------------------------------------ #
# Get                                                                 #
# ------------------------------------------------------------------ #


def test_get_site(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    site_id = create.json()["id"]

    response = client.get(f"/api/v1/sites/{site_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "HQ"
    assert response.json()["code"] == "hq"


def test_get_site_not_found(client):
    response = client.get("/api/v1/sites/9999")
    assert response.status_code == 404


def test_get_site_by_code(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )

    response = client.get("/api/v1/sites/code/hq")
    assert response.status_code == 200
    assert response.json()["name"] == "HQ"


def test_get_site_by_code_not_found(client):
    response = client.get("/api/v1/sites/code/nonexistent")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Update                                                              #
# ------------------------------------------------------------------ #


def test_update_site(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    site_id = create.json()["id"]

    response = client.put(
        f"/api/v1/sites/{site_id}",
        json={"name": "Headquarters", "color": "#00ff00"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Headquarters"
    assert response.json()["color"] == "#00ff00"
    assert response.json()["code"] == "hq"


def test_update_site_not_found(client):
    response = client.put(
        "/api/v1/sites/9999",
        json={"name": "Updated"},
    )
    assert response.status_code == 404


def test_update_site_name_conflict(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    create2 = client.post(
        "/api/v1/sites",
        json={"name": "Branch", "code": "branch"},
    )
    site2_id = create2.json()["id"]

    response = client.put(
        f"/api/v1/sites/{site2_id}",
        json={"name": "HQ"},
    )
    assert response.status_code == 409


def test_update_site_code_conflict(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    create2 = client.post(
        "/api/v1/sites",
        json={"name": "Branch", "code": "branch"},
    )
    site2_id = create2.json()["id"]

    response = client.put(
        f"/api/v1/sites/{site2_id}",
        json={"code": "hq"},
    )
    assert response.status_code == 409


# ------------------------------------------------------------------ #
# Delete                                                              #
# ------------------------------------------------------------------ #


def test_delete_site(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    site_id = create.json()["id"]

    response = client.delete(f"/api/v1/sites/{site_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/sites/{site_id}")
    assert get_response.status_code == 404


def test_delete_site_not_found(client):
    response = client.delete("/api/v1/sites/9999")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Enable / Disable                                                    #
# ------------------------------------------------------------------ #


def test_enable_site(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq", "enabled": False},
    )
    site_id = create.json()["id"]
    assert create.json()["enabled"] is False

    response = client.post(f"/api/v1/sites/{site_id}/enable")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_disable_site(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    site_id = create.json()["id"]
    assert create.json()["enabled"] is True

    response = client.post(f"/api/v1/sites/{site_id}/disable")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_enable_site_not_found(client):
    response = client.post("/api/v1/sites/9999/enable")
    assert response.status_code == 404


def test_disable_site_not_found(client):
    response = client.post("/api/v1/sites/9999/disable")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Health                                                              #
# ------------------------------------------------------------------ #


def test_get_site_health_empty(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    site_id = create.json()["id"]

    response = client.get(f"/api/v1/sites/{site_id}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["health"] == "unknown"
    assert data["integration_count"] == 0
    assert data["host_count"] == 0


def test_get_site_health_disabled_site(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq", "enabled": False},
    )
    site_id = create.json()["id"]

    response = client.get(f"/api/v1/sites/{site_id}/health")
    assert response.status_code == 200
    assert response.json()["health"] == "critical"
    assert "Site is disabled" in response.json()["issues"]


def test_get_all_sites_health(client):
    client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    client.post(
        "/api/v1/sites",
        json={"name": "Branch", "code": "branch", "enabled": False},
    )

    response = client.get("/api/v1/sites/health")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ------------------------------------------------------------------ #
# Default Site                                                        #
# ------------------------------------------------------------------ #


def test_create_default_site(client):
    response = client.post(
        "/api/v1/sites",
        json={
            "name": "Default",
            "code": "default",
            "is_default": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["is_default"] is True


def test_create_second_default_clears_first(client):
    client.post(
        "/api/v1/sites",
        json={
            "name": "First Default",
            "code": "first",
            "is_default": True,
        },
    )
    response = client.post(
        "/api/v1/sites",
        json={
            "name": "Second Default",
            "code": "second",
            "is_default": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["is_default"] is True

    sites = client.get("/api/v1/sites").json()["items"]
    defaults = [s for s in sites if s["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["code"] == "second"


# ------------------------------------------------------------------ #
# Computed Fields                                                     #
# ------------------------------------------------------------------ #


def test_site_includes_computed_counts(client):
    create = client.post(
        "/api/v1/sites",
        json={"name": "HQ", "code": "hq"},
    )
    site_id = create.json()["id"]

    response = client.get(f"/api/v1/sites/{site_id}")
    data = response.json()
    assert "integration_count" in data
    assert "host_count" in data
    assert data["integration_count"] == 0
    assert data["host_count"] == 0
