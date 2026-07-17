"""
Mission Control Plugin SDK — Base Class

All plugins must extend PluginSDK and implement at minimum
the lifecycle methods: setup(), start(), stop().
"""

from abc import ABC, abstractmethod
from typing import Any


class PluginSDK(ABC):
    """
    Abstract base class for all Mission Control plugins.

    Provides the lifecycle interface and shared utilities.
    Each plugin instance receives its manifest metadata and
    runtime configuration at construction time.
    """

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]):
        self.manifest = manifest
        self.config = config
        self._logger_name = f"plugin.{manifest.get('id', 'unknown')}"

    @property
    def slug(self) -> str:
        return self.manifest.get("id", "unknown")

    @property
    def version(self) -> str:
        return self.manifest.get("version", "0.0.0")

    @property
    def execution_target(self) -> str:
        return self.manifest.get("execution_target", "server")

    # ------------------------------------------------------------------ #
    # Lifecycle (must implement)                                          #
    # ------------------------------------------------------------------ #

    @abstractmethod
    async def setup(self) -> None:
        """Initialize plugin resources (DB tables, HTTP clients, etc.)."""

    @abstractmethod
    async def start(self) -> None:
        """Start background tasks, register routes, begin processing."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down: cancel tasks, close connections."""

    # ------------------------------------------------------------------ #
    # Optional hooks                                                      #
    # ------------------------------------------------------------------ #

    async def on_enable(self) -> None:
        """Called when the plugin is enabled by the administrator."""

    async def on_disable(self) -> None:
        """Called when the plugin is disabled by the administrator."""

    async def on_config_changed(self, new_config: dict[str, Any]) -> None:
        """Called when the administrator updates plugin configuration."""

    async def health_check(self) -> dict[str, Any]:
        """Return health status. Override to provide custom health checks."""
        return {"status": "ok", "version": self.version}

    async def get_capabilities(self) -> list[str]:
        """Return list of capabilities this plugin provides."""
        return self.manifest.get("capabilities", [])

    # ------------------------------------------------------------------ #
    # Utilities                                                           #
    # ------------------------------------------------------------------ #

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with optional default."""
        return self.config.get(key, default)

    def require_config(self, key: str) -> Any:
        """Get a required configuration value or raise ValueError."""
        if key not in self.config:
            raise ValueError(
                f"Plugin '{self.slug}' requires config key '{key}'"
            )
        return self.config[key]
