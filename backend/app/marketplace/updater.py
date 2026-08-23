"""
Plugin Updater

Handles plugin updates: check for updates, update single/all, changelog, release notes.
Supports rollback to previous version if update fails.

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
from typing import Any

from app.marketplace.installer import plugin_installer
from app.marketplace.registry import marketplace_registry

logger = logging.getLogger(__name__)


class PluginUpdater:
    """Manages plugin updates and rollback."""

    def check_updates(self) -> list[dict[str, Any]]:
        """Return list of plugins with available updates."""
        with_updates = marketplace_registry.get_with_updates()
        return [
            {
                "plugin_id": p.plugin_id,
                "name": p.name,
                "current_version": p.version,
                "available_version": p.update_version,
                "changelog": p.changelog,
            }
            for p in with_updates
        ]

    def update_plugin(self, plugin_id: str, zip_path: str, repo_name: str = "") -> dict[str, Any]:
        """Update a single plugin to a new version."""
        plugin = marketplace_registry.get(plugin_id)
        if not plugin:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}

        if not plugin.update_version:
            return {"success": False, "error": "No update available"}

        logger.info("Updating %s from %s to %s", plugin_id, plugin.version, plugin.update_version)

        # Snapshot for rollback
        snapshot = marketplace_registry.snapshot()

        # Install new version
        meta = {
            "id": plugin_id,
            "name": plugin.name,
            "version": plugin.update_version,
            "sdk_version": "3.10",
        }
        result = plugin_installer.install(meta, zip_path, repo_name, trust_level="official")

        if result["success"]:
            marketplace_registry.record_update(plugin_id, plugin.update_version)
            logger.info("Plugin %s updated to %s", plugin_id, plugin.update_version)
        else:
            # Rollback on failure
            logger.warning("Update failed for %s, rolling back", plugin_id)
            marketplace_registry.restore_snapshot(snapshot)

        return result

    def update_all(self, updates: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Update multiple plugins.

        Args:
            updates: [{"plugin_id": str, "zip_path": str, "repo_name": str}]

        Returns:
            {"results": list, "succeeded": int, "failed": int}
        """
        results = []
        succeeded = 0
        failed = 0

        for update in updates:
            result = self.update_plugin(
                update["plugin_id"],
                update.get("zip_path", ""),
                update.get("repo_name", ""),
            )
            results.append(result)
            if result["success"]:
                succeeded += 1
            else:
                failed += 1

        return {"results": results, "succeeded": succeeded, "failed": failed}

    def rollback(self, plugin_id: str) -> dict[str, Any]:
        """Rollback a plugin to its previous version."""
        plugin = marketplace_registry.get(plugin_id)
        if not plugin:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}
        if not plugin.previous_version:
            return {"success": False, "error": "No previous version available for rollback"}
        return plugin_installer.rollback(plugin_id)

    def get_changelog(self, plugin_id: str) -> dict[str, Any]:
        """Get changelog for pending update."""
        plugin = marketplace_registry.get(plugin_id)
        if not plugin:
            return {"plugin_id": plugin_id, "changelog": "", "error": "Plugin not found"}
        return {
            "plugin_id": plugin_id,
            "current_version": plugin.version,
            "available_version": plugin.update_version,
            "changelog": plugin.changelog,
        }

    def get_release_notes(self, plugin_id: str) -> dict[str, Any]:
        """Get release notes for pending update."""
        plugin = marketplace_registry.get(plugin_id)
        if not plugin:
            return {"plugin_id": plugin_id, "release_notes": "", "error": "Plugin not found"}
        # In production, release notes come from repository
        return {
            "plugin_id": plugin_id,
            "current_version": plugin.version,
            "available_version": plugin.update_version,
            "release_notes": plugin.changelog,
        }


plugin_updater = PluginUpdater()
