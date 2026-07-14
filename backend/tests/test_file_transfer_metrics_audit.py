"""
Tests for File Transfer, Session Metrics, and Audit Fields.

Sprint 2.1.8 - Remote Operations Finalization.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


MOCK_UPLOAD_RESULT = {
    "success": True,
    "message": "File uploaded",
    "remote_path": "/tmp/test.txt",
    "size_bytes": 12,
}

MOCK_DOWNLOAD_RESULT = {
    "success": True,
    "message": "File downloaded",
    "remote_path": "/tmp/test.txt",
    "content": b"hello world",
    "size_bytes": 11,
}

MOCK_LIST_RESULT = {
    "success": True,
    "path": "/tmp",
    "items": [
        {"name": "file1.txt", "path": "/tmp/file1.txt", "is_directory": False, "size_bytes": 100, "modified_at": None, "permissions": "644"},
        {"name": "subdir", "path": "/tmp/subdir", "is_directory": True, "size_bytes": None, "modified_at": None, "permissions": "755"},
    ],
}

MOCK_DELETE_RESULT = {
    "success": True,
    "message": "File deleted",
    "remote_path": "/tmp/test.txt",
}

MOCK_MKDIR_RESULT = {
    "success": True,
    "message": "Directory created",
    "remote_path": "/tmp/newdir",
}


def _mock_provider():
    mock = AsyncMock()
    mock.upload_file = AsyncMock(return_value=MOCK_UPLOAD_RESULT)
    mock.download_file = AsyncMock(return_value=MOCK_DOWNLOAD_RESULT)
    mock.list_directory = AsyncMock(return_value=MOCK_LIST_RESULT)
    mock.delete_file = AsyncMock(return_value=MOCK_DELETE_RESULT)
    mock.create_directory = AsyncMock(return_value=MOCK_MKDIR_RESULT)
    mock.execute_command = AsyncMock(return_value={
        "stdout": "ok", "stderr": "", "exit_code": 0,
        "success": True, "duration_ms": 10,
        "started_at": "2025-01-01T00:00:00+00:00",
        "completed_at": "2025-01-01T00:00:00+00:00",
    })
    return mock


class TestFileUpload:
    def test_upload_success(self, client, sample_host):
        import base64
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock_factory.return_value = _mock_provider()
            resp = client.post(
                "/api/v1/remote/files/upload",
                json={
                    "host_id": sample_host.id,
                    "remote_path": "/tmp/test.txt",
                    "content_base64": base64.b64encode(b"hello").decode(),
                },
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True

    def test_upload_nonexistent_host(self, client):
        import base64
        resp = client.post(
            "/api/v1/remote/files/upload",
            json={
                "host_id": 9999,
                "remote_path": "/tmp/test.txt",
                "content_base64": base64.b64encode(b"hello").decode(),
            },
        )
        assert resp.status_code == 404

    def test_upload_disabled_host(self, client, sample_disabled_host):
        import base64
        resp = client.post(
            "/api/v1/remote/files/upload",
            json={
                "host_id": sample_disabled_host.id,
                "remote_path": "/tmp/test.txt",
                "content_base64": base64.b64encode(b"hello").decode(),
            },
        )
        assert resp.status_code == 400


class TestFileDownload:
    def test_download_success(self, client, sample_host):
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock_factory.return_value = _mock_provider()
            resp = client.post(
                "/api/v1/remote/files/download",
                json={
                    "host_id": sample_host.id,
                    "remote_path": "/tmp/test.txt",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["content_base64"] is not None
            assert data["size_bytes"] == 11

    def test_download_nonexistent_host(self, client):
        resp = client.post(
            "/api/v1/remote/files/download",
            json={"host_id": 9999, "remote_path": "/tmp/test.txt"},
        )
        assert resp.status_code == 404


class TestFileList:
    def test_list_success(self, client, sample_host):
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock_factory.return_value = _mock_provider()
            resp = client.get(
                f"/api/v1/remote/files/list?host_id={sample_host.id}&path=/tmp",
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["path"] == "/tmp"
            assert len(data["items"]) == 2
            assert data["items"][0]["name"] == "file1.txt"
            assert data["items"][0]["is_directory"] is False
            assert data["items"][1]["name"] == "subdir"
            assert data["items"][1]["is_directory"] is True

    def test_list_nonexistent_host(self, client):
        resp = client.get(
            "/api/v1/remote/files/list?host_id=9999&path=/tmp",
        )
        assert resp.status_code == 404


class TestFileMkdir:
    def test_mkdir_success(self, client, sample_host):
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock_factory.return_value = _mock_provider()
            resp = client.post(
                "/api/v1/remote/files/mkdir",
                json={
                    "host_id": sample_host.id,
                    "remote_path": "/tmp/newdir",
                },
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True


class TestFileDelete:
    def test_delete_success(self, client, sample_host):
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock_factory.return_value = _mock_provider()
            resp = client.post(
                "/api/v1/remote/files/delete",
                json={
                    "host_id": sample_host.id,
                    "remote_path": "/tmp/test.txt",
                },
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True


class TestSessionMetrics:
    def test_get_metrics(self, client):
        resp = client.get("/api/v1/remote/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_ssh_sessions" in data
        assert "active_winrm_sessions" in data
        assert "connection_pool_size" in data
        assert "average_latency_ms" in data
        assert "total_commands_executed" in data
        assert "total_commands_failed" in data


class TestAuditFields:
    def test_history_includes_audit_fields(self, client, sample_host):
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock = _mock_provider()
            mock_factory.return_value = mock

            resp = client.post(
                "/api/v1/remote/execute",
                json={
                    "host_id": sample_host.id,
                    "command": "whoami",
                    "shell": "bash",
                },
            )
            assert resp.status_code == 200

            history = client.get("/api/v1/remote/history?search=whoami")
            assert history.status_code == 200
            items = history.json()["items"]
            assert len(items) >= 1
            item = items[0]
            assert "execution_source" in item
            assert item["execution_source"] == "manual"
            assert "username" in item
            assert "working_directory" in item
            assert "credential_id" in item

    def test_bulk_history_source(self, client, sample_host):
        with patch("app.services.remote_service.get_remote_provider") as mock_factory:
            mock = _mock_provider()
            mock_factory.return_value = mock

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
            for item in history.json()["items"]:
                assert item["execution_source"] == "bulk"
