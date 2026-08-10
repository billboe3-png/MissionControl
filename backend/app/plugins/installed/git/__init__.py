"""
Git Repository Integration Plugin

Production-grade plugin for Git repository monitoring.
Provides background sync, cached data, dashboard widgets,
plugin-scoped REST API, and Event Bus integration.

This plugin wraps the git CLI via subprocess calls and caches
results into local DB tables for dashboard widgets and REST API.
"""

import asyncio
import contextlib
import logging
import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.events import Event, EventType, event_bus
from app.plugins.installed.git.api import GitApiClient
from app.plugins.installed.git.cache import cache_manager
from app.plugins.installed.git.config import GitPluginConfig
from app.plugins.installed.git.models import GitRepository
from app.plugins.installed.git.routes import router
from app.plugins.installed.git.sync import (
    BranchSync,
    CommitSync,
    RemoteSync,
)
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.git")


class GitPlugin(ServerPluginSDK):
    """Git repository monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._clients: dict[int, GitApiClient] = {}
        self._sync_task: asyncio.Task[None] | None = None
        self._plugin_config: GitPluginConfig = GitPluginConfig(**config)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        """Initialize: load repository configs from IntegrationProfile and create clients."""
        def _load():
            session = SessionLocal()
            try:
                from app.repositories.integration_profile_repository import (
                    IntegrationProfileRepository,
                )
                profiles = IntegrationProfileRepository.get_all_enabled_by_type(
                    session, "git"
                )
                return [
                    {
                        "profile_id": p.id,
                        "name": p.name,
                        "path": p.base_url or "",
                    }
                    for p in profiles
                ]
            finally:
                session.close()

        repos = await asyncio.to_thread(_load)

        for repo in repos:
            if not repo["path"] or not os.path.isdir(repo["path"]):
                logger.warning("Git repo path does not exist: %s", repo["path"])
                continue

            client = GitApiClient(
                repo_path=repo["path"],
                timeout=self._plugin_config.git_timeout,
                retries=3,
            )
            self._clients[repo["profile_id"]] = client

        # Also check for the MissionControl project repo itself
        mc_root = os.environ.get("MISSIONCONTROL_PROJECT_ROOT", "")
        if mc_root and os.path.isdir(mc_root) and (mc_root not in [r["path"] for r in repos]):
            client = GitApiClient(
                repo_path=mc_root,
                timeout=self._plugin_config.git_timeout,
                retries=3,
            )
            self._clients[-1] = client  # -1 = local project repo

        logger.info(
            "Git plugin setup: %d repository(s) configured", len(self._clients)
        )

    async def start(self) -> None:
        """Start background sync task."""
        if self._plugin_config.auto_sync_enabled and self._clients:
            self._sync_task = asyncio.create_task(self._background_sync())
            logger.info(
                "Git background sync started (interval=%ds)",
                self._plugin_config.sync_interval_seconds,
            )

    async def stop(self) -> None:
        """Cancel sync task."""
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task
        self._clients.clear()
        logger.info("Git plugin stopped")

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def _background_sync(self) -> None:
        """Periodically sync data from all configured repositories."""
        while True:
            try:
                await self._run_sync_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Git sync cycle failed")
            await asyncio.sleep(self._plugin_config.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Run one sync cycle for all repositories."""
        def _load_repos():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(GitRepository).where(GitRepository.enabled.is_(True))
                    ).scalars().all()
                )
            finally:
                session.close()

        repos = await asyncio.to_thread(_load_repos)

        for repo in repos:
            client = self._clients.get(repo.id) or self._clients.get(-1)
            if not client:
                continue
            try:
                await self._sync_repo(client, repo)
                logger.debug("Sync completed for repo %s", repo.name)
            except Exception as exc:
                logger.warning("Sync failed for repo %s: %s", repo.name, exc)
                await self._mark_repo_error(repo.id, str(exc)[:500])

        await event_bus.publish(Event(
            type=EventType.PLUGIN_HEALTH_CHANGED,
            data={"plugin": "git", "status": "synced"},
            source="plugin.git",
        ))

    async def _sync_repo(self, client: GitApiClient, repo: GitRepository) -> None:
        """Sync all data for a single Git repository."""
        branch_sync = BranchSync()
        commit_sync = CommitSync()
        remote_sync = RemoteSync()
        repo_id = repo.id

        def _do_sync():
            session = SessionLocal()
            try:
                branch_sync.sync(session, client, repo_id)
                commit_sync.sync(session, client, repo_id, limit=self._plugin_config.max_commits)
                remote_sync.sync(session, client, repo_id)

                repo_row = session.get(GitRepository, repo_id)
                if repo_row:
                    repo_row.last_sync_at = datetime.now(UTC)
                    repo_row.status = "healthy"
                    repo_row.last_error = None
                session.commit()
            finally:
                session.close()

        await asyncio.to_thread(_do_sync)

    @staticmethod
    async def _mark_repo_error(repo_id: int, error_msg: str) -> None:
        """Write error state for a repo in a background thread."""

        def _write():
            session = SessionLocal()
            try:
                repo_row = session.get(GitRepository, repo_id)
                if repo_row:
                    repo_row.status = "error"
                    repo_row.last_error = error_msg
                session.commit()
            finally:
                session.close()

        await asyncio.to_thread(_write)

    # ------------------------------------------------------------------ #
    # Dashboard                                                           #
    # ------------------------------------------------------------------ #

    async def get_dashboard_widgets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "git-summary",
                "title": "Git Repository Overview",
                "component": "GitSummaryWidget",
                "size": "large",
                "refresh_interval": 120,
            },
            {
                "id": "git-branches",
                "title": "Branches",
                "component": "GitBranchesWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "git-recent-commits",
                "title": "Recent Commits",
                "component": "GitRecentCommitsWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "git-dirty-repos",
                "title": "Dirty Repositories",
                "component": "GitDirtyReposWidget",
                "size": "small",
                "refresh_interval": 300,
            },
            {
                "id": "git-remotes",
                "title": "Remotes",
                "component": "GitRemotesWidget",
                "size": "small",
                "refresh_interval": 300,
            },
        ]

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        def _query():
            session = SessionLocal()
            try:
                return self._fetch_widget_data(widget_id, session)
            finally:
                session.close()

        return await asyncio.to_thread(_query)

    def _fetch_widget_data(
        self, widget_id: str, session: Any,
    ) -> dict[str, Any]:
        """Fetch widget data from cache (runs in thread)."""
        if widget_id == "git-summary":
            return cache_manager.get_summary(session)
        if widget_id == "git-branches":
            return {"branches": cache_manager.get_branches(session)[:20]}
        if widget_id == "git-recent-commits":
            return {"commits": cache_manager.get_commits(session, limit=20)}
        if widget_id == "git-dirty-repos":
            from app.plugins.installed.git.models import GitRepository
            result = session.execute(
                select(GitRepository).where(GitRepository.status == "dirty")
            )
            repos = result.scalars().all()
            return {"repos": [{"id": r.id, "name": r.name, "path": r.path} for r in repos]}
        if widget_id == "git-remotes":
            return {"remotes": cache_manager.get_remotes(session)[:20]}
        return {}

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "git-overview",
                "label": "Git Overview",
                "icon": "git-branch",
                "path": "/plugins/git",
                "group": "Source Control",
                "order": 10,
            },
            {
                "id": "git-repositories",
                "label": "Repositories",
                "icon": "repo",
                "path": "/plugins/git/repositories",
                "group": "Source Control",
                "order": 20,
            },
            {
                "id": "git-branches",
                "label": "Branches",
                "icon": "git-branch",
                "path": "/plugins/git/branches",
                "group": "Source Control",
                "order": 30,
            },
            {
                "id": "git-commits",
                "label": "Commit History",
                "icon": "commit",
                "path": "/plugins/git/commits",
                "group": "Source Control",
                "order": 40,
            },
            {
                "id": "git-remotes",
                "label": "Remotes",
                "icon": "remote",
                "path": "/plugins/git/remotes",
                "group": "Source Control",
                "order": 50,
            },
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {
                "path": "/api/v1/plugins/git",
                "router": router,
                "summary": "Git plugin API",
            }
        ]

    # ------------------------------------------------------------------ #
    # Settings                                                            #
    # ------------------------------------------------------------------ #

    async def get_settings_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "auto_sync_enabled": {
                    "type": "boolean",
                    "title": "Auto-sync",
                    "default": True,
                },
                "sync_interval_seconds": {
                    "type": "integer",
                    "title": "Sync interval (seconds)",
                    "minimum": 30,
                    "maximum": 3600,
                    "default": 120,
                },
                "max_repos": {
                    "type": "integer",
                    "title": "Max repositories to monitor",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 50,
                },
                "max_commits": {
                    "type": "integer",
                    "title": "Max commits to cache per repo",
                    "minimum": 5,
                    "maximum": 500,
                    "default": 50,
                },
                "commit_retention_days": {
                    "type": "integer",
                    "title": "Commit history retention (days)",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                },
                "git_timeout": {
                    "type": "integer",
                    "title": "Git command timeout (seconds)",
                    "minimum": 5,
                    "maximum": 120,
                    "default": 30,
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self._plugin_config = GitPluginConfig(**settings)
        self.config.update(settings)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        def _query():
            session = SessionLocal()
            try:
                host_count = (session.execute(
                    select(func.count(GitRepository.id))
                )).scalar() or 0
                healthy_count = (session.execute(
                    select(func.count(GitRepository.id)).where(
                        GitRepository.status == "healthy"
                    )
                )).scalar() or 0
                return host_count, healthy_count
            finally:
                session.close()

        host_count, healthy_count = await asyncio.to_thread(_query)

        if host_count == 0:
            return {"status": "warning", "message": "No repositories configured"}

        if healthy_count == host_count:
            return {"status": "ok", "repos": host_count, "healthy": healthy_count}
        if healthy_count > 0:
            return {"status": "degraded", "repos": host_count, "healthy": healthy_count}
        return {"status": "error", "repos": host_count, "healthy": 0}
