"""
Mission Control Agent Remote Target plugins tests.

Covers the "Plugins to collect on this host" checkboxes:
- Create/update round-trips target_plugins through the API.
- Missing target_plugins is stored as null.
- Heartbeat response includes target_plugins so agents know what to collect.
"""


def _register_agent(client, name: str) -> dict:
    resp = client.post(
        "/api/v1/agents/register",
        json={"name": name, "hostname": name.lower().replace(" ", ".") + ".local"},
    )
    assert resp.status_code == 201
    return resp.json()


def _create_target(client, agent_id: int, **overrides) -> dict:
    payload = {
        "name": "Corp Veeam Host",
        "hostname": "192.168.10.49",
        "protocol": "ssh",
        "port": 22,
        "username": "kg\\administrator",
        "password": "secret",
        "target_plugins": "veeam,hyperv",
    }
    payload.update(overrides)
    resp = client.post(f"/api/v1/agents/{agent_id}/remote-targets", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestRemoteTargetPluginsAPI:
    def test_create_with_plugins_round_trips(self, client):
        agent = _register_agent(client, "Plugins Agent")
        target = _create_target(client, agent["agent_id"])
        assert target["target_plugins"] == "veeam,hyperv"

        listed = client.get(f"/api/v1/agents/{agent['agent_id']}/remote-targets")
        assert listed.status_code == 200
        assert listed.json()["targets"][0]["target_plugins"] == "veeam,hyperv"

    def test_create_without_plugins_stores_null(self, client):
        agent = _register_agent(client, "No Plugins Agent")
        target = _create_target(client, agent["agent_id"], target_plugins=None)
        assert target["target_plugins"] is None

    def test_update_plugins(self, client):
        agent = _register_agent(client, "Update Plugins Agent")
        target = _create_target(client, agent["agent_id"])

        resp = client.put(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}",
            json={"target_plugins": "docker"},
        )
        assert resp.status_code == 200
        assert resp.json()["target_plugins"] == "docker"

        resp = client.put(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}",
            json={"target_plugins": None},
        )
        assert resp.status_code == 200
        assert resp.json()["target_plugins"] is None

    def test_heartbeat_includes_target_plugins(self, client):
        agent = _register_agent(client, "Heartbeat Plugins Agent")
        _create_target(client, agent["agent_id"])

        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={
                "agent_id": agent["agent_id"],
                "health": "healthy",
            },
            headers={"X-Agent-API-Key": agent["api_key"]},
        )
        assert resp.status_code == 200
        targets = resp.json().get("remote_targets") or []
        assert len(targets) == 1
        assert targets[0]["target_plugins"] == "veeam,hyperv"
        assert targets[0]["hostname"] == "192.168.10.49"


def test_create_with_veeam_registers_server(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    agent = _register_agent(client, "Registry Agent")
    target = _create_target(client, agent["agent_id"], target_plugins="veeam")
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target["id"]
    ).one()
    assert row.enabled is True
    assert row.agent_id == agent["agent_id"]


def test_update_removing_veeam_disables_server(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    agent = _register_agent(client, "Registry Update Agent")
    target = _create_target(client, agent["agent_id"], target_plugins="veeam")
    resp = client.put(
        f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}",
        json={"target_plugins": "hyperv"},
    )
    assert resp.status_code == 200
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target["id"]
    ).one()
    assert row.enabled is False


def test_delete_target_disables_server(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    agent = _register_agent(client, "Registry Delete Agent")
    target = _create_target(client, agent["agent_id"], target_plugins="veeam")
    resp = client.delete(
        f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}"
    )
    assert resp.status_code == 204
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target["id"]
    ).one()
    assert row.enabled is False


class TestRemoteTargetVeeamDbType:
    def test_create_defaults_to_postgresql(self, client):
        agent = _register_agent(client, "DbType Default Agent")
        target = _create_target(client, agent["agent_id"])
        assert target["db_type"] == "postgresql"
        assert target["column_case"] == "pascal"

    def test_create_with_mssql_round_trips(self, client):
        agent = _register_agent(client, "DbType Mssql Agent")
        target = _create_target(
            client, agent["agent_id"], db_type="mssql", column_case="snake"
        )
        assert target["db_type"] == "mssql"
        assert target["column_case"] == "snake"

        listed = client.get(f"/api/v1/agents/{agent['agent_id']}/remote-targets")
        assert listed.status_code == 200
        assert listed.json()["targets"][0]["db_type"] == "mssql"
        assert listed.json()["targets"][0]["column_case"] == "snake"

    def test_update_db_type_and_column_case(self, client):
        agent = _register_agent(client, "DbType Update Agent")
        target = _create_target(client, agent["agent_id"])

        resp = client.put(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}",
            json={"db_type": "mssql", "column_case": "snake"},
        )
        assert resp.status_code == 200
        assert resp.json()["db_type"] == "mssql"
        assert resp.json()["column_case"] == "snake"

    def test_invalid_db_type_rejected(self, client):
        agent = _register_agent(client, "DbType Bad Agent")
        resp = client.post(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets",
            json={
                "name": "Bad DbType",
                "hostname": "192.168.10.49",
                "protocol": "ssh",
                "port": 22,
                "username": "kg\\administrator",
                "password": "secret",
                "db_type": "oracle",
            },
        )
        assert resp.status_code == 422

    def test_invalid_column_case_rejected(self, client):
        agent = _register_agent(client, "ColumnCase Bad Agent")
        resp = client.post(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets",
            json={
                "name": "Bad ColumnCase",
                "hostname": "192.168.10.49",
                "protocol": "ssh",
                "port": 22,
                "username": "kg\\administrator",
                "password": "secret",
                "column_case": "camel",
            },
        )
        assert resp.status_code == 422
