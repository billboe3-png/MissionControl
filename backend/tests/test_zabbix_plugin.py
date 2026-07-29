"""
Zabbix Plugin Tests

Tests for the Zabbix plugin components: config, models, API client,
sync, routes, registry, and plugin class.
"""

import json

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #


class TestZabbixPluginConfig:
    """Tests for ZabbixPluginConfig pydantic model."""

    def test_default_config(self):
        from app.plugins.installed.zabbix.config import ZabbixPluginConfig

        cfg = ZabbixPluginConfig()
        assert cfg.servers == []
        assert cfg.sync_interval_seconds == 300
        assert cfg.auto_sync_enabled is True
        assert cfg.max_problems_per_host == 50
        assert cfg.event_retention_days == 30

    def test_custom_config(self):
        from app.plugins.installed.zabbix.config import (
            ZabbixPluginConfig,
            ZabbixServerConfig,
        )

        cfg = ZabbixPluginConfig(
            servers=[ZabbixServerConfig(name="prod", url="https://zabbix.example.com", username="admin")],
            sync_interval_seconds=600,
            auto_sync_enabled=False,
        )
        assert len(cfg.servers) == 1
        assert cfg.servers[0].name == "prod"
        assert cfg.sync_interval_seconds == 600
        assert cfg.auto_sync_enabled is False

    def test_server_config_defaults(self):
        from app.plugins.installed.zabbix.config import ZabbixServerConfig

        srv = ZabbixServerConfig()
        assert srv.name == "default"
        assert srv.url == ""
        assert srv.verify_ssl is True
        assert srv.timeout == 30
        assert srv.retries == 3
        assert srv.enabled is True


# ------------------------------------------------------------------ #
# Models                                                               #
# ------------------------------------------------------------------ #


class TestZabbixPluginModels:
    """Tests for Zabbix plugin SQLAlchemy models."""

    def test_zabbix_server_table_name(self):
        from app.plugins.installed.zabbix.models import ZabbixServer

        assert ZabbixServer.__tablename__ == "zabbix_servers"

    def test_zabbix_host_table_name(self):
        from app.plugins.installed.zabbix.models import ZabbixHost

        assert ZabbixHost.__tablename__ == "zabbix_hosts"

    def test_zabbix_problem_table_name(self):
        from app.plugins.installed.zabbix.models import ZabbixProblem

        assert ZabbixProblem.__tablename__ == "zabbix_problems"

    def test_zabbix_event_table_name(self):
        from app.plugins.installed.zabbix.models import ZabbixEvent

        assert ZabbixEvent.__tablename__ == "zabbix_events"


# ------------------------------------------------------------------ #
# Plugin class                                                         #
# ------------------------------------------------------------------ #


class TestZabbixPlugin:
    """Tests for ZabbixPlugin ServerPluginSDK subclass."""

    def test_plugin_manifest(self):
        from pathlib import Path

        manifest_path = Path(__file__).parent.parent / "app" / "plugins" / "installed" / "zabbix" / "plugin.json"
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert raw["id"] == "zabbix"
        assert raw["execution_target"] == "server"
        assert "dashboard_widget" in raw["capabilities"]

    def test_plugin_instantiation(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        assert plugin.slug == "zabbix"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_setup_no_servers(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        await plugin.setup()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_start_no_servers(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={"auto_sync_enabled": False})
        await plugin.setup()
        await plugin.start()
        assert plugin._sync_task is None

    @pytest.mark.asyncio
    async def test_plugin_stop(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        await plugin.setup()
        await plugin.stop()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_health_check_no_clients(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        await plugin.setup()
        health = await plugin.health_check()
        assert health["status"] == "warning"

    @pytest.mark.asyncio
    async def test_get_dashboard_widgets(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 2
        assert widgets[0]["id"] == "zabbix-summary"
        assert widgets[1]["id"] == "zabbix-problems"

    @pytest.mark.asyncio
    async def test_get_navigation_items(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        nav = await plugin.get_navigation_items()
        assert len(nav) == 3
        assert nav[0]["id"] == "zabbix-overview"

    @pytest.mark.asyncio
    async def test_get_routes(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        routes = plugin.get_routes()
        assert len(routes) == 1
        assert routes[0]["path"] == "/api/v1/plugins/zabbix"

    @pytest.mark.asyncio
    async def test_get_settings_schema(self):
        from app.plugins.installed.zabbix import ZabbixPlugin

        manifest = {"id": "zabbix", "version": "1.0.0", "execution_target": "server", "capabilities": []}
        plugin = ZabbixPlugin(manifest=manifest, config={})
        schema = await plugin.get_settings_schema()
        assert schema["type"] == "object"
        assert "auto_sync_enabled" in schema["properties"]


# ------------------------------------------------------------------ #
# Plugin API client                                                    #
# ------------------------------------------------------------------ #


class TestZabbixApiClient:
    """Tests for ZabbixApiClient."""

    def test_api_client_init(self):
        from app.plugins.installed.zabbix.api import ZabbixApiClient

        client = ZabbixApiClient(
            url="https://zabbix.example.com",
            username="admin",
            password="secret",
        )
        assert client._url == "https://zabbix.example.com"
        assert client._username == "admin"
        assert client._auth_token is None

    def test_next_id(self):
        from app.plugins.installed.zabbix.api import ZabbixApiClient

        client = ZabbixApiClient(url="http://localhost", username="a", password="b")
        assert client._next_id() == 1
        assert client._next_id() == 2
        assert client._next_id() == 3

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        from app.plugins.installed.zabbix.api import ZabbixApiClient

        client = ZabbixApiClient(url="http://localhost", username="a", password="b")
        await client.close()
        assert client._client is None or client._client.is_closed


# ------------------------------------------------------------------ #
# Registry                                                             #
# ------------------------------------------------------------------ #


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_registry_singleton(self):
        from app.plugins.registry import PluginRegistry, plugin_registry

        assert isinstance(plugin_registry, PluginRegistry)

    def test_registry_get_plugin_empty(self):
        from app.plugins.registry import plugin_registry

        assert plugin_registry.get_plugin("nonexistent") is None
        assert plugin_registry.has_plugin("nonexistent") is False

    def test_registry_get_all_empty(self):
        from app.plugins.registry import plugin_registry

        plugins = plugin_registry.get_all_plugins()
        assert isinstance(plugins, dict)


# ------------------------------------------------------------------ #
# Plugin routes                                                        #
# ------------------------------------------------------------------ #


class TestZabbixPluginRoutes:
    """Tests for /api/v1/plugins/zabbix/* endpoints."""

    @pytest.fixture
    def zabbix_client(self, db_session):
        """Provide a FastAPI test client with zabbix router mounted."""
        from app.db.database import get_db
        from app.main import app as _app
        from app.plugins.installed.zabbix.routes import router as zabbix_router

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        _app.dependency_overrides[get_db] = override_get_db
        _app.include_router(zabbix_router)
        with TestClient(_app) as test_client:
            yield test_client
        _app.dependency_overrides.pop(get_db, None)

    def test_list_servers_empty(self, zabbix_client: TestClient) -> None:
        response = zabbix_client.get("/api/v1/plugins/zabbix/servers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_hosts_empty(self, zabbix_client: TestClient) -> None:
        response = zabbix_client.get("/api/v1/plugins/zabbix/hosts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_problems_empty(self, zabbix_client: TestClient) -> None:
        response = zabbix_client.get("/api/v1/plugins/zabbix/problems")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_events_empty(self, zabbix_client: TestClient) -> None:
        response = zabbix_client.get("/api/v1/plugins/zabbix/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_summary_empty(self, zabbix_client: TestClient) -> None:
        response = zabbix_client.get("/api/v1/plugins/zabbix/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["host_count"] == 0
        assert data["problem_count"] == 0
