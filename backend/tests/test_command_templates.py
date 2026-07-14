"""
Tests for Command Template CRUD API.

Sprint 2.1.8 - Remote Operations Finalization.
"""

import pytest
from fastapi.testclient import TestClient


def _create_template(client: TestClient, **overrides) -> dict:
    payload = {
        "name": "Test Template",
        "command": "uptime",
        "protocol": "ssh",
        "description": "Check uptime",
        "category": "monitoring",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/remote/templates", json=payload)
    assert resp.status_code == 201
    return resp.json()


class TestCommandTemplateCRUD:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/remote/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["items"] == []

    def test_create_template(self, client):
        data = _create_template(client)
        assert data["name"] == "Test Template"
        assert data["command"] == "uptime"
        assert data["protocol"] == "ssh"
        assert data["id"] is not None

    def test_create_duplicate_name(self, client):
        _create_template(client)
        resp = client.post(
            "/api/v1/remote/templates",
            json={"name": "Test Template", "command": "ls"},
        )
        assert resp.status_code == 409

    def test_get_template(self, client):
        created = _create_template(client)
        resp = client.get(f"/api/v1/remote/templates/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Template"

    def test_get_nonexistent(self, client):
        resp = client.get("/api/v1/remote/templates/9999")
        assert resp.status_code == 404

    def test_update_template(self, client):
        created = _create_template(client)
        resp = client.put(
            f"/api/v1/remote/templates/{created['id']}",
            json={"command": "df -h"},
        )
        assert resp.status_code == 200
        assert resp.json()["command"] == "df -h"

    def test_update_name_conflict(self, client):
        _create_template(client, name="Template A", command="a")
        t2 = _create_template(client, name="Template B", command="b")
        resp = client.put(
            f"/api/v1/remote/templates/{t2['id']}",
            json={"name": "Template A"},
        )
        assert resp.status_code == 409

    def test_delete_template(self, client):
        created = _create_template(client)
        resp = client.delete(f"/api/v1/remote/templates/{created['id']}")
        assert resp.status_code == 204
        resp = client.get(f"/api/v1/remote/templates/{created['id']}")
        assert resp.status_code == 404

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/v1/remote/templates/9999")
        assert resp.status_code == 404

    def test_list_after_create(self, client):
        _create_template(client, name="T1", command="a")
        _create_template(client, name="T2", command="b")
        resp = client.get("/api/v1/remote/templates")
        assert resp.json()["count"] == 2

    def test_invalid_protocol(self, client):
        resp = client.post(
            "/api/v1/remote/templates",
            json={"name": "X", "command": "ls", "protocol": "telnet"},
        )
        assert resp.status_code == 400

    def test_empty_command(self, client):
        resp = client.post(
            "/api/v1/remote/templates",
            json={"name": "X", "command": ""},
        )
        assert resp.status_code == 422

    def test_update_nonexistent(self, client):
        resp = client.put(
            "/api/v1/remote/templates/9999",
            json={"command": "ls"},
        )
        assert resp.status_code == 404


class TestExecuteTemplate:
    def test_execute_template_no_host(self, client, sample_host):
        created = _create_template(client, protocol="ssh")
        resp = client.post(
            f"/api/v1/remote/templates/{created['id']}/execute?host_id=9999"
        )
        assert resp.status_code == 404

    def test_execute_template_disabled_host(self, client, sample_disabled_host):
        created = _create_template(client, protocol="winrm")
        resp = client.post(
            f"/api/v1/remote/templates/{created['id']}/execute?host_id={sample_disabled_host.id}"
        )
        assert resp.status_code == 400
