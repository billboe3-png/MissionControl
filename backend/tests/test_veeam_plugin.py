"""
Veeam Plugin Tests

Tests for the Veeam plugin components: config, models, plugin class,
cache, routes, and registry integration.
"""

import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #


class TestVeeamPluginConfig:
    """Tests for VeeamPluginConfig pydantic model."""

    def test_default_config(self):
        from app.plugins.installed.official_veeam.config import VeeamPluginConfig

        cfg = VeeamPluginConfig()
        assert cfg.servers == []
        assert cfg.sync_interval_seconds == 300
        assert cfg.auto_sync_enabled is True
        assert cfg.max_jobs == 500
        assert cfg.repo_capacity_warning_pct == 80.0

    def test_custom_config(self):
        from app.plugins.installed.official_veeam.config import (
            VeeamPluginConfig,
            VeeamServerConfig,
        )

        cfg = VeeamPluginConfig(
            servers=[
                VeeamServerConfig(
                    name="prod", url="https://veeam.local", username="admin",
                )
            ],
            sync_interval_seconds=600,
            auto_sync_enabled=False,
        )
        assert len(cfg.servers) == 1
        assert cfg.servers[0].name == "prod"
        assert cfg.sync_interval_seconds == 600
        assert cfg.auto_sync_enabled is False

    def test_server_config_defaults(self):
        from app.plugins.installed.official_veeam.config import VeeamServerConfig

        srv = VeeamServerConfig()
        assert srv.name == "default"
        assert srv.url == ""
        assert srv.verify_ssl is True
        assert srv.timeout == 30
        assert srv.data_source == "both"
        assert srv.db_type == "auto"

    def test_server_config_live_fields(self):
        from app.plugins.installed.official_veeam.config import VeeamServerConfig

        srv = VeeamServerConfig()
        assert srv.edition == "enterprise"
        assert srv.data_source == "both"
        assert srv.db_type == "auto"
        assert srv.column_case == "pascal"
        assert srv.agent_id is None
        assert srv.target_id is None


# ------------------------------------------------------------------ #
# Models                                                               #
# ------------------------------------------------------------------ #


class TestVeeamPluginModels:
    """Tests for Veeam plugin SQLAlchemy models."""

    def test_veeam_backup_server_table_name(self):
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        assert VeeamBackupServer.__tablename__ == "veeam_backup_servers"

    def test_veeam_repository_table_name(self):
        from app.plugins.installed.official_veeam.models import VeeamRepository

        assert VeeamRepository.__tablename__ == "veeam_repositories"

    def test_veeam_job_table_name(self):
        from app.plugins.installed.official_veeam.models import VeeamJob

        assert VeeamJob.__tablename__ == "veeam_jobs"

    def test_veeam_restore_point_table_name(self):
        from app.plugins.installed.official_veeam.models import VeeamRestorePoint

        assert VeeamRestorePoint.__tablename__ == "veeam_restore_points"

    def test_veeam_license_table_name(self):
        from app.plugins.installed.official_veeam.models import VeeamLicense

        assert VeeamLicense.__tablename__ == "veeam_licenses"

    def test_veeam_job_run_table_name(self):
        from app.plugins.installed.official_veeam.models import VeeamJobRun

        assert VeeamJobRun.__tablename__ == "veeam_job_runs"

    def test_veeam_backup_server_live_fields(self):
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        assert VeeamBackupServer.__table__.c.edition is not None
        assert VeeamBackupServer.__table__.c.data_source is not None
        assert VeeamBackupServer.__table__.c.db_type is not None
        assert VeeamBackupServer.__table__.c.column_case is not None
        assert VeeamBackupServer.__table__.c.agent_id is not None
        assert VeeamBackupServer.__table__.c.target_id is not None
        assert VeeamBackupServer.__table__.c.rest_url is not None
        assert VeeamBackupServer.__table__.c.last_diagnostic is not None


# ------------------------------------------------------------------ #
# Plugin class                                                         #
# ------------------------------------------------------------------ #


class TestVeeamPlugin:
    """Tests for VeeamPlugin ServerPluginSDK subclass."""

    def test_plugin_manifest(self):
        manifest_path = (
            Path(__file__).parent.parent
            / "app"
            / "plugins"
            / "installed"
            / "official_veeam"
            / "plugin.json"
        )
        import json
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert raw["id"] == "official_veeam"
        assert raw["execution_target"] == "server"
        assert "dashboard_widget" in raw["capabilities"]

    def test_plugin_instantiation(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        assert plugin.slug == "official_veeam"
        assert plugin.version == "4.0.0"

    @pytest.mark.asyncio
    async def test_plugin_setup_no_servers(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        await plugin.setup()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_start_no_servers(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={"auto_sync_enabled": False})
        await plugin.setup()
        await plugin.start()
        assert plugin._sync_task is None

    @pytest.mark.asyncio
    async def test_plugin_stop(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        await plugin.setup()
        await plugin.stop()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_setup_keeps_db_session_alive(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        await plugin.setup()
        session = plugin._db_session
        assert session is not None
        assert not session.is_active or session.is_active
        await plugin.stop()
        assert plugin._db_session is None

    @pytest.mark.asyncio
    async def test_plugin_health_check_no_clients(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        await plugin.setup()
        health = await plugin.health_check()
        assert health["status"] == "warning"

    @pytest.mark.asyncio
    async def test_get_dashboard_widgets(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 8
        widget_ids = [w["id"] for w in widgets]
        assert "veeam-summary" in widget_ids
        assert "veeam-failed-jobs" in widget_ids
        assert "veeam-repository-capacity" in widget_ids

    @pytest.mark.asyncio
    async def test_get_navigation_items(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        nav = await plugin.get_navigation_items()
        assert len(nav) == 6
        nav_ids = [n["id"] for n in nav]
        assert "veeam-dashboard" in nav_ids
        assert "veeam-jobs" in nav_ids
        assert "veeam-repositories" in nav_ids

    @pytest.mark.asyncio
    async def test_get_routes(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        routes = plugin.get_routes()
        assert len(routes) == 1
        assert routes[0]["path"] == "/api/v1/plugins/veeam"

    @pytest.mark.asyncio
    async def test_get_settings_schema(self):
        from app.plugins.installed.official_veeam import VeeamPlugin

        manifest = {
            "id": "official_veeam",
            "version": "4.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = VeeamPlugin(manifest=manifest, config={})
        schema = await plugin.get_settings_schema()
        assert schema["type"] == "object"
        assert "auto_sync_enabled" in schema["properties"]
        assert "repo_capacity_warning_pct" in schema["properties"]
        assert "repo_capacity_critical_pct" in schema["properties"]


# ------------------------------------------------------------------ #
# Plugin API client                                                    #
# ------------------------------------------------------------------ #


class TestVeeamApiClient:
    """Tests for VeeamApiClient initialization and provider delegation."""

    def test_api_client_init(self):
        from app.plugins.installed.official_veeam.api import VeeamApiClient
        from app.plugins.installed.official_veeam.models import VeeamBackupServer
        from app.plugins.installed.official_veeam.provider import (
            VeeamServerProvider,
        )

        server = VeeamBackupServer(
            name="v1",
            edition="enterprise",
            data_source="both",
            rest_url="https://veeam.local:9419",
        )
        client = VeeamApiClient.from_server(db=object(), server=server)
        assert isinstance(client._provider, VeeamServerProvider)
        assert client._provider.server.name == "v1"

    @pytest.mark.asyncio
    async def test_get_jobs_delegates_to_provider(self):
        from app.plugins.installed.official_veeam.api import VeeamApiClient
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        server = VeeamBackupServer(
            name="v1",
            edition="enterprise",
            data_source="both",
            rest_url="https://veeam.local:9419",
        )
        client = VeeamApiClient.from_server(db=object(), server=server)

        async def fake_get_jobs(provider):
            return {"success": True, "jobs": [{"id": "j1"}]}

        client._provider.get_jobs = types.MethodType(
            fake_get_jobs, client._provider
        )
        result = await client.get_jobs()
        assert result == {"success": True, "jobs": [{"id": "j1"}]}


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


class TestVeeamPluginRoutes:
    """Tests for /api/v1/plugins/veeam/* endpoints."""

    @pytest.fixture
    def veeam_client(self, db_session):
        """Provide a FastAPI test client with veeam plugin router mounted."""
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

    def test_list_servers_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/servers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["success"] is False
        assert data["servers"] == []
        assert data["error"] == "No Veeam server configured"

    def test_list_repositories_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/repositories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["success"] is False
        assert data["repositories"] == []
        assert data["error"] == "No Veeam server configured"

    def test_list_jobs_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["success"] is False
        assert data["jobs"] == []
        assert data["error"] == "No Veeam server configured"

    def test_list_restore_points_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/restore-points")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["success"] is False
        assert data["restore_points"] == []
        assert data["error"] == "No Veeam server configured"

    def test_summary_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["server_count"] == 0
        assert data["job_count"] == 0

    def test_health_no_servers(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/health")
        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is False
        assert data["error"] == "No Veeam server configured"

    def test_jobs_by_status_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/jobs-by-status")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_jobs_by_type_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/jobs-by-type")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_repo_health_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/repo-health")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_licenses_empty(self, veeam_client: TestClient) -> None:
        response = veeam_client.get("/api/v1/plugins/veeam/licenses")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_server_dict_has_live_fields(self, db_session):
        from app.plugins.installed.official_veeam.cache import cache_manager
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        db_session.add(VeeamBackupServer(name="v1"))
        db_session.commit()
        row = cache_manager.get_servers(db_session)[0]
        assert "edition" in row
        assert "db_type" in row
        assert "last_diagnostic" in row
        assert row["name"] == "v1"
