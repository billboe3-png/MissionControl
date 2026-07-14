"""
Tests for Bulk Command Execution API.

Sprint 2.1.8 - Remote Operations Finalization.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


MOCK_EXEC_RESULT = {
    "stdout": "ok",
    "stderr": "",
    "exit_code": 0,
    "success": True,
    "duration_ms": 50,
}


def _mock_execute(*args, **kwargs):
    return MOCK_EXEC_RESULT


class TestBulkExecute:
    def test_empty_host_ids(self, client):
        resp = client.post(
            "/api/v1/remote/bulk-execute",
            json={"host_ids": [], "command": "uptime"},
        )
        assert resp.status_code == 422

    def test_single_host_success(self, client, sample_host):
        with patch(
            "app.services.remote_service.get_remote_provider"
        ) as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.execute_command = AsyncMock(
                return_value=MOCK_EXEC_RESULT
            )
            mock_factory.return_value = mock_provider

            resp = client.post(
                "/api/v1/remote/bulk-execute",
                json={
                    "host_ids": [sample_host.id],
                    "command": "uptime",
                    "shell": "bash",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["succeeded"] == 1
            assert data["failed"] == 0
            assert data["results"][0]["success"] is True

    def test_nonexistent_host(self, client, sample_host):
        with patch(
            "app.services.remote_service.get_remote_provider"
        ) as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.execute_command = AsyncMock(
                return_value=MOCK_EXEC_RESULT
            )
            mock_factory.return_value = mock_provider

            resp = client.post(
                "/api/v1/remote/bulk-execute",
                json={
                    "host_ids": [9999],
                    "command": "uptime",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["failed"] == 1
            assert "not found" in data["results"][0]["stderr"].lower()

    def test_disabled_host(self, client, sample_disabled_host):
        with patch(
            "app.services.remote_service.get_remote_provider"
        ) as mock_factory:
            mock_provider = AsyncMock()
            mock_factory.return_value = mock_provider

            resp = client.post(
                "/api/v1/remote/bulk-execute",
                json={
                    "host_ids": [sample_disabled_host.id],
                    "command": "uptime",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["failed"] == 1
            assert "disabled" in data["results"][0]["stderr"].lower()

    def test_mixed_results(self, client, sample_host, sample_disabled_host):
        with patch(
            "app.services.remote_service.get_remote_provider"
        ) as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.execute_command = AsyncMock(
                return_value=MOCK_EXEC_RESULT
            )
            mock_factory.return_value = mock_provider

            resp = client.post(
                "/api/v1/remote/bulk-execute",
                json={
                    "host_ids": [sample_host.id, sample_disabled_host.id],
                    "command": "uptime",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert data["succeeded"] == 1
            assert data["failed"] == 1

    def test_multiple_success(self, client, sample_host):
        with patch(
            "app.services.remote_service.get_remote_provider"
        ) as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.execute_command = AsyncMock(
                return_value=MOCK_EXEC_RESULT
            )
            mock_factory.return_value = mock_provider

            resp = client.post(
                "/api/v1/remote/bulk-execute",
                json={
                    "host_ids": [sample_host.id, sample_host.id],
                    "command": "uptime",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert data["succeeded"] == 2
            assert data["failed"] == 0

    def test_history_recorded_for_bulk(self, client, sample_host):
        with patch(
            "app.services.remote_service.get_remote_provider"
        ) as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.execute_command = AsyncMock(
                return_value=MOCK_EXEC_RESULT
            )
            mock_factory.return_value = mock_provider

            resp = client.post(
                "/api/v1/remote/bulk-execute",
                json={
                    "host_ids": [sample_host.id],
                    "command": "uptime",
                },
            )
            assert resp.status_code == 200

            history = client.get("/api/v1/remote/history?search=uptime")
            assert history.status_code == 200
            assert history.json()["count"] >= 1
            item = history.json()["items"][0]
            assert item["execution_source"] == "bulk"
