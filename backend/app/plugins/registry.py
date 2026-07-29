"""
Mission Control Plugin Registry

Manages the lifecycle of server plugins at startup:
discover → load → setup → start → register routes.

Provides runtime access to live plugin instances for
dashboard data, health checks, and background tasks.
"""

import inspect
import logging
from typing import Any

from fastapi import FastAPI

from app.plugins.loader import PluginLoader, plugin_loader
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for live server plugin instances."""

    def __init__(self) -> None:
        self._loader: PluginLoader = plugin_loader
        self._live: dict[str, ServerPluginSDK] = {}

    # ------------------------------------------------------------------ #
    # Startup lifecycle                                                    #
    # ------------------------------------------------------------------ #

    async def discover_and_load(self) -> dict[str, str]:
        """Discover, load, and instantiate all valid plugins."""
        manifests = self._loader.discover()
        results: dict[str, str] = {}

        for raw in manifests:
            slug = raw.get("id", "")
            if not slug:
                continue
            try:
                instance = self._loader.load(slug)
                if isinstance(instance, ServerPluginSDK):
                    self._live[slug] = instance
                    results[slug] = "loaded"
                else:
                    results[slug] = "skipped (not server plugin)"
            except Exception as exc:
                results[slug] = f"load_error: {exc}"
                logger.exception("Failed to load plugin: %s", slug)

        logger.info("Plugin discovery complete: %d loaded", len(self._live))
        return results

    async def setup_all(self) -> dict[str, str]:
        """Call setup() on all loaded plugins."""
        results: dict[str, str] = {}
        for slug, plugin in self._live.items():
            try:
                await plugin.setup()
                results[slug] = "ok"
                logger.info("Plugin setup: %s", slug)
            except Exception as exc:
                results[slug] = f"error: {exc}"
                logger.exception("Plugin setup failed: %s", slug)
        return results

    async def start_all(self) -> dict[str, str]:
        """Call start() on all loaded plugins."""
        results: dict[str, str] = {}
        for slug, plugin in self._live.items():
            try:
                await plugin.start()
                results[slug] = "started"
                logger.info("Plugin started: %s", slug)
            except Exception as exc:
                results[slug] = f"error: {exc}"
                logger.exception("Plugin start failed: %s", slug)
        return results

    async def stop_all(self) -> dict[str, str]:
        """Call stop() on all loaded plugins."""
        results: dict[str, str] = {}
        for slug, plugin in self._live.items():
            try:
                await plugin.stop()
                results[slug] = "stopped"
            except Exception as exc:
                results[slug] = f"error: {exc}"
                logger.exception("Plugin stop failed: %s", slug)
        self._live.clear()
        return results

    # ------------------------------------------------------------------ #
    # Route registration                                                   #
    # ------------------------------------------------------------------ #

    async def register_routes(self, app: FastAPI) -> int:
        """Register plugin-provided FastAPI routes with the app.

        Returns the number of routers registered.
        """
        registered = 0
        for slug, plugin in self._live.items():
            try:
                raw_routes = plugin.get_routes()
                if inspect.isawaitable(raw_routes):
                    routes = await raw_routes
                else:
                    routes = raw_routes
                for route_def in routes:
                    route_router = route_def.get("router")
                    if route_router is not None:
                        # Each plugin router already declares its own prefix
                        # (e.g. "/api/v1/plugins/unifi"); include it as-is so the
                        # route path is not double-prefixed.
                        prefix = route_def.get("path", "")
                        app.include_router(route_router)
                        registered += 1
                        logger.info(
                            "Plugin route registered: %s -> %s",
                            slug,
                            prefix,
                        )
            except Exception:
                logger.exception("Failed to register routes for plugin: %s", slug)
        return registered

    # ------------------------------------------------------------------ #
    # Runtime access                                                       #
    # ------------------------------------------------------------------ #

    def get_plugin(self, slug: str) -> ServerPluginSDK | None:
        """Return a live plugin instance by slug."""
        return self._live.get(slug)

    def get_all_plugins(self) -> dict[str, ServerPluginSDK]:
        """Return all live plugin instances."""
        return dict(self._live)

    def has_plugin(self, slug: str) -> bool:
        """Check if a plugin is loaded and running."""
        return slug in self._live

    async def get_widget_data(self, slug: str, widget_id: str) -> dict[str, Any]:
        """Get dashboard widget data from a live plugin."""
        plugin = self._live.get(slug)
        if plugin is None:
            return {}
        try:
            return await plugin.get_widget_data(widget_id)
        except Exception:
            logger.exception("Widget data failed: %s/%s", slug, widget_id)
            return {}

    async def get_health(self) -> dict[str, dict[str, Any]]:
        """Get health status from all live plugins."""
        health: dict[str, dict[str, Any]] = {}
        for slug, plugin in self._live.items():
            try:
                health[slug] = await plugin.health_check()
            except Exception:
                health[slug] = {"status": "error", "message": "Health check failed"}
        return health


# Module-level singleton
plugin_registry = PluginRegistry()
