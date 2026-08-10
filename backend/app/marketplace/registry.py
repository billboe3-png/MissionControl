"""
Marketplace Registry

Central registry for installed plugins with their marketplace metadata.
Tracks versions, install dates, update status, health, and rollback state.
All plugin installation state lives here.

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class PluginStatus(StrEnum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"
    INCOMPATIBLE = "incompatible"
    DEPRECATED = "deprecated"
    UPDATE_AVAILABLE = "update_available"
    SECURITY_WARNING = "security_warning"


class PluginHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class InstalledPlugin:
    """Represents an installed plugin with its full state."""

    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        repo: str = "",
        installed_at: str = "",
        updated_at: str = "",
        status: str = PluginStatus.INSTALLED,
        health: str = PluginHealth.UNKNOWN,
        signature_status: str = "unsigned",
        checksum: str = "",
        enabled: bool = True,
        dependencies: list[str] | None = None,
        previous_version: str = "",
        update_version: str = "",
        changelog: str = "",
        permissions: list[str] | None = None,
        error_message: str = "",
    ) -> None:
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.repo = repo
        self.installed_at = installed_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or self.installed_at
        self.status = status
        self.health = health
        self.signature_status = signature_status
        self.checksum = checksum
        self.enabled = enabled
        self.dependencies = dependencies or []
        self.previous_version = previous_version
        self.update_version = update_version
        self.changelog = changelog
        self.permissions = permissions or []
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "repo": self.repo,
            "installed_at": self.installed_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "health": self.health,
            "signature_status": self.signature_status,
            "checksum": self.checksum,
            "enabled": self.enabled,
            "dependencies": self.dependencies,
            "previous_version": self.previous_version,
            "update_version": self.update_version,
            "changelog": self.changelog,
            "permissions": self.permissions,
            "error_message": self.error_message,
        }


class MarketplaceRegistry:
    """Central registry for all installed marketplace plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, InstalledPlugin] = {}

    def register(self, plugin: InstalledPlugin) -> None:
        """Register or update a plugin in the registry."""
        self._plugins[plugin.plugin_id] = plugin
        logger.info("Registry: %s v%s registered (%s)", plugin.plugin_id, plugin.version, plugin.status)

    def unregister(self, plugin_id: str) -> bool:
        """Remove a plugin from the registry."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            logger.info("Registry: %s unregistered", plugin_id)
            return True
        return False

    def get(self, plugin_id: str) -> InstalledPlugin | None:
        return self._plugins.get(plugin_id)

    def get_all(self) -> list[InstalledPlugin]:
        return list(self._plugins.values())

    def get_by_status(self, status: str) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.status == status]

    def get_enabled(self) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.enabled]

    def get_with_updates(self) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.update_version and p.update_version != p.version]

    def get_deprecated(self) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.status == PluginStatus.DEPRECATED]

    def get_security_warnings(self) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.status == PluginStatus.SECURITY_WARNING]

    def get_failed(self) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.status == PluginStatus.FAILED]

    def get_incompatible(self) -> list[InstalledPlugin]:
        return [p for p in self._plugins.values() if p.status == PluginStatus.INCOMPATIBLE]

    def set_enabled(self, plugin_id: str, enabled: bool) -> bool:
        plugin = self.get(plugin_id)
        if plugin:
            plugin.enabled = enabled
            plugin.status = PluginStatus.ENABLED if enabled else PluginStatus.DISABLED
            plugin.updated_at = datetime.now(UTC).isoformat()
            return True
        return False

    def set_health(self, plugin_id: str, health: str, error: str = "") -> bool:
        plugin = self.get(plugin_id)
        if plugin:
            plugin.health = health
            plugin.error_message = error
            return True
        return False

    def set_update_available(self, plugin_id: str, new_version: str, changelog: str = "") -> bool:
        plugin = self.get(plugin_id)
        if plugin:
            plugin.update_version = new_version
            plugin.changelog = changelog
            plugin.status = PluginStatus.UPDATE_AVAILABLE
            return True
        return False

    def record_update(self, plugin_id: str, new_version: str) -> bool:
        plugin = self.get(plugin_id)
        if plugin:
            plugin.previous_version = plugin.version
            plugin.version = new_version
            plugin.update_version = ""
            plugin.changelog = ""
            plugin.status = PluginStatus.INSTALLED
            plugin.updated_at = datetime.now(UTC).isoformat()
            return True
        return False

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a full snapshot of registry state for rollback."""
        return {pid: p.to_dict() for pid, p in self._plugins.items()}

    def restore_snapshot(self, snapshot: dict[str, dict[str, Any]]) -> None:
        """Restore registry state from a snapshot (rollback)."""
        self._plugins.clear()
        for pid, data in snapshot.items():
            self._plugins[pid] = InstalledPlugin(
                plugin_id=pid,
                **{k: v for k, v in data.items() if k != "plugin_id"},
            )
        logger.info("Registry restored from snapshot: %d plugins", len(self._plugins))

    def summary(self) -> dict[str, Any]:
        """Return a marketplace health summary."""
        all_p = self.get_all()
        return {
            "total": len(all_p),
            "enabled": len([p for p in all_p if p.enabled]),
            "installed": len(self.get_by_status(PluginStatus.INSTALLED)),
            "updates_available": len(self.get_with_updates()),
            "disabled": len(self.get_by_status(PluginStatus.DISABLED)),
            "failed": len(self.get_failed()),
            "incompatible": len(self.get_incompatible()),
            "deprecated": len(self.get_deprecated()),
            "security_warnings": len(self.get_security_warnings()),
        }

    def to_dicts(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._plugins.values()]


marketplace_registry = MarketplaceRegistry()
