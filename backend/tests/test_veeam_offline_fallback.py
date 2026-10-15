"""Offline-agent fallback tests for the Veeam plugin routes.

When the agent feeding a Veeam server is offline the live collection fails.
The daily window key embeds the request (days + system flag), so an exact
cache miss is common (the UI asks for 8 days, the collector writes 7). These
tests lock the fallback to the last successful snapshot plus the offline
annotation the UI renders as a banner.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.db.agent import Agent
from app.plugins.installed.official_veeam.models import VeeamBackupServer, VeeamSnapshot

DAILY_CACHED = {
    "success": True,
    "jobs": [{"job_name": "Daily", "daily": {"2026-08-01": {"failed_count": 0}}}],
    "dates": ["2026-08-01"],
    "server_names": ["v1"],
    "ssh_available": True,
    "count": 1,
    "message": "ok",
    "error": None,
}

JOBS_CACHED = {
    "success": True,
    "jobs": [{"id": "old"}],
    "count": 1,
    "server_names": [],
    "error": None,
}


class FailingProvider:
    """Provider double whose live collections always fail."""

    def __init__(self, error: str):
        self._error = error

    async def get_jobs(self):
        return {
            "success": False, "jobs": [], "count": 0,
            "server_names": [], "error": self._error,
        }

    async def get_job_stats_daily(self, days: int = 7, include_system: bool = False):
        return {
            "success": False, "jobs": [], "dates": [], "ssh_available": False,
            "count": 0, "server_names": [], "message": None, "error": self._error,
        }


@pytest.fixture
def veeam_client(db_session):
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


def _make_agent(db_session, name, status):
    agent = Agent(
        name=name, hostname=f"{name}.local",
        api_key=f"mc_agent_{name}", status=status,
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def _make_server(db_session, name, agent_id=None):
    server = VeeamBackupServer(
        name=name, edition="enterprise", data_source="both",
        url="https://veeam.local:9419", username="admin", version="12.3",
        enabled=True, agent_id=agent_id,
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


def _seed(db_session, server_id, dataset, payload, minutes_ago):
    db_session.add(VeeamSnapshot(
        server_id=server_id,
        dataset=dataset,
        payload=json.dumps(payload),
        collected_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    ))
    db_session.commit()


def _patch_provider(monkeypatch, provider):
    from app.plugins.installed.official_veeam import routes as routes_module

    monkeypatch.setattr(
        routes_module, "build_server_provider", lambda _db, _server: provider
    )


def test_offline_agent_daily_window_falls_back_to_last_snapshot(
    veeam_client, db_session, monkeypatch,
):
    agent = _make_agent(db_session, "ERFM-Magalies", "offline")
    server = _make_server(db_session, "v-offline", agent_id=agent.id)
    _seed(db_session, server.id, "job_stats_daily:7:jobs", DAILY_CACHED, minutes_ago=120)
    _patch_provider(monkeypatch, FailingProvider("Agent 'relay' is offline"))

    # The UI asks for an 8-day window the collector never wrote; the fallback
    # must still serve the 7-day snapshot instead of the raw offline error.
    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs/stats/daily",
        params={"days": 8, "server_id": server.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["jobs"] == DAILY_CACHED["jobs"]
    assert data["dates"] == DAILY_CACHED["dates"]
    assert data["stale"] is True
    assert data["offline"] is True
    assert data["agent_name"] == "ERFM-Magalies"
    assert data["collected_at"]
    assert "offline" in data["error"]
    assert "may be outdated" in data["error"]


def test_offline_agent_without_cache_annotates_failure(veeam_client, db_session, monkeypatch):
    agent = _make_agent(db_session, "relay-offline", "offline")
    server = _make_server(db_session, "v-nocache", agent_id=agent.id)
    _patch_provider(monkeypatch, FailingProvider("Agent 'relay-offline' is offline"))

    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs/stats/daily",
        params={"days": 8, "server_id": server.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["offline"] is True
    assert data["agent_name"] == "relay-offline"
    assert "offline" in data["error"]


def test_online_agent_stale_uses_generic_message(veeam_client, db_session, monkeypatch):
    agent = _make_agent(db_session, "relay-online", "online")
    server = _make_server(db_session, "v-online", agent_id=agent.id)
    _seed(db_session, server.id, "jobs", JOBS_CACHED, minutes_ago=120)
    _patch_provider(monkeypatch, FailingProvider("relay down"))

    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs", params={"server_id": server.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == JOBS_CACHED["jobs"]
    assert "may be stale" in data["error"]
    assert not data.get("offline")


def test_api_source_server_is_never_flagged_offline(veeam_client, db_session, monkeypatch):
    server = _make_server(db_session, "v-api", agent_id=None)
    _seed(db_session, server.id, "jobs", JOBS_CACHED, minutes_ago=120)
    _patch_provider(monkeypatch, FailingProvider("db bridge down"))

    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs", params={"server_id": server.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "may be stale" in data["error"]
    assert not data.get("offline")
    assert not data.get("agent_name")


def test_refresh_offline_also_serves_last_snapshot(veeam_client, db_session, monkeypatch):
    agent = _make_agent(db_session, "relay-refresh", "offline")
    server = _make_server(db_session, "v-refresh", agent_id=agent.id)
    _seed(db_session, server.id, "job_stats_daily:7:jobs", DAILY_CACHED, minutes_ago=120)
    _patch_provider(monkeypatch, FailingProvider("Agent 'relay-refresh' is offline"))

    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs/stats/daily",
        params={"days": 8, "server_id": server.id, "refresh": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["jobs"] == DAILY_CACHED["jobs"]
    assert data["offline"] is True


def test_fresh_exact_cache_returns_unannotated(veeam_client, db_session, monkeypatch):
    agent = _make_agent(db_session, "relay-fresh", "offline")
    server = _make_server(db_session, "v-fresh", agent_id=agent.id)
    _seed(db_session, server.id, "job_stats_daily:8:jobs", DAILY_CACHED, minutes_ago=1)

    class Boom:
        async def get_job_stats_daily(self, days: int = 7, include_system: bool = False):
            raise AssertionError("provider must not run for a fresh snapshot")

    _patch_provider(monkeypatch, Boom())
    response = veeam_client.get(
        "/api/v1/plugins/veeam/jobs/stats/daily",
        params={"days": 8, "server_id": server.id},
    )
    assert response.status_code == 200
    assert response.json() == DAILY_CACHED
