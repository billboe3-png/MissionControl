"""Mission Control Edge Agent - Core orchestrator.

Ties together storage, plugins, sync, and remote targets into a single
offline-first edge collector loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import socket
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent.config import AgentSettings
from agent.logger import setup_logging
from agent.plugin import PluginManager
from agent.remote import RemoteManager
from agent.storage import EdgeStorage, HeartbeatRecord, InventoryRecord, StorageConfig
from agent.sync import EdgeSync, SyncResult

logger = logging.getLogger("mc-agent")


class EdgeCore:
    """Offline-first edge agent core."""

    def __init__(self, config: AgentSettings):
        self.config = config
        self._running = False
        self._agent_id: int | None = config.agent_id

        # Local storage
        db_path = Path(config.data_dir) / "edge.db"
        self._storage = EdgeStorage(StorageConfig(db_path=db_path))

        # Plugin manager
        self._plugin_manager = PluginManager(data_dir=config.data_dir)

        # Remote manager
        self._remote_manager = RemoteManager()

        # Sync manager
        self._sync: EdgeSync | None = None

    async def start(self) -> None:
        """Start the edge agent."""
        logger.info("Mission Control Edge Agent starting")
logger.info("DEBUG server=%s agent_id=%s api_key_prefix=%s", self.config.server_url, self._agent_id, (self.config.api_key or "")[:12])
        logger.info("Data dir: %s", self.config.data_dir)
        logger.info("Server: %s | SSL verify: %s", self.config.server_url, self.config.verify_ssl)

        self._running = True

        # Initialize plugins with a real RemoteManager so relay can work
        # even before the first successful config pull.
        await self._plugin_manager.discover_plugins()
        await self._plugin_manager.initialize_plugins(context={
            "agent_id": self._agent_id,
            "remote_manager": self._remote_manager,
            "integration_profiles": [],
            "remote_targets": [],
        })

        # Initialize sync
        self._sync = EdgeSync(
            storage=self._storage,
            base_url=self.config.server_url,
            api_key=self.config.api_key,
            agent_id=self._agent_id or 0,
            verify_ssl=self.config.verify_ssl,
        )

        # Run main loops
        await asyncio.gather(
            self._sync_loop(),
            self._heartbeat_loop(),
            self._inventory_loop(),
        )

    async def stop(self) -> None:
        """Stop the edge agent."""
        logger.info("Edge agent stopping...")
        self._running = False
        await self._plugin_manager.shutdown_all()
        if self._sync:
            self._sync.close()
        self._storage.close()

    def _request_restart(self) -> None:
        """Request a graceful restart of the edge agent."""
        logger.info("New bundle applied; requesting graceful restart")
        self._running = False

    # ------------------------------------------------------------------ #
    # Sync loop
    # ------------------------------------------------------------------ #

    async def _sync_loop(self) -> None:
        """Periodic config pull + data push."""
        interval = max(30, self.config.heartbeat_interval or 60)
        while self._running:
            try:
                if self._sync:
                    results = self._sync.run_sync_cycle()
                    for name, result in results.items():
                        if name == "config" and result.success:
                            self._apply_pulled_manifest()
                        if name == "bundle" and result.success and getattr(result, "restart_requested", False):
                            logger.info("New bundle applied; requesting agent restart")
                            self._request_restart()
                        if result.success:
                            logger.debug("Sync %s: success", name)
                        else:
                            logger.warning("Sync %s failed: %s", name, result.error)
            except Exception as e:
                logger.error("Sync loop error: %s", e)
            await asyncio.sleep(interval)

    # ------------------------------------------------------------------ #
    # Heartbeat loop
    # ------------------------------------------------------------------ #

    async def _heartbeat_loop(self) -> None:
        """Local heartbeat logging."""
        interval = max(10, self.config.heartbeat_interval or 60)
        while self._running:
            try:
                start = time.monotonic()
                record = HeartbeatRecord(
                    agent_id=self._agent_id or 0,
                    status="online",
                    latency_ms=(time.monotonic() - start) * 1000.0,
                    pushed_at=datetime.now(UTC).isoformat(),
                )
                self._storage.append_heartbeat(record)

                # Push heartbeat if sync is available
                if self._sync:
                    result = self._sync.push_heartbeat(record)
                    if not result.success:
                        logger.debug("Heartbeat push deferred: %s", result.error)
            except Exception as e:
                logger.error("Heartbeat loop error: %s", e)
            await asyncio.sleep(interval)

    # ------------------------------------------------------------------ #
    # Inventory loop
    # ------------------------------------------------------------------ #

    async def _inventory_loop(self) -> None:
        """Run plugins and cache results locally."""
        interval = max(60, self.config.heartbeat_interval * 2 or 120)
        while self._running:
            try:
                await self._run_all_plugins()
            except Exception as e:
                logger.error("Inventory loop error: %s", e)
            await asyncio.sleep(interval)

    async def _run_all_plugins(self) -> None:
        """Execute all enabled plugins and store results."""
        plugins = list(self._plugin_manager._plugins.keys())
        if not plugins:
            logger.debug("No plugins discovered")
            return

        for plugin_name in plugins:
            if not self._running:
                break
            await self._run_single_plugin(plugin_name)

    async def _run_single_plugin(self, plugin_name: str) -> None:
        """Run one plugin and store its inventory."""
        started = datetime.now(UTC).isoformat()
        start_mono = time.monotonic()
        try:
            result = await self._plugin_manager.execute(plugin_name)
            duration_ms = (time.monotonic() - start_mono) * 1000.0

            record = InventoryRecord(
                plugin_name=plugin_name,
                data=result if isinstance(result, dict) else {"value": str(result)},
                checksum="",
                collected_at=started,
            )
            self._storage.append_inventory(record)
            logger.info("Plugin %s completed in %.1fms", plugin_name, duration_ms)
        except Exception as e:
            duration_ms = (time.monotonic() - start_mono) * 1000.0
            logger.error("Plugin %s failed: %s", plugin_name, e)
            self._storage.append_plugin_record(
                type("PluginRecord", (), {
                    "plugin_name": plugin_name,
                    "status": "error",
                    "error": str(e),
                    "started_at": started,
                    "finished_at": datetime.now(UTC).isoformat(),
                    "duration_ms": duration_ms,
                    "meta": {},
                })()
            )

    # ------------------------------------------------------------------ #
    # Config application
    # ------------------------------------------------------------------ #

    def _apply_pulled_manifest(self) -> None:
        """Apply the latest saved config manifest to plugins and remote manager."""
        try:
            manifest = self._storage.get_manifest()
        except Exception as e:
            logger.warning("Failed to load pulled manifest: %s", e)
            return

        if manifest is None:
            return

        remote_targets = list(getattr(manifest, "remote_targets", None) or [])
        integration_profiles = list(getattr(manifest, "integration_profiles", None) or [])

        logger.info(
            "Applying pulled config manifest: %d targets, %d profiles",
            len(remote_targets),
            len(integration_profiles),
        )

        self._remote_manager.update_targets(remote_targets)

        for plugin in self._plugin_manager._plugins.values():
            if not hasattr(plugin, "_context"):
                continue
            plugin._context["remote_targets"] = remote_targets
            plugin._context["integration_profiles"] = integration_profiles
            plugin._context["remote_manager"] = self._remote_manager
            if hasattr(plugin, "reinitialize"):
                try:
                    plugin.reinitialize()
                except Exception as e:
                    logger.debug("Plugin reinitialize skipped: %s", e)
