"""
Git Plugin Tests

Tests for the Git plugin components: config, models, plugin class,
cache, routes, and registry integration.
"""

import json

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #


class TestGitPluginConfig:
    """Tests for GitPluginConfig pydantic model."""

    def test_default_config(self):
        from app.plugins.installed.git.config import GitPluginConfig

        cfg = GitPluginConfig()
        assert cfg.auto_sync_enabled is True
        assert cfg.sync_interval_seconds == 120
        assert cfg.max_repos == 50
        assert cfg.max_commits == 50
        assert cfg.commit_retention_days == 30
        assert cfg.git_timeout == 30

    def test_custom_config(self):
        from app.plugins.installed.git.config import GitPluginConfig

        cfg = GitPluginConfig(
            sync_interval_seconds=300,
            auto_sync_enabled=False,
            max_repos=10,
            max_commits=100,
        )
        assert cfg.sync_interval_seconds == 300
        assert cfg.auto_sync_enabled is False
        assert cfg.max_repos == 10
        assert cfg.max_commits == 100


# ------------------------------------------------------------------ #
# Models                                                               #
# ------------------------------------------------------------------ #


class TestGitPluginModels:
    """Tests for Git plugin SQLAlchemy models."""

    def test_git_repository_table_name(self):
        from app.plugins.installed.git.models import GitRepository

        assert GitRepository.__tablename__ == "git_repositories"

    def test_git_branch_table_name(self):
        from app.plugins.installed.git.models import GitBranch

        assert GitBranch.__tablename__ == "git_branches"

    def test_git_commit_table_name(self):
        from app.plugins.installed.git.models import GitCommit

        assert GitCommit.__tablename__ == "git_commits"

    def test_git_remote_table_name(self):
        from app.plugins.installed.git.models import GitRemote

        assert GitRemote.__tablename__ == "git_remotes"


# ------------------------------------------------------------------ #
# Plugin class                                                         #
# ------------------------------------------------------------------ #


class TestGitPlugin:
    """Tests for GitPlugin ServerPluginSDK subclass."""

    def test_plugin_manifest(self):
        from pathlib import Path

        manifest_path = (
            Path(__file__).parent.parent
            / "app"
            / "plugins"
            / "installed"
            / "git"
            / "plugin.json"
        )
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert raw["id"] == "git"
        assert raw["execution_target"] == "server"
        assert "dashboard_widget" in raw["capabilities"]

    def test_plugin_instantiation(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        assert plugin.slug == "git"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_setup_no_repos(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        await plugin.setup()
        assert plugin._clients == {}

    @pytest.mark.asyncio
    async def test_plugin_start_no_repos(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(
            manifest=manifest, config={"auto_sync_enabled": False}
        )
        await plugin.setup()
        await plugin.start()
        assert plugin._sync_task is None

    @pytest.mark.asyncio
    async def test_plugin_stop(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        await plugin.setup()
        await plugin.stop()

    @pytest.mark.asyncio
    async def test_get_dashboard_widgets(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        widgets = await plugin.get_dashboard_widgets()
        assert len(widgets) == 5
        widget_ids = [w["id"] for w in widgets]
        assert "git-summary" in widget_ids
        assert "git-branches" in widget_ids
        assert "git-recent-commits" in widget_ids

    @pytest.mark.asyncio
    async def test_get_navigation_items(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        nav = await plugin.get_navigation_items()
        assert len(nav) == 5
        nav_ids = [n["id"] for n in nav]
        assert "git-overview" in nav_ids
        assert "git-repositories" in nav_ids

    @pytest.mark.asyncio
    async def test_get_routes(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        routes = plugin.get_routes()
        assert len(routes) == 1
        assert routes[0]["path"] == "/api/v1/plugins/git"

    @pytest.mark.asyncio
    async def test_get_settings_schema(self):
        from app.plugins.installed.git import GitPlugin

        manifest = {
            "id": "git",
            "version": "1.0.0",
            "execution_target": "server",
            "capabilities": [],
        }
        plugin = GitPlugin(manifest=manifest, config={})
        schema = await plugin.get_settings_schema()
        assert schema["type"] == "object"
        assert "auto_sync_enabled" in schema["properties"]
        assert "max_repos" in schema["properties"]
        assert "git_timeout" in schema["properties"]


# ------------------------------------------------------------------ #
# Cache                                                              #
# ------------------------------------------------------------------ #


class TestGitPluginCache:
    """Tests for Git plugin cache."""

    def test_cache_manager_exists(self):
        from app.plugins.installed.git.cache import cache_manager

        assert cache_manager is not None
        assert hasattr(cache_manager, "get_summary")
        assert hasattr(cache_manager, "get_repositories")
        assert hasattr(cache_manager, "get_branches")
        assert hasattr(cache_manager, "get_commits")
        assert hasattr(cache_manager, "get_remotes")


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


class TestGitPluginRoutes:
    """Tests for /api/v1/plugins/git/* endpoints."""

    @pytest.fixture
    def git_client(self, db_session):
        """Provide a FastAPI test client with git plugin router mounted."""
        from app.db.database import get_db
        from app.main import app as _app
        from app.plugins.installed.git.routes import router as git_router

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        _app.dependency_overrides[get_db] = override_get_db
        _app.include_router(git_router)
        with TestClient(_app) as test_client:
            yield test_client
        _app.dependency_overrides.pop(get_db, None)

    def test_list_repositories_empty(self, git_client: TestClient) -> None:
        response = git_client.get("/api/v1/plugins/git/repositories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_branches_empty(self, git_client: TestClient) -> None:
        response = git_client.get("/api/v1/plugins/git/branches")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_commits_empty(self, git_client: TestClient) -> None:
        response = git_client.get("/api/v1/plugins/git/commits")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_remotes_empty(self, git_client: TestClient) -> None:
        response = git_client.get("/api/v1/plugins/git/remotes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_summary_empty(self, git_client: TestClient) -> None:
        response = git_client.get("/api/v1/plugins/git/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["repo_count"] == 0
        assert data["branch_count"] == 0

    def test_health_empty(self, git_client: TestClient) -> None:
        response = git_client.get("/api/v1/plugins/git/health")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["healthy"] == 0
