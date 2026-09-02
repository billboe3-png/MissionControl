"""
Veeam plugin live-data route tests.

Covers both the no-server fallback (empty db -> legacy shape with
success/healthy/connected False) and with-server delegation to a fake
provider returning canned legacy dicts.
"""

import pytest
from fastapi.testclient import TestClient

from app.plugins.installed.official_veeam.models import VeeamBackupServer

NO_SERVER_ERROR = "No Veeam server configured"

LEGACY_KEYS = {
    "/overview": ("success", "version", "name", "total_jobs", "running_jobs",
                  "total_repositories", "total_space_bytes", "used_space_bytes",
                  "recent_sessions", "sessions_success", "sessions_warning",
                  "sessions_failed", "error"),
    "/health": ("healthy", "version", "name", "error"),
    "/test": ("connected", "version", "name", "server_id", "error"),
    "/jobs": ("success", "jobs", "count", "server_names", "error"),
    "/jobs/stats": ("success", "jobs", "ssh_available", "count", "message", "error"),
    "/jobs/stats/daily": ("success", "jobs", "dates", "ssh_available", "count",
                          "server_names", "message", "error"),
    "/jobs/j1": ("success", "job", "error"),
    "/jobs/j1/start": ("success", "message", "error"),
    "/jobs/j1/stop": ("success", "message", "error"),
    "/sessions": ("success", "sessions", "count", "server_names", "error"),
    "/sessions/stats": ("success", "stats", "ssh_available", "count", "message", "error"),
    "/repositories": ("success", "repositories", "count", "error"),
    "/servers": ("success", "servers", "count", "error"),
    "/restore-points": ("success", "restore_points", "count", "error"),
    "/license": ("success", "license", "error"),
    "/capacity-tier": ("success", "object_storages", "count", "error"),
}

LIVE_ROUTE_CASES = [
    ("GET", "/overview"),
    ("GET", "/jobs"),
    ("GET", "/jobs/stats"),
    ("GET", "/jobs/stats/daily"),
    ("GET", "/jobs/j1"),
    ("GET", "/sessions"),
    ("GET", "/sessions/stats"),
    ("GET", "/repositories"),
    ("GET", "/servers"),
    ("GET", "/restore-points"),
    ("GET", "/license"),
    ("GET", "/capacity-tier"),
    ("POST", "/jobs/j1/start"),
    ("POST", "/jobs/j1/stop"),
]

WITH_SERVER_CASES = [
    ("GET", "/overview", "get_summary"),
    ("GET", "/health", "get_health"),
    ("GET", "/jobs", "get_jobs"),
    ("GET", "/jobs/stats", "get_job_stats"),
    ("GET", "/jobs/stats/daily", "get_job_stats_daily"),
    ("GET", "/jobs/j1", "get_job_detail"),
    ("POST", "/jobs/j1/start", "start_job"),
    ("POST", "/jobs/j1/stop", "stop_job"),
    ("GET", "/sessions", "get_sessions"),
    ("GET", "/sessions/stats", "get_session_stats"),
    ("GET", "/repositories", "get_repositories"),
    ("GET", "/servers", "get_managed_servers"),
    ("GET", "/restore-points", "get_restore_points"),
    ("GET", "/license", "get_license"),
    ("GET", "/capacity-tier", "get_capacity_tier"),
]

CANNED = {
    "get_summary": {
        "success": True, "version": "12.3", "name": "v1",
        "total_jobs": 3, "running_jobs": 1, "total_repositories": 2,
        "total_space_bytes": 1000, "used_space_bytes": 400, "recent_sessions": 5,
        "sessions_success": 4, "sessions_warning": 1, "sessions_failed": 0,
        "error": None,
    },
    "get_health": {"healthy": True, "version": "12.3", "name": "v1", "error": None},
    "get_jobs": {
        "success": True, "jobs": [{"id": "j1"}, {"id": "j2"}], "count": 2,
        "server_names": ["v1"], "error": None,
    },
    "get_job_stats": {
        "success": True, "jobs": [], "ssh_available": True, "count": 0,
        "message": "ok", "error": None,
    },
    "get_job_stats_daily": {
        "success": True, "jobs": [], "dates": ["2026-08-01"], "ssh_available": True,
        "count": 0, "server_names": ["v1"], "message": "ok", "error": None,
    },
    "get_job_detail": {"success": True, "job": {"id": "j1", "name": "Daily"}, "error": None},
    "start_job": {"success": True, "message": "Job j1 started", "error": None},
    "stop_job": {"success": True, "message": "Job j1 stopped", "error": None},
    "get_sessions": {"success": True, "sessions": [{"id": "s1"}], "count": 1,
                     "server_names": ["v1"], "error": None},
    "get_session_stats": {
        "success": True, "stats": [], "ssh_available": True, "count": 0,
        "message": "ok", "error": None,
    },
    "get_repositories": {"success": True, "repositories": [{"id": "r1"}], "count": 1,
                         "error": None},
    "get_managed_servers": {"success": True, "servers": [{"id": "srv1"}], "count": 1,
                            "error": None},
    "get_restore_points": {"success": True, "restore_points": [{"id": "rp1"}], "count": 1,
                           "error": None},
    "get_license": {"success": True, "license": {"edition": "enterprise"}, "error": None},
    "get_capacity_tier": {"success": True, "object_storages": [{"id": "obj1"}], "count": 1,
                          "error": None},
}


class FakeProvider:
    """Provider double that returns canned legacy dicts per method."""

    def __init__(self, server, results):
        self.server = server
        self._results = results

    def _result(self, name):
        return self._results.get(name, {})

    async def get_summary(self):
        return self._result("get_summary")

    async def get_health(self):
        return self._result("get_health")

    async def get_jobs(self):
        return self._result("get_jobs")

    async def get_job_stats(self):
        return self._result("get_job_stats")

    async def get_job_stats_daily(self, days=7):
        return self._result("get_job_stats_daily")

    async def get_job_detail(self, job_id):
        return self._result("get_job_detail")

    async def start_job(self, job_id):
        return self._result("start_job")

    async def stop_job(self, job_id):
        return self._result("stop_job")

    async def get_sessions(self):
        return self._result("get_sessions")

    async def get_session_stats(self):
        return self._result("get_session_stats")

    async def get_repositories(self):
        return self._result("get_repositories")

    async def get_managed_servers(self):
        return self._result("get_managed_servers")

    async def get_restore_points(self, vm_id=None):
        return self._result("get_restore_points")

    async def get_license(self):
        return self._result("get_license")

    async def get_capacity_tier(self):
        return self._result("get_capacity_tier")

    async def test_connection(self):
        return self._result("test_connection")


@pytest.fixture
def veeam_client(db_session):
    """FastAPI test client with the veeam plugin router and db override."""
    from app.db.database import get_db
    from app.main import app as _app
    from app.plugins.installed.official_veeam.routes import router as veeam_router

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    _app.dependency_overrides[get_db] = override_get_db
    _app.include_router(veeam_router)
    with TestClient(_app) as test_client:
        yield test_client
    _app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def veeam_server(db_session):
    """A single enabled VeeamBackupServer row."""
    server = VeeamBackupServer(
        name="v1",
        edition="enterprise",
        data_source="api",
        url="https://veeam.local:9419",
        username="admin",
        version="12.3",
        enabled=True,
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


@pytest.fixture
def fake_provider(veeam_server, monkeypatch):
    """Monkeypatch build_server_provider to return a canned FakeProvider."""
    from app.plugins.installed.official_veeam import routes as routes_module

    provider = FakeProvider(veeam_server, CANNED)

    def _build(_db, _server):
        return provider

    monkeypatch.setattr(routes_module, "build_server_provider", _build)
    return provider


@pytest.mark.parametrize("method,path", LIVE_ROUTE_CASES)
def test_no_server_legacy_shape(veeam_client, method, path):
    response = veeam_client.request(method, f"/api/v1/plugins/veeam{path}")
    assert response.status_code == 200
    data = response.json()
    for key in LEGACY_KEYS[path]:
        assert key in data
    assert data["success"] is False
    assert data["error"] == NO_SERVER_ERROR


def test_no_server_health(veeam_client):
    response = veeam_client.get("/api/v1/plugins/veeam/health")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is False
    assert data["error"] == NO_SERVER_ERROR


def test_no_server_test(veeam_client):
    response = veeam_client.get("/api/v1/plugins/veeam/test")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert data["error"] == NO_SERVER_ERROR


def test_with_disabled_server_only_uses_no_server_shape(veeam_client, db_session):
    db_session.add(VeeamBackupServer(name="disabled", enabled=False))
    db_session.commit()
    response = veeam_client.get("/api/v1/plugins/veeam/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] == NO_SERVER_ERROR


@pytest.mark.parametrize("method,path,canned_key", WITH_SERVER_CASES)
def test_with_server_delegates(veeam_client, fake_provider, method, path, canned_key):
    response = veeam_client.request(method, f"/api/v1/plugins/veeam{path}")
    assert response.status_code == 200
    assert response.json() == CANNED[canned_key]


def test_with_server_test_mapping(veeam_client, fake_provider, monkeypatch):
    canned_test = {
        "connected": True,
        "version": "12.3",
        "name": "v1",
        "server_id": fake_provider.server.id,
        "db_available": True,
        "rest_available": True,
        "powershell_available": False,
        "error": None,
    }

    async def fake_test_connection():
        return canned_test

    monkeypatch.setattr(fake_provider, "test_connection", fake_test_connection)
    response = veeam_client.get("/api/v1/plugins/veeam/test")
    assert response.status_code == 200
    assert response.json() == canned_test


def test_with_server_job_stats_daily_passes_days(veeam_client, fake_provider, monkeypatch):
    captured = {}

    async def get_job_stats_daily(days=7):
        captured["days"] = days
        return CANNED["get_job_stats_daily"]

    monkeypatch.setattr(fake_provider, "get_job_stats_daily", get_job_stats_daily)
    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs/stats/daily", params={"days": 14}
    )
    assert response.status_code == 200
    assert captured["days"] == 14


def test_with_server_restore_points_passes_vm_id(veeam_client, fake_provider, monkeypatch):
    captured = {}

    async def get_restore_points(vm_id=None):
        captured["vm_id"] = vm_id
        return CANNED["get_restore_points"]

    monkeypatch.setattr(fake_provider, "get_restore_points", get_restore_points)
    response = veeam_client.get(
        "/api/v1/plugins/veeam/restore-points", params={"vm_id": "vm-1"}
    )
    assert response.status_code == 200
    assert captured["vm_id"] == "vm-1"


def test_with_server_provider_error(veeam_client, fake_provider, monkeypatch):
    async def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(fake_provider, "get_jobs", boom)
    response = veeam_client.get("/api/v1/plugins/veeam/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "boom"



def test_unknown_server_id_returns_404(veeam_client, veeam_server):
    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs", params={"server_id": 999999}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Veeam server not found"}


def test_disabled_server_id_returns_404(veeam_client, veeam_server, db_session):
    disabled = VeeamBackupServer(
        name="disabled2", edition="enterprise", data_source="api",
        url="https://veeam.local:9419", username="admin",
        version="12.3", enabled=False,
    )
    db_session.add(disabled)
    db_session.commit()
    db_session.refresh(disabled)
    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs", params={"server_id": disabled.id}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Veeam server not found"}


def test_server_id_selects_that_server(veeam_client, veeam_server, monkeypatch, db_session):
    from app.plugins.installed.official_veeam import routes as routes_module

    # create a second enabled server with a higher id than the veeam_server fixture
    second = VeeamBackupServer(
        name="v2", edition="enterprise", data_source="api",
        url="https://veeam2.local:9419", username="admin",
        version="12.3", enabled=True,
    )
    db_session.add(second)
    db_session.commit()
    db_session.refresh(second)

    selected = {}

    def _build(_db, _server):
        selected["id"] = _server.id
        selected["name"] = _server.name
        return FakeProvider(_server, CANNED)

    monkeypatch.setattr(routes_module, "build_server_provider", _build)

    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs", params={"server_id": second.id}
    )
    assert response.status_code == 200
    assert selected["id"] == second.id
    assert selected["name"] == "v2"
    assert response.json() == CANNED["get_jobs"]
