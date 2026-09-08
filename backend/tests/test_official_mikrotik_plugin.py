"""
official_mikrotik Plugin Tests

Covers config, plugin class, service unit logic, and REST API routes
(CRUD, credential encryption, RBAC, audit log) against the /servers
contract used by frontend/src/services/mikrotik.ts.
"""

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------- #
# Fixtures                                                                #
# ---------------------------------------------------------------------- #


@pytest.fixture
def mikrotik_client(db_session, monkeypatch):
    """Test client with the MikroTik router mounted on the main app."""
    from app.db.database import get_db
    from app.main import app as _app
    from app.plugins.installed.official_mikrotik.config import MikroTikPluginConfig
    from app.plugins.installed.official_mikrotik.routes import router as mikrotik_router
    from app.plugins.loader import plugin_loader

    def override_get_db():
        yield db_session

    _app.dependency_overrides[get_db] = override_get_db

    mock_plugin = MagicMock()
    mock_plugin._plugin_config = MikroTikPluginConfig()

    def _fake_get_loaded(slug):
        return mock_plugin if slug == "official_mikrotik" else None

    monkeypatch.setattr(plugin_loader, "get_loaded", _fake_get_loaded)

    _app.include_router(mikrotik_router)
    with TestClient(_app) as test_client:
        yield test_client
    # Remove routes added by include_router to keep the app clean per test
    mikrotik_paths = {r.path for r in mikrotik_router.routes}
    _app.router.routes = [
        r for r in _app.router.routes if getattr(r, "path", None) not in mikrotik_paths
    ]


def _role_override(role: str):
    from app.core.auth_dependency import get_current_user

    class _RoleUser:
        def __init__(self) -> None:
            self.id = 99
            self.email = f"{role}@test.local"
            self.display_name = role.title()
            self.role = role
            self.enabled = True

    async def _override():
        return _RoleUser()

    return get_current_user, _override


SERVER_PAYLOAD = {
    "name": "core-sw-01",
    "host": "10.161.0.14",
    "username": "admin",
    "password": "change-me-please",
}


def _create_server(client: TestClient, **overrides) -> dict:
    payload = {**SERVER_PAYLOAD, **overrides}
    response = client.post("/api/v1/plugins/mikrotik/servers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------- #
# Config                                                                  #
# ---------------------------------------------------------------------- #


class TestMikroTikPluginConfig:
    def test_default_config(self):
        from app.plugins.installed.official_mikrotik.config import MikroTikPluginConfig

        cfg = MikroTikPluginConfig()
        assert cfg.auto_sync_enabled is True
        assert cfg.sync_interval_seconds == 300
        assert cfg.command_timeout == 60

    def test_env_prefix_respected(self, monkeypatch):
        from app.plugins.installed.official_mikrotik.config import MikroTikPluginConfig

        monkeypatch.setenv("MIKROTIK_SYNC_INTERVAL_SECONDS", "600")
        cfg = MikroTikPluginConfig()
        assert cfg.sync_interval_seconds == 600


# ---------------------------------------------------------------------- #
# Service unit logic                                                      #
# ---------------------------------------------------------------------- #


class TestServiceUnits:
    def test_connector_type_resolution(self):
        from app.plugins.installed.official_mikrotik.models import MikroTikServer
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        base = {"name": "s", "host": "10.0.0.1", "username": "admin"}
        assert MikroTikService.resolve_connector_type(MikroTikServer(**base)) == "ssh"
        assert (
            MikroTikService.resolve_connector_type(MikroTikServer(**base, telnet_enabled=True))
            == "telnet"
        )
        assert (
            MikroTikService.resolve_connector_type(
                MikroTikServer(**base, telnet_enabled=True, api_enabled=True)
            )
            == "rest"
        )

    def test_build_connector_types(self):
        from app.plugins.installed.official_mikrotik.connector import (
            SshConnector,
            TelnetConnector,
            WebUiConnector,
        )
        from app.plugins.installed.official_mikrotik.models import MikroTikServer
        from app.plugins.installed.official_mikrotik.service import mikrotik_service

        base = {"name": "s", "host": "10.0.0.1", "username": "admin"}
        assert isinstance(
            mikrotik_service.build_connector(MikroTikServer(**base)), SshConnector
        )
        assert isinstance(
            mikrotik_service.build_connector(
                MikroTikServer(**base, telnet_enabled=True, telnet_port=2323)
            ),
            TelnetConnector,
        )
        rest_conn = mikrotik_service.build_connector(
            MikroTikServer(**base, api_enabled=True, api_port=443)
        )
        assert isinstance(rest_conn, WebUiConnector)

    def test_password_encrypt_decrypt_roundtrip(self):
        from app.plugins.installed.official_mikrotik.service import (
            decrypt_password,
            encrypt_password,
        )

        token = encrypt_password("s3cret-value")
        assert token is not None
        assert "s3cret-value" not in token
        assert decrypt_password(token) == "s3cret-value"

    def test_parse_resource_output_rest_json(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        payload = json.dumps(
            {
                "version": "7.14.3",
                "board-name": "CRS326-24S+2Q+RM",
                "uptime": "3w1d02:15:00",
                "cpu-load": 12,
                "free-memory": 268435456,
                "total-memory": 1073741824,
            }
        )
        info = MikroTikService()._parse_resource_output(payload)
        assert info["version"] == "7.14.3"
        assert info["board-name"] == "CRS326-24S+2Q+RM"
        assert info["cpu-load"] == "12"
        assert info["memory_usage_pct"] == 75

    def test_parse_resource_output_cli_fallback(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        raw = (
            "uptime: 1w2d03:04:05\n"
            "version: 7.14.3 (stable)\n"
            "board-name: hEX S\n"
            "cpu-load: 4%\n"
        )
        info = MikroTikService()._parse_resource_output(raw)
        assert info["version"] == "7.14.3 (stable)"
        assert info["board-name"] == "hEX S"
        assert info["cpu-load"] == "4%"


class TestDetailOutputParsing:
    """Parsers must handle real RouterOS 'print detail' output.

    Real output (captured from RouterOS 7.24): entries wrap across
    indented continuation lines, flag letters sit between index and the
    first key=value pair, and counters use space thousands separators.
    """

    INTERFACE_DETAIL = (
        "Flags: R - RUNNING; S - SLAVE\n"
        '0  S name="ether1" default-name="ether1" type="ether" mtu=1500'
        " actual-mtu=1500\n"
        "     l2mtu=1596 max-l2mtu=2026 vrf=main mac-address=F4:1E:57:B3:AB:A8\n"
        "     link-downs=0\n"
        " \n"
        '1 RS name="ether2" default-name="ether2" type="ether" mtu=1500'
        " actual-mtu=1500\n"
        "     last-link-up-time=2026-08-24 13:54:15 link-downs=33\n"
    )

    STATS_DETAIL = (
        "Flags: R - RUNNING; S - SLAVE\n"
        '0  S name="ether1" link-downs=0 rx-byte=0 tx-byte=0 rx-packet=0 tx-packet=0\n'
        " \n"
        '1 RS name="ether2" link-downs=33 rx-byte=475 991 995 tx-byte=510 403 156\n'
        "     rx-packet=1 356 226 tx-packet=1 194 494\n"
    )

    def test_parse_detail_records_flags_and_wrapping(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        records = MikroTikService._parse_key_value_output(self.INTERFACE_DETAIL)
        assert len(records) == 2
        assert records[0]["_flags"] == "S"
        assert records[1]["_flags"] == "RS"
        assert records[0]["mac-address"] == "F4:1E:57:B3:AB:A8"
        # Continuation-line pairs land in the same record.
        assert records[0]["l2mtu"] == "1596"

    def test_map_interfaces_merges_stats_and_compact_numbers(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService
        from app.plugins.installed.official_mikrotik.service_types import CommandResult

        svc = MikroTikService()
        rows = svc._map_interfaces(
            CommandResult(success=True, output=self.INTERFACE_DETAIL),
            CommandResult(success=True, output=self.STATS_DETAIL),
        )
        by_name = {r["name"]: r for r in rows}
        assert set(by_name) == {"ether1", "ether2"}
        ether2 = by_name["ether2"]
        assert ether2["rx_bytes"] == 475991995
        assert ether2["tx_bytes"] == 510403156
        assert ether2["rx_packets"] == 1356226
        assert ether2["status"] == "running"
        ether1 = by_name["ether1"]
        assert ether1["rx_bytes"] == 0
        assert ether1["status"] == "down"
        assert ether1["mac"] == "F4:1E:57:B3:AB:A8"
        assert ether1["mtu"] == 1500

    def test_map_firewall_disabled_flag_and_counters(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService
        from app.plugins.installed.official_mikrotik.service_types import CommandResult

        raw = (
            "Flags: X - disabled, I - inactive, D - dynamic\n"
            ' 0 X chain=input action=drop comment="block wan"'
            " bytes=12 345 packets=67\n"
            " 1   chain=forward action=accept bytes=9 packets=8\n"
        )
        rows = MikroTikService()._map_firewall(CommandResult(success=True, output=raw))
        assert rows[0]["disabled"] is True
        assert rows[0]["bytes"] == 12345
        assert rows[0]["comment"] == "block wan"
        assert rows[1]["disabled"] is False
        assert rows[1]["packets"] == 8


# ---------------------------------------------------------------------- #
# Plugin class                                                            #
# ---------------------------------------------------------------------- #


class TestMikroTikPlugin:
    @pytest.mark.asyncio
    async def test_plugin_manifest(self):
        from app.plugins.installed.official_mikrotik import MikroTikPlugin

        manifest = {
            "id": "official_mikrotik",
            "name": "MikroTik RouterOS",
            "version": "1.1.0",
            "execution_target": "server",
        }
        plugin = MikroTikPlugin(manifest=manifest, config={})
        assert plugin.slug == "official_mikrotik"
        assert plugin.version == "1.1.0"

    @pytest.mark.asyncio
    async def test_plugin_dashboard_widgets(self):
        from app.plugins.installed.official_mikrotik import MikroTikPlugin

        plugin = MikroTikPlugin(manifest={"id": "official_mikrotik"}, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 1
        assert widgets[0]["id"] == "mikrotik-interfaces"

    @pytest.mark.asyncio
    async def test_plugin_navigation_items(self):
        from app.plugins.installed.official_mikrotik import MikroTikPlugin

        plugin = MikroTikPlugin(manifest={"id": "official_mikrotik"}, config={})
        items = await plugin.get_navigation_items()
        assert len(items) == 1
        assert items[0]["path"] == "/mikrotik"

    @pytest.mark.asyncio
    async def test_health_check_no_servers(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik import MikroTikPlugin

        plugin = MikroTikPlugin(manifest={"id": "official_mikrotik"}, config={})
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.SessionLocal", lambda: db_session
        )
        health = await plugin.health_check()
        assert health["status"] == "warning"
        assert health["message"] == "No servers configured"

    @pytest.mark.asyncio
    async def test_widget_data_reports_servers(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik import MikroTikPlugin
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        MikroTikRepository.create_server(
            db_session,
            name="sw-a",
            host="10.0.0.1",
            username="admin",
            status="online",
            version="7.14",
        )
        plugin = MikroTikPlugin(manifest={"id": "official_mikrotik"}, config={})
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.SessionLocal", lambda: db_session
        )
        data = await plugin.get_widget_data("mikrotik-interfaces")
        assert data["total"] == 1
        assert data["online"] == 1
        assert data["servers"][0]["version"] == "7.14"


# ---------------------------------------------------------------------- #
# Routes: CRUD                                                            #
# ---------------------------------------------------------------------- #


class TestServerCrudRoutes:
    def test_create_server_encrypts_password(self, mikrotik_client: TestClient, db_session):
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        body = _create_server(mikrotik_client)
        assert body["name"] == SERVER_PAYLOAD["name"]
        assert "password" not in body
        assert "password_encrypted" not in body

        stored = MikroTikRepository.get_server(db_session, body["id"])
        assert stored is not None
        cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
        assert cipher.decrypt(stored.password_encrypted) == SERVER_PAYLOAD["password"]

    def test_create_rejects_missing_name(self, mikrotik_client: TestClient):
        payload = {k: v for k, v in SERVER_PAYLOAD.items() if k != "name"}
        response = mikrotik_client.post("/api/v1/plugins/mikrotik/servers", json=payload)
        assert response.status_code == 422

    def test_duplicate_name_conflict(self, mikrotik_client: TestClient):
        first = _create_server(mikrotik_client)
        second_payload = {**SERVER_PAYLOAD, "host": "10.0.0.9"}
        conflict = mikrotik_client.post("/api/v1/plugins/mikrotik/servers", json=second_payload)
        assert conflict.status_code == 409
        rename = mikrotik_client.put(
            f"/api/v1/plugins/mikrotik/servers/{first['id']}",
            json={"name": "other-sw"},
        )
        assert rename.status_code == 200

    def test_update_password_reencrypts(self, mikrotik_client: TestClient, db_session):
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        body = _create_server(mikrotik_client)
        updated = mikrotik_client.put(
            f"/api/v1/plugins/mikrotik/servers/{body['id']}",
            json={"password": "brand-new-pw", "api_enabled": True, "api_port": 443},
        )
        assert updated.status_code == 200
        assert updated.json()["api_enabled"] is True

        stored = MikroTikRepository.get_server(db_session, body["id"])
        cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
        assert cipher.decrypt(stored.password_encrypted) == "brand-new-pw"

    def test_cannot_set_encrypted_column_directly(self, mikrotik_client: TestClient, db_session):
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        body = _create_server(mikrotik_client)
        response = mikrotik_client.put(
            f"/api/v1/plugins/mikrotik/servers/{body['id']}",
            json={"password_encrypted": "attacker-controlled"},
        )
        assert response.status_code == 200
        stored = MikroTikRepository.get_server(db_session, body["id"])
        assert stored.password_encrypted != "attacker-controlled"

    def test_get_and_list_servers(self, mikrotik_client: TestClient):
        created = _create_server(mikrotik_client)
        listing = mikrotik_client.get("/api/v1/plugins/mikrotik/servers")
        assert listing.status_code == 200
        assert isinstance(listing.json(), list)
        assert len(listing.json()) == 1

        single = mikrotik_client.get(f"/api/v1/plugins/mikrotik/servers/{created['id']}")
        assert single.status_code == 200
        assert single.json()["host"] == SERVER_PAYLOAD["host"]

    def test_get_missing_server_404(self, mikrotik_client: TestClient):
        response = mikrotik_client.get("/api/v1/plugins/mikrotik/servers/9999")
        assert response.status_code == 404

    def test_delete_server(self, mikrotik_client: TestClient):
        created = _create_server(mikrotik_client)
        deleted = mikrotik_client.delete(f"/api/v1/plugins/mikrotik/servers/{created['id']}")
        assert deleted.status_code == 200
        assert deleted.json() == {"success": True}

        gone = mikrotik_client.get(f"/api/v1/plugins/mikrotik/servers/{created['id']}")
        assert gone.status_code == 404


# ---------------------------------------------------------------------- #
# Routes: RBAC and auth                                                   #
# ---------------------------------------------------------------------- #


class TestRouteRbacAndAuth:
    def test_readonly_cannot_create_or_delete(self, mikrotik_client: TestClient):
        from app.main import app as _app

        dep, override = _role_override("readonly")
        _app.dependency_overrides[dep] = override
        try:
            create_response = mikrotik_client.post(
                "/api/v1/plugins/mikrotik/servers", json=dict(SERVER_PAYLOAD)
            )
            assert create_response.status_code == 403

            delete_response = mikrotik_client.delete("/api/v1/plugins/mikrotik/servers/1")
            assert delete_response.status_code == 403
        finally:
            _app.dependency_overrides.pop(dep, None)

    def test_readonly_can_list_and_get_cached(self, mikrotik_client: TestClient, db_session):
        from app.main import app as _app
        from app.plugins.installed.official_mikrotik.cache import cache_manager
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        server = MikroTikRepository.create_server(
            db_session, name="ro-sw", host="10.0.0.5", username="admin"
        )
        cache_manager.replace_interfaces(
            db_session,
            server.id,
            [{"name": "ether1", "status": "running", "rx_bytes": 1, "tx_bytes": 2}],
        )

        dep, override = _role_override("readonly")
        _app.dependency_overrides[dep] = override
        try:
            listing = mikrotik_client.get("/api/v1/plugins/mikrotik/servers")
            assert listing.status_code == 200
            interfaces = mikrotik_client.get(
                f"/api/v1/plugins/mikrotik/servers/{server.id}/interfaces"
            )
            assert interfaces.status_code == 200
            assert interfaces.json()["success"] is True
        finally:
            _app.dependency_overrides.pop(dep, None)

    def test_operator_can_execute_but_not_create(self, mikrotik_client: TestClient, db_session):
        from app.main import app as _app
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        server = MikroTikRepository.create_server(
            db_session, name="op-sw", host="10.0.0.6", username="admin"
        )
        dep, override = _role_override("operator")
        _app.dependency_overrides[dep] = override
        try:
            forbidden = mikrotik_client.post(
                "/api/v1/plugins/mikrotik/servers", json=dict(SERVER_PAYLOAD)
            )
            assert forbidden.status_code == 403

            missing = mikrotik_client.post(
                f"/api/v1/plugins/mikrotik/servers/{server.id}/execute",
                json={"command": "/system identity print"},
            )
            # Reaches execution path (fails to connect -> 500), proving RBAC passed
            assert missing.status_code == 500
        finally:
            _app.dependency_overrides.pop(dep, None)

    def test_invalid_token_rejected(self, mikrotik_client: TestClient):
        response = mikrotik_client.get(
            "/api/v1/plugins/mikrotik/servers",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------- #
# Routes: audit log and health                                            #
# ---------------------------------------------------------------------- #


class TestAuditAndHealthRoutes:
    def test_command_logs_endpoint(self, mikrotik_client: TestClient, db_session):
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        server = MikroTikRepository.create_server(
            db_session, name="log-sw", host="10.0.0.7", username="admin"
        )
        MikroTikRepository.add_command_log(
            db_session,
            server_id=server.id,
            connector_type="ssh",
            command="/system identity print",
            output="name: log-sw",
            success=True,
            duration_ms=12,
            executed_by="tester",
        )
        response = mikrotik_client.get(f"/api/v1/plugins/mikrotik/servers/{server.id}/logs")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 1
        assert body["items"][0]["command"] == "/system identity print"
        assert body["items"][0]["executed_by"] == "tester"

    def test_logs_require_operator(self, mikrotik_client: TestClient, db_session):
        from app.main import app as _app
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        server = MikroTikRepository.create_server(
            db_session, name="log-ro", host="10.0.0.8", username="admin"
        )
        dep, override = _role_override("readonly")
        _app.dependency_overrides[dep] = override
        try:
            response = mikrotik_client.get(f"/api/v1/plugins/mikrotik/servers/{server.id}/logs")
            assert response.status_code == 403
        finally:
            _app.dependency_overrides.pop(dep, None)

    def test_execute_on_missing_server_404(self, mikrotik_client: TestClient):
        response = mikrotik_client.post(
            "/api/v1/plugins/mikrotik/servers/9999/execute",
            json={"command": "/system identity print"},
        )
        assert response.status_code == 404

    def test_empty_command_400(self, mikrotik_client: TestClient, db_session):
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        server = MikroTikRepository.create_server(
            db_session, name="cmd-sw", host="10.0.0.9", username="admin"
        )
        response = mikrotik_client.post(
            f"/api/v1/plugins/mikrotik/servers/{server.id}/execute",
            json={"command": ""},
        )
        assert response.status_code == 400

    def test_health_summary(self, mikrotik_client: TestClient, db_session):
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )

        MikroTikRepository.create_server(
            db_session, name="h-sw", host="10.0.0.10", username="admin", status="online"
        )
        response = mikrotik_client.get("/api/v1/plugins/mikrotik/health")
        assert response.status_code == 200
        body = response.json()
        assert body["total_servers"] == 1
        assert body["online_servers"] == 1

# ---------------------------------------------------------------------- #
# Agent relay                                                             #
# ---------------------------------------------------------------------- #


class TestRelayProvisioning:
    def test_create_relayed_server_provisions_target(
        self, mikrotik_client: TestClient, db_session
    ):
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        agent = Agent(name="edge-01", hostname="10.161.0.10", api_key="k", status="online")
        db_session.add(agent)
        db_session.commit()

        body = _create_server(
            mikrotik_client,
            name="relayed-sw",
            relay_agent_id=agent.id,
            ssh_port=2222,
            username="netadmin",
        )
        assert body["relay_agent_id"] == agent.id
        assert body["remote_target_id"] is not None

        target = db_session.get(AgentRemoteTarget, body["remote_target_id"])
        assert target is not None
        assert target.agent_id == agent.id
        assert target.protocol == "ssh"
        assert target.port == 2222
        assert target.username == "netadmin"
        cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
        assert cipher.decrypt(target.password_encrypted) == SERVER_PAYLOAD["password"]
        assert target.target_plugins == "mikrotik"

    def test_unknown_relay_agent_rejected(self, mikrotik_client: TestClient):
        response = mikrotik_client.post(
            "/api/v1/plugins/mikrotik/servers",
            json={**SERVER_PAYLOAD, "name": "bad-relay", "relay_agent_id": 424242},
        )
        assert response.status_code == 400

    def test_update_password_refreshes_target(
        self, mikrotik_client: TestClient, db_session
    ):
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        agent = Agent(name="edge-02", hostname="10.161.0.10", api_key="k", status="online")
        db_session.add(agent)
        db_session.commit()

        body = _create_server(mikrotik_client, name="relay-pw", relay_agent_id=agent.id)
        updated = mikrotik_client.put(
            f"/api/v1/plugins/mikrotik/servers/{body['id']}",
            json={"password": "rotated-pw-9"},
        )
        assert updated.status_code == 200

        target = db_session.get(AgentRemoteTarget, body["remote_target_id"])
        cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
        assert cipher.decrypt(target.password_encrypted) == "rotated-pw-9"
        assert target.target_plugins == "mikrotik"

    def test_sync_preserves_user_plugin_selection(
        self, mikrotik_client: TestClient, db_session
    ):
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        agent = Agent(name="edge-05", hostname="10.161.0.10", api_key="k", status="online")
        db_session.add(agent)
        db_session.commit()

        body = _create_server(mikrotik_client, name="relay-plugins", relay_agent_id=agent.id)
        target_id = body["remote_target_id"]
        assert target_id is not None

        # User curates the plugin selection on the auto-provisioned target.
        edited = mikrotik_client.put(
            f"/api/v1/agents/{agent.id}/remote-targets/{target_id}",
            json={"target_plugins": "veeam,docker"},
        )
        assert edited.status_code == 200

        # A later server update re-syncs the target; user picks must survive.
        resync = mikrotik_client.put(
            f"/api/v1/plugins/mikrotik/servers/{body['id']}",
            json={"host": SERVER_PAYLOAD["host"]},
        )
        assert resync.status_code == 200

        target = db_session.get(AgentRemoteTarget, target_id)
        parts = [p.strip() for p in (target.target_plugins or "").split(",") if p.strip()]
        assert "veeam" in parts
        assert "docker" in parts
        assert "mikrotik" in parts

    def test_clearing_relay_agent_deletes_target(
        self, mikrotik_client: TestClient, db_session
    ):
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        agent = Agent(name="edge-03", hostname="10.161.0.10", api_key="k", status="online")
        db_session.add(agent)
        db_session.commit()

        body = _create_server(mikrotik_client, name="relay-off", relay_agent_id=agent.id)
        target_id = body["remote_target_id"]
        response = mikrotik_client.put(
            f"/api/v1/plugins/mikrotik/servers/{body['id']}",
            json={"relay_agent_id": None},
        )
        assert response.status_code == 200
        assert response.json()["remote_target_id"] is None
        assert db_session.get(AgentRemoteTarget, target_id) is None

    def test_delete_server_removes_target(self, mikrotik_client: TestClient, db_session):
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        agent = Agent(name="edge-04", hostname="10.161.0.10", api_key="k", status="online")
        db_session.add(agent)
        db_session.commit()

        body = _create_server(mikrotik_client, name="relay-del", relay_agent_id=agent.id)
        target_id = body["remote_target_id"]
        deleted = mikrotik_client.delete(f"/api/v1/plugins/mikrotik/servers/{body['id']}")
        assert deleted.status_code == 200
        assert db_session.get(AgentRemoteTarget, target_id) is None

    def test_list_agents_endpoint(self, mikrotik_client: TestClient, db_session):
        from app.models.db.agent import Agent

        db_session.add(Agent(name="zz-listed", hostname="h", api_key="k", status="online"))
        db_session.commit()
        response = mikrotik_client.get("/api/v1/plugins/mikrotik/agents")
        assert response.status_code == 200
        names = [a["name"] for a in response.json()]
        assert "zz-listed" in names


class TestRelayExecutor:
    @staticmethod
    def _seed(db_session):
        from app.models.db.agent import Agent
        from app.plugins.installed.official_mikrotik.models import MikroTikServer

        agent = Agent(name="exec-agent", hostname="h", api_key="k", status="online")
        db_session.add(agent)
        server = MikroTikServer(name="exec-sw", host="10.161.0.14", username="admin")
        db_session.add(server)
        db_session.commit()
        server.relay_agent_id = agent.id
        server.remote_target_id = 555
        db_session.commit()
        return agent, server

    @staticmethod
    def _patch_commands(monkeypatch, states):
        """states: list of fake command rows returned by get_by_id in order."""
        from app.repositories.agent_repository import AgentCommandRepository

        seq = list(states)

        def fake_get_by_id(db, command_id):
            if len(seq) > 1:
                return seq.pop(0)
            return seq[0]

        monkeypatch.setattr(
            AgentCommandRepository, "get_by_id", staticmethod(fake_get_by_id)
        )

    @staticmethod
    def _last_dispatched_command(db_session):
        from app.models.db.agent_command import AgentCommand

        return (
            db_session.query(AgentCommand).order_by(AgentCommand.id.desc()).first()
        )

    @pytest.mark.asyncio
    async def test_success_path(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik.models import MikroTikCommandLog
        from app.plugins.installed.official_mikrotik.relay import relay_executor
        from app.plugins.installed.official_mikrotik.repository import (
            MikroTikRepository,
        )
        from app.plugins.installed.official_mikrotik.service import mikrotik_service

        agent, server = self._seed(db_session)

        class _Done:
            status = "completed"
            stdout = "name: exec-sw"
            stderr = ""
            exit_code = 0
            success = True

        self._patch_commands(monkeypatch, [_Done()])
        result = await relay_executor.execute_via_agent(
            db_session, server, "/system resource print", poll_interval=0.01
        )
        assert result.success is True
        assert result.output == "name: exec-sw"

        dispatched = self._last_dispatched_command(db_session)
        assert dispatched.command_type == "remote_execute"
        payload = json.loads(dispatched.command)
        assert payload == {"command": "/system resource print", "target_id": 555}

        await mikrotik_service.run_command(
            db_session, server, "/system resource print"
        )
        logs = MikroTikRepository.list_command_logs(db_session, server.id)
        assert logs[0].connector_type == "relay"
        refreshed = db_session.get(MikroTikCommandLog, logs[0].id)
        assert refreshed.success is True
        assert db_session.get(type(server), server.id).status == "online"
        assert agent.status == "online"

    @pytest.mark.asyncio
    async def test_failure_path_marks_unreachable(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik.service import mikrotik_service

        _, server = self._seed(db_session)

        class _Failed:
            status = "failed"
            stdout = ""
            stderr = "Permission denied"
            exit_code = 255
            success = False

        self._patch_commands(monkeypatch, [_Failed()])
        result = await mikrotik_service.run_command(
            db_session, server, "/system resource print"
        )
        assert result.success is False
        assert "Permission denied" in result.error
        assert server.status == "unreachable"
        assert server.last_error

    @pytest.mark.asyncio
    async def test_offline_agent_short_circuits(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik.relay import relay_executor

        agent, server = self._seed(db_session)
        agent.status = "offline"
        db_session.commit()

        self._patch_commands(monkeypatch, [])
        result = await relay_executor.execute_via_agent(
            db_session, server, "/system resource print", poll_interval=0.01
        )
        assert result.success is False
        assert "offline" in result.error
        assert self._last_dispatched_command(db_session) is None

    @pytest.mark.asyncio
    async def test_timeout_when_agent_never_reports(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik.relay import relay_executor

        _, server = self._seed(db_session)

        class _Pending:
            id = 778
            status = "pending"

        self._patch_commands(monkeypatch, [_Pending()])
        result = await relay_executor.execute_via_agent(
            db_session,
            server,
            "/system resource print",
            poll_interval=0.01,
            wait_deadline=0.05,
        )
        assert result.success is False
        assert "Timed out" in result.error

    def test_resolve_connector_type_prefers_relay(self):
        from app.plugins.installed.official_mikrotik.models import MikroTikServer
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        server = MikroTikServer(
            name="s", host="10.0.0.1", username="admin",
            api_enabled=True, relay_agent_id=3,
        )
        assert MikroTikService.resolve_connector_type(server) == "relay"

    @pytest.mark.asyncio
    async def test_retry_when_target_not_yet_learned(self, db_session, monkeypatch):
        from app.plugins.installed.official_mikrotik import relay as relay_module
        from app.plugins.installed.official_mikrotik.relay import relay_executor

        _, server = self._seed(db_session)
        monkeypatch.setattr(relay_module, "MISSING_CONNECTOR_GRACE_S", 0.01)

        class _NoConn:
            status = "failed"
            stdout = ""
            stderr = "No connector for target 555 (unknown)"
            exit_code = -1
            success = False

        class _Pending:
            id = 779
            status = "pending"

        class _Done:
            status = "completed"
            stdout = "name: exec-sw"
            stderr = ""
            exit_code = 0
            success = True

        self._patch_commands(monkeypatch, [_NoConn(), _Pending(), _Done()])
        result = await relay_executor.execute_via_agent(
            db_session,
            server,
            "/system resource print",
            poll_interval=0.01,
        )
        assert result.success is True
        assert result.output == "name: exec-sw"
        assert self._last_dispatched_command(db_session) is not None

    def test_parse_resource_output_cli_memory_strings(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        raw = (
            "uptime: 5d10h37m7s\n"
            "version: 7.24 (stable)\n"
            "board-name: hEX S\n"
            "cpu-load: 6%\n"
            "free-memory: 128.0MiB\n"
            "total-memory: 256.0MiB\n"
        )
        info = MikroTikService()._parse_resource_output(raw)
        assert info["version"] == "7.24 (stable)"
        assert info["memory_usage_pct"] == 50

    def test_parse_resource_output_cli_garbage_memory_is_none(self):
        from app.plugins.installed.official_mikrotik.service import MikroTikService

        raw = "version: 7.24 (stable)\nboard-name: hEX S\n"
        info = MikroTikService()._parse_resource_output(raw)
        assert info["memory_usage_pct"] is None
