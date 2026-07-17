"""Mission Control Agent - Plugin framework."""

import importlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger("mc-agent")


class AgentPlugin(ABC):
    """Base class for all Mission Control Agent plugins."""

    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base plugin"
    platform_required: str | None = None

    @abstractmethod
    async def initialize(self, context: dict[str, Any]) -> bool:
        """Initialize the plugin. Return True if successful."""
        ...

    @abstractmethod
    async def collect_inventory(self) -> dict[str, Any]:
        """Collect plugin-specific inventory data."""
        ...

    @abstractmethod
    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a plugin-specific command."""
        ...

    async def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass

    def is_compatible(self) -> bool:
        """Check if this plugin can run on the current platform."""
        if self.platform_required is None:
            return True
        import platform

        current = platform.system().lower()
        return self.platform_required.lower() in current


class PluginManager:
    """Manages loading and lifecycle of agent plugins."""

    def __init__(self):
        self._plugins: dict[str, AgentPlugin] = {}
        self._initialized: dict[str, bool] = {}

    async def discover_plugins(self) -> list[str]:
        """Discover available plugins from the plugins directory."""
        plugins_dir = Path(__file__).parent / "plugins"
        discovered = []

        if not plugins_dir.exists():
            return discovered

        for py_file in plugins_dir.glob("*_plugin.py"):
            module_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(
                    f"agent.plugins.{module_name}", py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, AgentPlugin)
                            and attr is not AgentPlugin
                        ):
                            plugin = attr()
                            if plugin.is_compatible():
                                self._plugins[plugin.name] = plugin
                                discovered.append(plugin.name)
                                logger.info(
                                    "Discovered plugin: %s v%s",
                                    plugin.name,
                                    plugin.version,
                                )
            except Exception as e:
                logger.error(
                    "Failed to load plugin %s: %s",
                    module_name,
                    e,
                )

        return discovered

    async def initialize_plugins(
        self, context: dict[str, Any]
    ) -> dict[str, bool]:
        """Initialize all discovered plugins."""
        results = {}
        for name, plugin in self._plugins.items():
            try:
                success = await plugin.initialize(context)
                self._initialized[name] = success
                results[name] = success
                if success:
                    logger.info("Plugin %s initialized", name)
                else:
                    logger.warning(
                        "Plugin %s failed to initialize", name
                    )
            except Exception as e:
                logger.error(
                    "Plugin %s initialization error: %s", name, e
                )
                self._initialized[name] = False
                results[name] = False
        return results

    async def collect_all_inventory(self) -> dict[str, Any]:
        """Collect inventory from all initialized plugins."""
        inventory = {}
        for name, plugin in self._plugins.items():
            if self._initialized.get(name):
                try:
                    data = await plugin.collect_inventory()
                    inventory[name] = data
                except Exception as e:
                    logger.error(
                        "Plugin %s inventory failed: %s", name, e
                    )
                    inventory[name] = {"error": str(e)}
        return inventory

    async def execute_plugin_command(
        self, plugin_name: str, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a command on a specific plugin."""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return {
                "success": False,
                "error": f"Plugin not found: {plugin_name}",
            }
        if not self._initialized.get(plugin_name):
            return {
                "success": False,
                "error": f"Plugin not initialized: {plugin_name}",
            }
        return await plugin.execute_command(command, args)

    def get_active_plugins(self) -> str:
        """Get comma-separated list of active plugins."""
        active = [
            name
            for name, init in self._initialized.items()
            if init
        ]
        return ",".join(active)

    async def shutdown_all(self) -> None:
        """Shutdown all plugins."""
        for name, plugin in self._plugins.items():
            try:
                await plugin.shutdown()
                logger.info("Plugin %s shut down", name)
            except Exception as e:
                logger.error(
                    "Plugin %s shutdown error: %s", name, e
                )
        self._plugins.clear()
        self._initialized.clear()

    @property
    def plugin_count(self) -> int:
        return len(self._plugins)

    @property
    def active_count(self) -> int:
        return sum(1 for v in self._initialized.values() if v)
