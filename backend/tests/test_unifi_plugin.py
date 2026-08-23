"""
UniFi Plugin Tests

Tests for the UniFi plugin components: config, models, plugin class,
cache, routes, and registry integration.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #


class TestUniFiPluginConfig:
    """Tests for UniFiPluginConfig pydantic model."""

    def test_default_config(self):
        from app.plugins.installed.official_unifi.config import UniFiPluginConfig

        cfg = UniFiPluginConfig()
        assert cfg.controllers == []
        assert cfg.sync_interval_seconds == 300
        assert cfg.auto_sync_enabled is True
        assert cfg.max_clients == 2000
        assert cfg.max_devices == 500

    def test_custom_config(self):
        from app.plugins.installed.official_unifi.config import (
            UniFiControllerConfig,
            UniFiPluginConfig,
        )

        cfg = UniFiPluginConfig(
            controllers=[
                UniFiControllerConfig(
                    name="office", url="https://unifi.local", api_key="key123",
                )
            ],
            sync_interval_seconds=600,
            auto_sync_enabled=False,
        )
        assert len(cfg.controllers) == 1
        assert cfg.controllers[0].name == "office"
        assert cfg.sync_interval_seconds == 600
        assert cfg.auto_sync_enabled is False

    def test_controller_config_defaults(self):
        from app.plugins.installed.official_unifi.config import UniFiControllerConfig

        ctrl = UniFiControllerConfig()
        assert ctrl.name == "default"
        assert ctrl.url == ""
        assert ctrl.verify_ssl is True
        assert ctrl.timeout == 30
        assert ctrl.retries == 3
        assert ctrl.controller_type == "cloud"


# ------------------------------------------------------------------ #
# Models                                                               #
# ------------------------------------------------------------------ #


class TestUniFiPluginModels:
    """Tests for UniFi plugin SQLAlchemy models."""

    def test_unifi_controller_table_name(self):
        from app.plugins.installed.official_unifi.models import UniFiController

        assert UniFiController.__tablename__ == "unifi_controllers"

    def test_unifi_site_table_name(self):
        from app.plugins.installed.official_unifi.models import UniFiSite

        assert UniFiSite.__tablename__ == "unifi_sites"

    def test_unifi_device_table_name(self):
        from app.plugins.installed.official_unifi.models import UniFiDevice

        assert UniFiDevice.__tablename__ == "unifi_devices"

    def test_unifi_client_table_name(self):
        from app.plugins.installed.official_unifi.models import UniFiClient

        assert UniFiClient.__tablename__ == "unifi_clients"

    def test_unifi_alert_table_name(self):
        from app.plugins.installed.official_unifi.models import UniFiAlert

        assert UniFiAlert.__tablename__ == "unifi_alerts"

    def test_unifi_wireless_network_table_name(self):
        from app.plugins.installed.official_unifi.models import UniFiWirelessNetwork

        assert UniFiWirelessNetwork.__tablename__ == "unifi_wireless_networks"


# ------------------------------------------------------------------ #
# Plugin class                                                         #
# ------------------------------------------------------------------ #


class TestUniFiPlugin:
    """Tests for UniFiPlugin ServerPluginSDK subclass."""

    def test_plugin_manifest(self):
        manifest_path = (
            Path(__file__).parent.parent
            / "app"
            / "plugins"
            / "installed"
            / "official_unifi"
            / "plugin.json"
        )
        import json
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert raw["id"] == "official_unifi"
        assert raw["execution_target"] == "server"
        assert "dashboard_widget" in raw["capabilities"]

    def test_plugin_instantiation(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        assert plugin.slug == "official_unifi"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_setup_no_controllers(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        await plugin.setup()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_start_no_controllers(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={"auto_sync_enabled": False})
        await plugin.setup()
        await plugin.start()
        assert plugin._sync_task is None

    @pytest.mark.asyncio
    async def test_plugin_stop(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        await plugin.setup()
        await plugin.stop()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_health_check_no_clients(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        await plugin.setup()
        health = await plugin.health_check()
        assert health["status"] == "warning"

    @pytest.mark.asyncio
    async def test_get_dashboard_widgets(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 12
        widget_ids = [w["id"] for w in widgets]
        assert "unifi-summary" in widget_ids
        assert "unifi-devices-by-status" in widget_ids
        assert "unifi-access-points" in widget_ids
        assert "unifi-topology" in widget_ids

    @pytest.mark.asyncio
    async def test_get_navigation_items(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        nav = await plugin.get_navigation_items()
        assert len(nav) == 6
        nav_ids = [n["id"] for n in nav]
        assert "unifi-dashboard" in nav_ids
        assert "unifi-devices" in nav_ids
        assert "unifi-clients" in nav_ids

    @pytest.mark.asyncio
    async def test_get_routes(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        routes = plugin.get_routes()
        assert len(routes) == 1
        assert routes[0]["path"] == "/api/v1/plugins/unifi"

    @pytest.mark.asyncio
    async def test_get_settings_schema(self):
        from app.plugins.installed.official_unifi import UniFiPlugin

        manifest = {
            "id": "official_unifi",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = UniFiPlugin(manifest=manifest, config={})
        schema = await plugin.get_settings_schema()
        assert schema["type"] == "object"
        assert "auto_sync_enabled" in schema["properties"]
        assert "cpu_warning_pct" in schema["properties"]
        assert "temperature_warning_c" in schema["properties"]


# ------------------------------------------------------------------ #
# Plugin API client                                                    #
# ------------------------------------------------------------------ #


class TestUniFiApiClient:
    """Tests for UniFiApiClient initialization."""

    def test_api_client_init(self):
        from app.plugins.installed.official_unifi.api import UniFiApiClient

        client = UniFiApiClient(
            url="https://unifi.ui.com",
            api_key="key123",
        )
        assert client._url == "https://unifi.ui.com"
        assert client._api_key == "key123"
        assert client._controller_type == "cloud"

    def test_api_client_local(self):
        from app.plugins.installed.official_unifi.api import UniFiApiClient

        client = UniFiApiClient(
            url="https://192.168.1.1:8443",
            api_key="local-key",
            controller_type="local",
            verify_ssl=False,
        )
        assert client._controller_type == "local"
        assert client._verify_ssl is False


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


# ------------------------------------------------------------------ #
# Plugin routes                                                        #
# ------------------------------------------------------------------ #


class TestUniFiPluginRoutes:
    """Tests for /api/v1/plugins/unifi/* endpoints."""

    @pytest.fixture
    def unifi_client(self, db_session):
        """Provide a FastAPI test client with unifi plugin router mounted."""
        from app.db.database import get_db
        from app.main import app as _app
        from app.plugins.installed.official_unifi.routes import router as unifi_router

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        _app.dependency_overrides[get_db] = override_get_db
        _app.include_router(unifi_router)
        with TestClient(_app) as test_client:
            yield test_client
        _app.dependency_overrides.pop(get_db, None)

    def test_list_controllers_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/controllers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_sites_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/sites")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_devices_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/devices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_clients_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/clients")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_alerts_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_wireless_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/wireless")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_summary_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["controller_count"] == 0
        assert data["device_count"] == 0

    def test_health_no_controllers(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_controllers"
        assert data["controllers"] == 0

    def test_devices_by_status_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/devices-by-status")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_devices_by_type_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/devices-by-type")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_list_access_points_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/access-points")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_switches_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/switches")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_gateways_empty(self, unifi_client: TestClient) -> None:
        response = unifi_client.get("/api/v1/plugins/unifi/gateways")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
