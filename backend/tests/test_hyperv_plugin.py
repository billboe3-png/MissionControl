"""
Hyper-V Plugin Tests

Tests for the Hyper-V plugin components: config, models, plugin class,
cache, routes, and registry integration.
"""

import json

import pytest
from fastapi.testclient import TestClient


# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #


class TestHyperVPluginConfig:
    """Tests for HyperVPluginConfig pydantic model."""

    def test_default_config(self):
        from app.plugins.installed.hyperv.config import HyperVPluginConfig

        cfg = HyperVPluginConfig()
        assert cfg.auto_sync_enabled is True
        assert cfg.sync_interval_seconds == 120
        assert cfg.max_vms == 2000
        assert cfg.max_networks == 200
        assert cfg.max_volumes == 500
        assert cfg.max_checkpoints == 500
        assert cfg.cpu_warning_pct == 80.0
        assert cfg.cpu_critical_pct == 95.0

    def test_custom_config(self):
        from app.plugins.installed.hyperv.config import HyperVPluginConfig

        cfg = HyperVPluginConfig(
            sync_interval_seconds=300,
            auto_sync_enabled=False,
            max_vms=500,
        )
        assert cfg.sync_interval_seconds == 300
        assert cfg.auto_sync_enabled is False
        assert cfg.max_vms == 500


# ------------------------------------------------------------------ #
# Models                                                               #
# ------------------------------------------------------------------ #


class TestHyperVPluginModels:
    """Tests for Hyper-V plugin SQLAlchemy models."""

    def test_hyperv_host_table_name(self):
        from app.plugins.installed.hyperv.models import HyperVHost

        assert HyperVHost.__tablename__ == "hyperv_hosts"

    def test_hyperv_vm_table_name(self):
        from app.plugins.installed.hyperv.models import HyperVVM

        assert HyperVVM.__tablename__ == "hyperv_vms"

    def test_hyperv_network_table_name(self):
        from app.plugins.installed.hyperv.models import HyperVNetwork

        assert HyperVNetwork.__tablename__ == "hyperv_networks"

    def test_hyperv_volume_table_name(self):
        from app.plugins.installed.hyperv.models import HyperVVolume

        assert HyperVVolume.__tablename__ == "hyperv_volumes"

    def test_hyperv_checkpoint_table_name(self):
        from app.plugins.installed.hyperv.models import HyperVCheckpoint

        assert HyperVCheckpoint.__tablename__ == "hyperv_checkpoints"


# ------------------------------------------------------------------ #
# Plugin class                                                         #
# ------------------------------------------------------------------ #


class TestHyperVPlugin:
    """Tests for HyperVPlugin ServerPluginSDK subclass."""

    def test_plugin_manifest(self):
        from pathlib import Path

        manifest_path = (
            Path(__file__).parent.parent
            / "app"
            / "plugins"
            / "installed"
            / "hyperv"
            / "plugin.json"
        )
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert raw["id"] == "hyperv"
        assert raw["execution_target"] == "server"
        assert "dashboard_widget" in raw["capabilities"]

    def test_plugin_instantiation(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        assert plugin.slug == "hyperv"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_setup_no_hosts(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        await plugin.setup()
        assert plugin._host_cache == {}

    @pytest.mark.asyncio
    async def test_plugin_start_no_hosts(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(
            manifest=manifest, config={"auto_sync_enabled": False}
        )
        await plugin.setup()
        await plugin.start()
        assert plugin._sync_task is None

    @pytest.mark.asyncio
    async def test_plugin_stop(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        await plugin.setup()
        await plugin.stop()

    @pytest.mark.asyncio
    async def test_get_dashboard_widgets(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 5
        widget_ids = [w["id"] for w in widgets]
        assert "hyperv-summary" in widget_ids
        assert "hyperv-vms-running" in widget_ids
        assert "hyperv-checkpoints" in widget_ids

    @pytest.mark.asyncio
    async def test_get_navigation_items(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        nav = await plugin.get_navigation_items()
        assert len(nav) == 5
        nav_ids = [n["id"] for n in nav]
        assert "hyperv-overview" in nav_ids
        assert "hyperv-vms" in nav_ids

    @pytest.mark.asyncio
    async def test_get_routes(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        routes = plugin.get_routes()
        assert len(routes) == 1
        assert routes[0]["path"] == "/api/v1/plugins/hyperv"

    @pytest.mark.asyncio
    async def test_get_settings_schema(self):
        from app.plugins.installed.hyperv import HyperVPlugin

        manifest = {
            "id": "hyperv",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = HyperVPlugin(manifest=manifest, config={})
        schema = await plugin.get_settings_schema()
        assert schema["type"] == "object"
        assert "auto_sync_enabled" in schema["properties"]
        assert "cpu_warning_pct" in schema["properties"]
        assert "max_vms" in schema["properties"]


# ------------------------------------------------------------------ #
# Cache                                                              #
# ------------------------------------------------------------------ #


class TestHyperVPluginCache:
    """Tests for Hyper-V plugin cache."""

    def test_cache_manager_exists(self):
        from app.plugins.installed.hyperv.cache import cache_manager

        assert cache_manager is not None
        assert hasattr(cache_manager, "get_summary")
        assert hasattr(cache_manager, "get_hosts")
        assert hasattr(cache_manager, "get_vms")
        assert hasattr(cache_manager, "get_networks")
        assert hasattr(cache_manager, "get_volumes")
        assert hasattr(cache_manager, "get_checkpoints")


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


class TestHyperVPluginRoutes:
    """Tests for /api/v1/plugins/hyperv/* endpoints."""

    @pytest.fixture
    def hyperv_client(self, db_session):
        """Provide a FastAPI test client with hyperv plugin router mounted."""
        from app.db.database import get_db
        from app.main import app as _app
        from app.plugins.installed.hyperv.routes import router as hyperv_router

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        _app.dependency_overrides[get_db] = override_get_db
        _app.include_router(hyperv_router)
        with TestClient(_app) as test_client:
            yield test_client
        _app.dependency_overrides.pop(get_db, None)

    def test_list_hosts_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/hosts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_vms_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/vms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_networks_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/networks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_volumes_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/volumes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_checkpoints_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/checkpoints")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_summary_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["vm_count"] == 0
        assert data["running_count"] == 0

    def test_health_empty(self, hyperv_client: TestClient) -> None:
        response = hyperv_client.get("/api/v1/plugins/hyperv/health")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["healthy"] == 0
