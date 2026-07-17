"""
Tests for Scheduled Command CRUD API.

Sprint 2.1.8 - Remote Operations Finalization.
"""

from fastapi.testclient import TestClient


def _create_schedule(client: TestClient, host_id: int, **overrides) -> dict:
    payload = {
        "host_id": host_id,
        "command": "uptime",
        "cron_expression": "0 */6 * * *",
        "enabled": True,
    }
    payload.update(overrides)
    resp = client.post("/api/v1/remote/schedules", json=payload)
    assert resp.status_code == 201
    return resp.json()


class TestScheduledCommandCRUD:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/remote/schedules")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_create_schedule(self, client, sample_host):
        data = _create_schedule(client, sample_host.id)
        assert data["host_id"] == sample_host.id
        assert data["command"] == "uptime"
        assert data["cron_expression"] == "0 */6 * * *"
        assert data["enabled"] is True

    def test_get_schedule(self, client, sample_host):
        created = _create_schedule(client, sample_host.id)
        resp = client.get(f"/api/v1/remote/schedules/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["host_name"] == "Test Server"

    def test_get_nonexistent(self, client):
        resp = client.get("/api/v1/remote/schedules/9999")
        assert resp.status_code == 404

    def test_update_schedule(self, client, sample_host):
        created = _create_schedule(client, sample_host.id)
        resp = client.put(
            f"/api/v1/remote/schedules/{created['id']}",
            json={"command": "df -h", "enabled": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["command"] == "df -h"
        assert data["enabled"] is False

    def test_delete_schedule(self, client, sample_host):
        created = _create_schedule(client, sample_host.id)
        resp = client.delete(f"/api/v1/remote/schedules/{created['id']}")
        assert resp.status_code == 204

    def test_create_invalid_host(self, client):
        resp = client.post(
            "/api/v1/remote/schedules",
            json={"host_id": 9999, "command": "ls", "cron_expression": "0 * * * *"},
        )
        assert resp.status_code == 404

    def test_list_after_create(self, client, sample_host):
        _create_schedule(client, sample_host.id)
        _create_schedule(client, sample_host.id, command="df")
        resp = client.get("/api/v1/remote/schedules")
        assert resp.json()["count"] == 2

    def test_update_nonexistent(self, client):
        resp = client.put(
            "/api/v1/remote/schedules/9999",
            json={"command": "ls"},
        )
        assert resp.status_code == 404

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/v1/remote/schedules/9999")
        assert resp.status_code == 404
