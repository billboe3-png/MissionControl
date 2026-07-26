"""
Mission Control Plugin Loader

Handles dynamic plugin discovery, loading, and instantiation.
Plugins are loaded from a configurable plugins directory.
Each plugin must have a plugin.json manifest and a main module.
"""

import importlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from app.plugins.base import PluginSDK
from app.plugins.server import ServerPluginSDK
from app.schemas.plugin import PluginManifest

logger = logging.getLogger(__name__)

DEFAULT_PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "installed")


class PluginLoadError(Exception):
    """Raised when a plugin fails to load."""


class PluginLoader:
    """Discovers and loads plugins from the filesystem."""

    def __init__(self, plugins_dir: str | None = None):
        self.plugins_dir = Path(plugins_dir or DEFAULT_PLUGINS_DIR)
        self._loaded: dict[str, PluginSDK] = {}

    def discover(self) -> list[dict[str, Any]]:
        """Discover all valid plugins in the plugins directory.

        Returns a list of parsed manifests for valid plugins.
        """
        manifests = []

        if not self.plugins_dir.exists():
            logger.info("Plugins directory does not exist: %s", self.plugins_dir)
            return manifests

        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir():
                continue

            manifest_path = entry / "plugin.json"
            if not manifest_path.exists():
                continue

            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest = PluginManifest(**raw)
                manifests.append(raw)
                logger.info("Discovered plugin: %s v%s", manifest.id, manifest.version)
            except Exception:
                logger.exception("Invalid plugin manifest: %s", manifest_path)

        return manifests

    def load(self, slug: str) -> PluginSDK:
        """Load a plugin by its slug.

        The plugin directory must contain:
        - plugin.json (manifest)
        - __init__.py or main.py with a PluginSDK subclass

        The module must export a class that extends PluginSDK.
        """
        plugin_dir = self.plugins_dir / slug
        if not plugin_dir.exists():
            raise PluginLoadError(f"Plugin directory not found: {slug}")

        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.exists():
            raise PluginLoadError(f"Missing plugin.json in: {slug}")

        # Parse and validate manifest
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = PluginManifest(**raw)

        if manifest.id != slug:
            raise PluginLoadError(
                f"Manifest slug mismatch: expected '{slug}', got '{manifest.id}'"
            )

        # Dynamically import the plugin module
        module_name = f"app.plugins.installed.{slug}"
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise PluginLoadError(f"Failed to import plugin module '{module_name}': {exc}") from exc

        # Find the PluginSDK subclass (exclude base + abstract intermediaries)
        plugin_class = None
        _skip = {PluginSDK, ServerPluginSDK}
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginSDK)
                and attr not in _skip
            ):
                plugin_class = attr
                break

        if plugin_class is None:
            raise PluginLoadError(
                f"No PluginSDK subclass found in plugin module '{module_name}'"
            )

        # Instantiate
        config = json.loads(
            (plugin_dir / "config.json").read_text(encoding="utf-8")
        ) if (plugin_dir / "config.json").exists() else {}

        instance = plugin_class(manifest=raw, config=config)
        self._loaded[slug] = instance
        logger.info("Loaded plugin: %s (%s)", slug, plugin_class.__name__)
        return instance

    def get_loaded(self, slug: str) -> PluginSDK | None:
        """Return a loaded plugin instance by slug."""
        return self._loaded.get(slug)

    def get_all_loaded(self) -> dict[str, PluginSDK]:
        """Return all loaded plugin instances."""
        return dict(self._loaded)

    def unload(self, slug: str) -> bool:
        """Unload a plugin from memory."""
        if slug in self._loaded:
            del self._loaded[slug]
            logger.info("Unloaded plugin: %s", slug)
            return True
        return False

    async def setup_all(self) -> dict[str, str]:
        """Call setup() on all loaded plugins. Returns status per plugin."""
        results = {}
        for slug, plugin in self._loaded.items():
            try:
                await plugin.setup()
                results[slug] = "ok"
            except Exception as exc:
                results[slug] = f"error: {exc}"
                logger.exception("Plugin setup failed: %s", slug)
        return results

    async def start_all(self) -> dict[str, str]:
        """Call start() on all loaded plugins."""
        results = {}
        for slug, plugin in self._loaded.items():
            try:
                await plugin.start()
                results[slug] = "started"
            except Exception as exc:
                results[slug] = f"error: {exc}"
                logger.exception("Plugin start failed: %s", slug)
        return results

    async def stop_all(self) -> dict[str, str]:
        """Call stop() on all loaded plugins."""
        results = {}
        for slug, plugin in self._loaded.items():
            try:
                await plugin.stop()
                results[slug] = "stopped"
            except Exception as exc:
                results[slug] = f"error: {exc}"
                logger.exception("Plugin stop failed: %s", slug)
        return results


# Module-level singleton
plugin_loader = PluginLoader()
