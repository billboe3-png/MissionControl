"""Tests for the edge agent bundle download endpoint.

The bundle ZIP path used to be hardcoded to ``/project/.agents`` which
does not exist on servers deployed from ``/opt/MissionControl``. The path
is now configurable via ``MC_EDGE_AGENT_ROOT`` and these tests pin that
behaviour so the hardcoded path cannot silently come back.
"""

import zipfile

import pytest


@pytest.fixture
def registered_agent(client):
    resp = client.post(
        "/api/v1/agents/register",
        json={"name": "Bundle Agent", "hostname": "bundle.agent.local"},
    )
    assert resp.status_code == 201
    return resp.json()["agent_id"], resp.json()["api_key"]


def _write_bundle(root, content=b"fake-agent-bundle", version="1.2.3"):
    """Write agent-bundle-live.zip + .version into root."""
    root.mkdir(parents=True, exist_ok=True)
    zip_path = root / "agent-bundle-live.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("agent/version.txt", content)
    (root / "agent-bundle-live.version").write_text(version, encoding="utf-8")
    return zip_path


def test_download_edge_bundle_uses_configurable_root(client, registered_agent, tmp_path, monkeypatch):
    """Bundle download resolves the ZIP under edge_agent_root, not /project."""
    agent_id, api_key = registered_agent
    _write_bundle(tmp_path)
    monkeypatch.setenv("MC_EDGE_AGENT_ROOT", str(tmp_path))

    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        resp = client.post(
            f"/api/v1/edge/{agent_id}/bundle/download",
            headers={"X-Agent-API-Key": api_key},
        )
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 200
    assert resp.headers.get("X-Agent-Bundle-Version") == "1.2.3"
    assert "agent-bundle-1.2.3.zip" in resp.headers.get("content-disposition", "")


def test_download_edge_bundle_404_when_bundle_missing(client, registered_agent, tmp_path, monkeypatch):
    """Bundle download returns 404 when no ZIP exists under edge_agent_root."""
    agent_id, api_key = registered_agent
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MC_EDGE_AGENT_ROOT", str(tmp_path))

    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        resp = client.post(
            f"/api/v1/edge/{agent_id}/bundle/download",
            headers={"X-Agent-API-Key": api_key},
        )
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 404


def test_settings_edge_agent_root_env_override(monkeypatch):
    """MC_EDGE_AGENT_ROOT env var overrides the default /project/.agents."""
    monkeypatch.setenv("MC_EDGE_AGENT_ROOT", "/opt/MissionControl/.agents")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        assert get_settings().edge_agent_root == "/opt/MissionControl/.agents"
    finally:
        get_settings.cache_clear()


def test_edge_heartbeat_stores_plugins_and_metrics(client, registered_agent, db_session):
    """Edge heartbeats persist active_plugins, health metrics, and version."""
    from app.models.db.agent import Agent

    agent_id, api_key = registered_agent
    resp = client.post(
        f"/api/v1/edge/{agent_id}/heartbeat",
        headers={"X-Agent-API-Key": api_key},
        json={
            "agent_id": agent_id,
            "status": "online",
            "health": "healthy",
            "cpu_percent": 12.5,
            "memory_percent": 48.0,
            "disk_percent": 31.0,
            "ip_address": "10.161.0.10",
            "agent_version": "3.0.0-rc1",
            "active_plugins": "linux",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "agent_id": agent_id}

    row = db_session.query(Agent).filter(Agent.id == agent_id).first()
    assert row is not None
    assert row.status == "online"
    assert row.active_plugins == "linux"
    assert row.health == "healthy"
    assert row.cpu_percent == 12.5
    assert row.memory_percent == 48.0
    assert row.disk_percent == 31.0
    assert row.ip_address == "10.161.0.10"
    assert row.agent_version == "3.0.0-rc1"


def test_edge_config_manifest_includes_enabled_plugins(client, registered_agent, db_session):
    """Config manifests carry the server-selected enabled plugin list."""
    from app.models.db.agent import Agent

    agent_id, api_key = registered_agent
    row = db_session.query(Agent).filter(Agent.id == agent_id).first()
    row.enabled_plugins = "linux,docker"
    db_session.commit()

    resp = client.get(
        f"/api/v1/edge/{agent_id}/config",
        headers={"X-Agent-API-Key": api_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["config"]["enabled_plugins"] == ["linux", "docker"]