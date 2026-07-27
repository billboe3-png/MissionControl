"""
Docker Plugin Tests

Tests for the Docker plugin components: config, models, plugin class,
cache, routes, and registry integration.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #


class TestDockerPluginConfig:
    """Tests for DockerPluginConfig pydantic model."""

    def test_default_config(self):
        from app.plugins.installed.official_docker.config import DockerPluginConfig

        cfg = DockerPluginConfig()
        assert cfg.hosts == []
        assert cfg.sync_interval_seconds == 120
        assert cfg.auto_sync_enabled is True
        assert cfg.max_containers == 2000
        assert cfg.cpu_warning_pct == 80.0

    def test_custom_config(self):
        from app.plugins.installed.official_docker.config import (
            DockerHostConfig,
            DockerPluginConfig,
        )

        cfg = DockerPluginConfig(
            hosts=[
                DockerHostConfig(
                    name="prod", host="192.168.1.10:2375", tls=True,
                )
            ],
            sync_interval_seconds=300,
            auto_sync_enabled=False,
        )
        assert len(cfg.hosts) == 1
        assert cfg.hosts[0].name == "prod"
        assert cfg.sync_interval_seconds == 300
        assert cfg.auto_sync_enabled is False

    def test_host_config_defaults(self):
        from app.plugins.installed.official_docker.config import DockerHostConfig

        host = DockerHostConfig()
        assert host.name == "default"
        assert host.host == ""
        assert host.tls is False
        assert host.timeout == 30
        assert host.retries == 3
        assert host.enabled is True


# ------------------------------------------------------------------ #
# Models                                                               #
# ------------------------------------------------------------------ #


class TestDockerPluginModels:
    """Tests for Docker plugin SQLAlchemy models."""

    def test_docker_host_table_name(self):
        from app.plugins.installed.official_docker.models import DockerHost

        assert DockerHost.__tablename__ == "docker_hosts"

    def test_docker_container_table_name(self):
        from app.plugins.installed.official_docker.models import DockerContainer

        assert DockerContainer.__tablename__ == "docker_containers"

    def test_docker_image_table_name(self):
        from app.plugins.installed.official_docker.models import DockerImage

        assert DockerImage.__tablename__ == "docker_images"

    def test_docker_volume_table_name(self):
        from app.plugins.installed.official_docker.models import DockerVolume

        assert DockerVolume.__tablename__ == "docker_volumes"

    def test_docker_network_table_name(self):
        from app.plugins.installed.official_docker.models import DockerNetwork

        assert DockerNetwork.__tablename__ == "docker_networks"

    def test_docker_compose_stack_table_name(self):
        from app.plugins.installed.official_docker.models import DockerComposeStack

        assert DockerComposeStack.__tablename__ == "docker_compose_stacks"


# ------------------------------------------------------------------ #
# Plugin class                                                         #
# ------------------------------------------------------------------ #


class TestDockerPlugin:
    """Tests for DockerPlugin ServerPluginSDK subclass."""

    def test_plugin_manifest(self):
        manifest_path = (
            Path(__file__).parent.parent
            / "app"
            / "plugins"
            / "installed"
            / "official_docker"
            / "plugin.json"
        )
        import json
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert raw["id"] == "official_docker"
        assert raw["execution_target"] == "server"
        assert "dashboard_widget" in raw["capabilities"]

    def test_plugin_instantiation(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        assert plugin.slug == "official_docker"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_setup_no_hosts(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        await plugin.setup()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_start_no_hosts(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={"auto_sync_enabled": False})
        await plugin.setup()
        await plugin.start()
        assert plugin._sync_task is None

    @pytest.mark.asyncio
    async def test_plugin_stop(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        await plugin.setup()
        await plugin.stop()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_health_check_no_clients(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        await plugin.setup()
        health = await plugin.health_check()
        assert health["status"] == "warning"

    @pytest.mark.asyncio
    async def test_get_dashboard_widgets(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 12
        widget_ids = [w["id"] for w in widgets]
        assert "docker-summary" in widget_ids
        assert "docker-containers-running" in widget_ids
        assert "docker-containers-unhealthy" in widget_ids
        assert "docker-compose" in widget_ids

    @pytest.mark.asyncio
    async def test_get_navigation_items(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        nav = await plugin.get_navigation_items()
        assert len(nav) == 6
        nav_ids = [n["id"] for n in nav]
        assert "docker-dashboard" in nav_ids
        assert "docker-containers" in nav_ids
        assert "docker-compose" in nav_ids

    @pytest.mark.asyncio
    async def test_get_routes(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        routes = plugin.get_routes()
        assert len(routes) == 1
        assert routes[0]["path"] == "/api/v1/plugins/docker"

    @pytest.mark.asyncio
    async def test_get_settings_schema(self):
        from app.plugins.installed.official_docker import DockerPlugin

        manifest = {
            "id": "official_docker",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = DockerPlugin(manifest=manifest, config={})
        schema = await plugin.get_settings_schema()
        assert schema["type"] == "object"
        assert "auto_sync_enabled" in schema["properties"]
        assert "cpu_warning_pct" in schema["properties"]
        assert "disk_warning_pct" in schema["properties"]


# ------------------------------------------------------------------ #
# Plugin API client                                                    #
# ------------------------------------------------------------------ #


class TestDockerApiClient:
    """Tests for DockerApiClient initialization."""

    def test_api_client_init(self):
        from app.plugins.installed.official_docker.api import DockerApiClient

        client = DockerApiClient(host="192.168.1.10:2375")
        assert client._host == "192.168.1.10:2375"
        assert client._tls is False

    def test_api_client_tls(self):
        from app.plugins.installed.official_docker.api import DockerApiClient

        client = DockerApiClient(
            host="docker.local:2376",
            tls=True,
            tls_cert_path="/certs",
            tls_verify=True,
        )
        assert client._tls is True
        assert client._tls_cert_path == "/certs"


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


class TestDockerPluginRoutes:
    """Tests for /api/v1/plugins/docker/* endpoints."""

    @pytest.fixture
    def docker_client(self, db_session):
        """Provide a FastAPI test client with docker plugin router mounted."""
        from app.db.database import get_db
        from app.main import app as _app
        from app.plugins.installed.official_docker.routes import router as docker_router

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        _app.dependency_overrides[get_db] = override_get_db
        _app.include_router(docker_router)
        with TestClient(_app) as test_client:
            yield test_client
        _app.dependency_overrides.pop(get_db, None)

    def test_summary_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["host_count"] == 0
        assert data["container_count"] == 0

    def test_list_hosts_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/hosts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_containers_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/containers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_images_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/images")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_volumes_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/volumes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_networks_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/networks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_compose_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/compose")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_resource_usage_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/resource-usage")
        assert response.status_code == 200
        data = response.json()
        assert data["running_count"] == 0

    def test_container_health_empty(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/container-health")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_health_no_hosts(self, docker_client: TestClient) -> None:
        response = docker_client.get("/api/v1/plugins/docker/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_hosts"
        assert data["hosts"] == 0
