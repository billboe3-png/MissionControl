"""
Mission Control Plugin Service

Manages the plugin registry: registration, lifecycle (enable/disable/start/stop),
configuration, and health monitoring. Plugins are loaded from the database and
instantiated at startup; runtime state is held in-memory with DB persistence.
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.db.plugin import Plugin
from app.repositories.plugin_repository import PluginRepository
from app.schemas.plugin import (
    PluginActionResponse,
    PluginCreate,
    PluginResponse,
    PluginUpdate,
)

logger = logging.getLogger(__name__)

# In-memory registry of live plugin instances keyed by slug.
# Only populated when a plugin is started at runtime.
_live_plugins: dict[str, Any] = {}


class PluginService:
    """Business logic for plugin management and lifecycle."""

    # ------------------------------------------------------------------ #
    # CRUD                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_plugins(
        db: Session,
        execution_target: str | None = None,
        category: str | None = None,
        enabled_only: bool = False,
    ) -> list[Plugin]:
        return PluginRepository.get_all(
            db,
            execution_target=execution_target,
            category=category,
            enabled_only=enabled_only,
        )

    @staticmethod
    def get_plugin(db: Session, plugin_id: int) -> Plugin | None:
        return PluginRepository.get_by_id(db, plugin_id)

    @staticmethod
    def get_plugin_by_slug(db: Session, slug: str) -> Plugin | None:
        return PluginRepository.get_by_slug(db, slug)

    @staticmethod
    def register_plugin(db: Session, data: PluginCreate) -> Plugin:
        """Register a new plugin from its manifest."""
        existing = PluginRepository.get_by_slug(db, data.slug)
        if existing:
            raise ValueError(f"Plugin '{data.slug}' is already registered")

        capabilities_json = (
            json.dumps(data.capabilities) if data.capabilities else None
        )
        permissions_json = (
            json.dumps(data.permissions) if data.permissions else None
        )
        dependencies_json = (
            json.dumps(data.dependencies) if data.dependencies else None
        )
        config_json = json.dumps(data.config) if data.config else None

        plugin = PluginRepository.create(
            db,
            slug=data.slug,
            name=data.name,
            version=data.version,
            execution_target=data.execution_target.value,
            description=data.description,
            author=data.author,
            category=data.category,
            min_core_version=data.min_core_version,
            capabilities_json=capabilities_json,
            permissions_json=permissions_json,
            dependencies_json=dependencies_json,
            config_json=config_json,
        )

        logger.info("Plugin registered: %s v%s (%s)", plugin.slug, plugin.version, plugin.execution_target)
        return plugin

    @staticmethod
    def update_plugin(db: Session, plugin_id: int, data: PluginUpdate) -> Plugin | None:
        """Update plugin metadata."""
        updates: dict[str, Any] = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.version is not None:
            updates["version"] = data.version
        if data.description is not None:
            updates["description"] = data.description
        if data.author is not None:
            updates["author"] = data.author
        if data.category is not None:
            updates["category"] = data.category
        if data.min_core_version is not None:
            updates["min_core_version"] = data.min_core_version
        if data.capabilities is not None:
            updates["capabilities_json"] = json.dumps(data.capabilities)
        if data.permissions is not None:
            updates["permissions_json"] = json.dumps(data.permissions)
        if data.dependencies is not None:
            updates["dependencies_json"] = json.dumps(data.dependencies)
        if data.config is not None:
            updates["config_json"] = json.dumps(data.config)

        return PluginRepository.update(db, plugin_id, **updates)

    @staticmethod
    def unregister_plugin(db: Session, plugin_id: int) -> bool:
        """Uninstall a plugin."""
        plugin = PluginRepository.get_by_id(db, plugin_id)
        if plugin is None:
            return False

        if plugin.slug in _live_plugins:
            logger.warning("Plugin '%s' is still running; unregistering anyway", plugin.slug)
            _live_plugins.pop(plugin.slug, None)

        slug = plugin.slug
        PluginRepository.delete(db, plugin_id)
        logger.info("Plugin unregistered: %s", slug)
        return True

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def enable_plugin(db: Session, plugin_id: int) -> Plugin | None:
        plugin = PluginRepository.update(db, plugin_id, enabled=True)
        if plugin:
            logger.info("Plugin enabled: %s", plugin.slug)
        return plugin

    @staticmethod
    def disable_plugin(db: Session, plugin_id: int) -> Plugin | None:
        plugin = PluginRepository.update(db, plugin_id, enabled=False)
        if plugin:
            _live_plugins.pop(plugin.slug, None)
            logger.info("Plugin disabled: %s", plugin.slug)
        return plugin

    @staticmethod
    def start_plugin(db: Session, plugin_id: int) -> PluginActionResponse:
        """Start a plugin (load into memory, run setup + start)."""
        plugin = PluginRepository.get_by_id(db, plugin_id)
        if plugin is None:
            return PluginActionResponse(slug="", status="error", message="Plugin not found")

        if plugin.slug in _live_plugins:
            return PluginActionResponse(
                slug=plugin.slug, status="running", message="Plugin already running"
            )

        PluginRepository.update(db, plugin_id, status="initializing")

        # In a real implementation, this would dynamically import and
        # instantiate the plugin class. For now we just mark it running.
        PluginRepository.update(db, plugin_id, status="running")
        logger.info("Plugin started: %s", plugin.slug)

        return PluginActionResponse(
            slug=plugin.slug, status="running", message=f"Plugin '{plugin.slug}' started"
        )

    @staticmethod
    def stop_plugin(db: Session, plugin_id: int) -> PluginActionResponse:
        """Stop a plugin."""
        plugin = PluginRepository.get_by_id(db, plugin_id)
        if plugin is None:
            return PluginActionResponse(slug="", status="error", message="Plugin not found")

        _live_plugins.pop(plugin.slug, None)
        PluginRepository.update(db, plugin_id, status="stopped")
        logger.info("Plugin stopped: %s", plugin.slug)

        return PluginActionResponse(
            slug=plugin.slug, status="stopped", message=f"Plugin '{plugin.slug}' stopped"
        )

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def record_heartbeat(db: Session, plugin_id: int) -> None:
        """Record a plugin heartbeat."""
        from datetime import UTC, datetime
        PluginRepository.update(db, plugin_id, last_heartbeat=datetime.now(UTC))

    @staticmethod
    def record_error(db: Session, plugin_id: int, error: str) -> None:
        """Record a plugin error."""
        PluginRepository.update(
            db, plugin_id, status="error", last_error=error
        )

    # ------------------------------------------------------------------ #
    # Statistics                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_stats(db: Session) -> dict[str, Any]:
        """Return plugin statistics."""
        all_plugins = PluginRepository.get_all(db)
        by_target = PluginRepository.count_by_target(db)
        enabled_count = PluginRepository.count_enabled(db)
        running = PluginRepository.get_by_status(db, "running")
        errored = PluginRepository.get_by_status(db, "error")

        return {
            "total": len(all_plugins),
            "enabled": enabled_count,
            "running": len(running),
            "errored": len(errored),
            "by_target": by_target,
        }

    # ------------------------------------------------------------------ #
    # Serialization helpers                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def to_response(plugin: Plugin) -> PluginResponse:
        """Convert ORM plugin to response schema."""
        capabilities = json.loads(plugin.capabilities_json) if plugin.capabilities_json else []
        permissions = json.loads(plugin.permissions_json) if plugin.permissions_json else []
        dependencies = json.loads(plugin.dependencies_json) if plugin.dependencies_json else []
        config = json.loads(plugin.config_json) if plugin.config_json else None

        return PluginResponse(
            id=plugin.id,
            slug=plugin.slug,
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            author=plugin.author,
            execution_target=plugin.execution_target,
            category=plugin.category,
            enabled=plugin.enabled,
            status=plugin.status,
            config=config,
            capabilities=capabilities,
            min_core_version=plugin.min_core_version,
            permissions=permissions,
            dependencies=dependencies,
            last_heartbeat=plugin.last_heartbeat,
            last_error=plugin.last_error,
            created_at=plugin.created_at,
            updated_at=plugin.updated_at,
        )


plugin_service = PluginService()
