"""Mission Control Edge Agent - Core orchestrator.

Ties together storage, plugins, sync, and remote targets into a single
offline-first edge collector loop.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

from agent import __version__
from agent.config import AgentSettings
from agent.plugin import PluginManager
from agent.remote import RemoteManager
from agent.storage import EdgeStorage, HeartbeatRecord, InventoryRecord, StorageConfig
from agent.sync import EdgeSync

logger = logging.getLogger("mc-agent")


def _collect_health_metrics() -> dict[str, float]:
    """Best-effort local health metrics for heartbeat payloads."""
    try:
        import psutil

        boot_time = psutil.boot_time()
        uptime_hours = max(0.0, (time.time() - boot_time) / 3600.0)
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "uptime_hours": uptime_hours,
        }
    except Exception as e:  # pragma: no cover - platform dependent
        logger.debug("Health metrics unavailable: %s", e)
        return {}


def _filter_targets_for_plugin(remote_targets: list[dict[str, Any]], plugin_name: str) -> list[dict[str, Any]]:
    """Filter remote targets to only those allowed for the given plugin."""
    allowed = []
    for target in remote_targets:
        target_plugins = (target.get("target_plugins") or "").strip()
        if not target_plugins:
            allowed.append(target)
            continue
        plugins = {p.strip() for p in target_plugins.split(",") if p.strip()}
        if plugin_name in plugins:
            allowed.append(target)
    return allowed

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

        # Server-selected plugins (None until first config pull = permissive)
        self._enabled_plugins: set[str] | None = None

    async def start(self) -> None:
        """Start the edge agent."""
        logger.info("Mission Control Edge Agent starting")
        logger.info(
            "DEBUG server=%s agent_id=%s api_key_prefix=%s",
            self.config.server_url,
            self._agent_id,
            (self.config.api_key or "")[:12],
        )
        logger.info("Data dir: %s", self.config.data_dir)
        logger.info(
            "Server: %s | SSL verify: %s",
            self.config.server_url,
            self.config.verify_ssl,
        )

        self._running = True

        # Initialize plugins with a real RemoteManager so relay can work
        # even before the first successful config pull.
        await self._plugin_manager.discover_plugins()
        await self._plugin_manager.initialize_plugins(
            context={
                "agent_id": self._agent_id,
                "remote_manager": self._remote_manager,
                "integration_profiles": [],
                "remote_targets": [],
            }
        )

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
            self._command_loop(),
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
                        if (
                            name == "bundle"
                            and result.success
                            and getattr(result, "restart_requested", False)
                        ):
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

    def _plugin_enabled(self, name: str) -> bool:
        """True if the server enables this plugin (permissive before first pull)."""
        return self._enabled_plugins is None or name in self._enabled_plugins

    async def _heartbeat_loop(self) -> None:
        """Local heartbeat logging."""
        interval = max(10, self.config.heartbeat_interval or 60)
        while self._running:
            try:
                start = time.monotonic()
                active_plugins = ",".join(
                    p
                    for p in self._plugin_manager.get_active_plugins().split(",")
                    if p and self._plugin_enabled(p)
                )
                metrics = _collect_health_metrics()
                cpu = metrics.get("cpu_percent")
                mem = metrics.get("memory_percent")
                disk = metrics.get("disk_percent")
                health = "healthy"
                if cpu is not None and (cpu > 90 or (mem is not None and mem > 90)):
                    health = "warning"
                record = HeartbeatRecord(
                    agent_id=self._agent_id or 0,
                    status="online",
                    latency_ms=(time.monotonic() - start) * 1000.0,
                    pushed_at=datetime.now(UTC).isoformat(),
                    active_plugins=active_plugins,
                    health=health,
                    cpu_percent=cpu,
                    memory_percent=mem,
                    disk_percent=disk,
                    agent_version=__version__,
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
    # Command loop
    # ------------------------------------------------------------------ #

    async def _command_loop(self) -> None:
        """Poll for pending commands and execute them via the command executor."""
        from agent.executor import CommandExecutor

        executor = CommandExecutor(timeout=120)
        interval = max(5, min(self.config.heartbeat_interval or 10, 15))
        while self._running:
            try:
                if self._sync:
                    commands = self._sync.pull_commands()
                    for cmd in commands:
                        command_id = cmd.get("id")
                        if command_id is None:
                            continue
                        await self._execute_pulled_command(executor, cmd)
            except Exception as e:
                logger.error("Command loop error: %s", e)
            await asyncio.sleep(interval)

    async def _execute_pulled_command(self, executor, cmd: dict) -> None:
        """Execute one pulled command and push its result."""
        import json as _json
        import time as _time

        command_id = cmd.get("id")
        command = cmd.get("command") or ""
        command_type = cmd.get("command_type") or "execute"
        timeout = cmd.get("timeout") or 120
        file_path = cmd.get("file_path")
        file_name = cmd.get("file_name")
        file_content_b64 = cmd.get("file_content_b64")
        logger.info("Executing edge command %s (type=%s)", command_id, command_type)
        start = _time.monotonic()
        if command_type == "console_start":
            self._handle_console_start(command)
            return
        try:
            if command_type == "remote_execute":
                result = await self._execute_remote_execute(
                    command, timeout
                )
            else:
                result = await executor.execute(
                    command=command,
                    command_type=command_type,
                    timeout=timeout,
                    file_path=file_path,
                    file_name=file_name,
                    file_content_b64=file_content_b64,
                )
        except Exception as e:
            result = {
                "success": False,
                "error_message": str(e),
                "exit_code": -1,
            }
        result["duration_ms"] = int((_time.monotonic() - start) * 1000)

        # AD management ops: refresh the AD inventory and push it BEFORE
        # reporting success, so the server's user/group views reflect the
        # change the moment the UI is told the command succeeded.
        if command_type == "remote_execute" and result.get("success"):
            try:
                payload = (
                    _json.loads(command)
                    if isinstance(command, str) and command.startswith("{")
                    else {}
                )
            except ValueError:
                payload = {}
            if payload.get("namespace") == "active_directory":
                try:
                    await self._run_single_plugin("active_directory")
                    if self._sync:
                        self._sync.push_inventory()
                except Exception as e:
                    logger.error(
                        "Post-command inventory refresh failed: %s", e
                    )

        if self._sync:
            self._sync.push_command_result(command_id, result)
        if command_type == "vm_action":
            try:
                await self._run_single_plugin("hyperv")
                if self._sync:
                    self._sync.push_inventory()
            except Exception as e:
                logger.error("Post-action inventory refresh failed: %s", e)
        logger.info(
            "Edge command %s finished: success=%s", command_id, result.get("success")
        )

    def _handle_console_start(self, command: str) -> None:
        """Start an interactive console relay session (fire-and-forget).

        Session status is reported through the console I/O endpoint, not the
        command-result channel.
        """
        import json as _json

        from agent.console_manager import ConsoleRelay

        if getattr(self, "_console_relay", None) is None:
            self._console_relay = ConsoleRelay()

        try:
            payload = _json.loads(command) if command.startswith("{") else {}
        except _json.JSONDecodeError:
            payload = {}
        session_id = str(payload.get("session_id") or "")
        hostname = str(payload.get("hostname") or "")
        if not session_id or not hostname:
            logger.warning("console_start missing session_id/hostname")
            return

        targets = list(getattr(self._remote_manager, "_targets", {}).values())
        self._console_relay.start_session(
            session_id=session_id,
            agent_id=self._agent_id or 0,
            base_url=self.config.server_url,
            api_key=self.config.api_key or "",
            verify_ssl=self.config.verify_ssl,
            targets=targets,
            hostname=hostname,
            width=int(payload.get("width") or 120),
            height=int(payload.get("height") or 40),
        )
        logger.info("Console relay %s starting for %s", session_id, hostname)

    async def _execute_remote_execute(
        self, command: str, timeout: int
    ) -> dict[str, Any]:
        """Handle a remote_execute command (veeam relay or generic SSH target).

        Mirrors the legacy agent's remote_execute handler: JSON payloads with a
        ``namespace`` are dispatched to the matching plugin; otherwise the
        command runs on the SSH target via the remote manager.
        """
        import json as _json

        target_id = None
        command_text = command
        namespace = None
        op = None
        params: dict = {}
        if command.startswith("{"):
            try:
                payload = _json.loads(command)
                namespace = payload.get("namespace")
                op = payload.get("op")
                params = payload.get("params") or {}
                target_id = payload.get("target_id")
                if namespace is None:
                    command_text = payload.get("command", "")
            except (_json.JSONDecodeError, AttributeError):
                pass

        if namespace in ("veeam", "active_directory"):
            plugin_result = await self._plugin_manager.execute_plugin_command(
                namespace, op or "", params
            )
            ok = bool(plugin_result.get("success", False))
            return {
                "success": ok,
                "stdout": _json.dumps(plugin_result),
                "stderr": plugin_result.get("error")
                or plugin_result.get("stderr")
                or "",
                "exit_code": 0 if ok else 1,
            }

        if target_id is None:
            return {
                "success": False,
                "stdout": "",
                "stderr": "No target_id specified for remote_execute",
                "exit_code": -1,
            }

        return await self._remote_manager.execute_on_target(
            target_id=target_id,
            command=command_text,
            timeout=timeout,
        )

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
        plugins = [
            name
            for name in self._plugin_manager._plugins
            if self._plugin_enabled(name)
        ]
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
                type(
                    "PluginRecord",
                    (),
                    {
                        "plugin_name": plugin_name,
                        "status": "error",
                        "error": str(e),
                        "started_at": started,
                        "finished_at": datetime.now(UTC).isoformat(),
                        "duration_ms": duration_ms,
                        "meta": {},
                    },
                )()
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
        integration_profiles = list(
            getattr(manifest, "integration_profiles", None) or []
        )

        enabled = (manifest.config or {}).get("enabled_plugins")
        if enabled is not None:
            self._enabled_plugins = {
                str(p).strip() for p in enabled if str(p).strip()
            }
            logger.info(
                "Server-enabled plugins: %s",
                ",".join(sorted(self._enabled_plugins)) or "(none)",
            )

        logger.info(
            "Applying pulled config manifest: %d targets, %d profiles",
            len(remote_targets),
            len(integration_profiles),
        )

        self._remote_manager.update_targets(remote_targets)

        for plugin in self._plugin_manager._plugins.values():
            if not hasattr(plugin, "_context"):
                continue
            plugin._context = {
                **plugin._context,
                "remote_targets": _filter_targets_for_plugin(
                    remote_targets, plugin.name
                ),
                "integration_profiles": integration_profiles,
                "remote_manager": self._remote_manager,
            }
            if hasattr(plugin, "reinitialize"):
                try:
                    plugin.reinitialize()
                except Exception as e:
                    logger.debug("Plugin reinitialize skipped: %s", e)
