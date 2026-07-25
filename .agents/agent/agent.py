"""Mission Control Agent - Main agent orchestrator."""

import asyncio
import json
import logging
import platform
import socket
import time
from typing import Any

from agent import __version__
from agent.client import AgentClient
from agent.command_queue import CommandQueue
from agent.config import AgentSettings
from agent.executor import CommandExecutor
from agent.heartbeat import HeartbeatManager
from agent.inventory import InventoryCollector
from agent.plugin import PluginManager
from agent.registration import RegistrationManager
from agent.remote import RemoteManager
from agent.updater import AgentUpdater

logger = logging.getLogger("mc-agent")


class MissionControlAgent:
    """Main agent class that orchestrates all agent components."""

    def __init__(self, config: AgentSettings):
        self.config = config
        self.client = AgentClient(
            server_url=config.server_url,
            api_key=config.api_key,
            verify_ssl=config.verify_ssl,
        )
        self.heartbeat_manager = HeartbeatManager(
            self.client, config
        )
        self.registration_manager = RegistrationManager(
            self.client, config
        )
        self.inventory_collector = InventoryCollector()
        self.command_executor = CommandExecutor(
            timeout=config.command_timeout
        )
        self.command_queue = CommandQueue(
            data_dir=config.data_dir,
            max_size=config.offline_buffer_max,
        )
        self.plugin_manager = PluginManager()
        self.remote_manager = RemoteManager()
        self.updater = AgentUpdater(self.client, __version__)
        self._running = False
        self._remote_inventory_cache: dict[str, Any] = {}
        self._agent_id: int | None = config.agent_id
        self._last_inventory_time: float = 0
        self._last_update_check: float = 0

    async def start(self) -> None:
        """Start the agent."""
        logger.info(
            "Mission Control Agent v%s starting", __version__
        )
        logger.info(
            "Server: %s | SSL: %s",
            self.config.server_url,
            self.config.verify_ssl,
        )

        self._running = True

        if not self._agent_id or not self.config.api_key:
            await self._register()

        await self._discover_plugins()

        await asyncio.gather(
            self._heartbeat_loop(),
            self._inventory_loop(),
            self._remote_inventory_loop(),
            self._result_reporting_loop(),
        )

    async def stop(self) -> None:
        """Stop the agent gracefully."""
        logger.info("Agent stopping...")
        self._running = False
        await self.plugin_manager.shutdown_all()
        await self.client.close()

    async def _register(self) -> None:
        """Register this agent with Mission Control."""
        hostname = socket.gethostname()
        os_name = platform.system()
        os_version = platform.platform()
        ip = self._get_ip_address()

        result = await self.registration_manager.register(
            hostname=hostname,
            os_name=os_name,
            os_version=os_version,
            ip_address=ip,
            agent_version=__version__,
        )

        self._agent_id = result["agent_id"]
        self.config.api_key = result["api_key"]
        self.config.agent_id = result["agent_id"]
        self.client.set_api_key(result["api_key"])

        logger.info(
            "Agent registered: ID=%d, key=%s...",
            self._agent_id,
            result["api_key"][:12],
        )

    async def _discover_plugins(self) -> None:
        """Discover and initialize plugins."""
        discovered = await self.plugin_manager.discover_plugins()
        if discovered:
            logger.info(
                "Discovered %d plugins: %s",
                len(discovered),
                ", ".join(discovered),
            )
            await self.plugin_manager.initialize_plugins(
                {"agent_id": self._agent_id}
            )

    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                health_metrics = (
                    self.inventory_collector.collect_health_metrics()
                )
                active_plugins = (
                    self.plugin_manager.get_active_plugins()
                )

                response = await self.heartbeat_manager.send_heartbeat(
                    agent_id=self._agent_id,
                    health=self._determine_health(health_metrics),
                    cpu_percent=health_metrics.get("cpu_percent"),
                    memory_percent=health_metrics.get(
                        "memory_percent"
                    ),
                    disk_percent=health_metrics.get("disk_percent"),
                    agent_version=__version__,
                    active_plugins=active_plugins,
                )

                remote_targets = response.get("remote_targets")
                if remote_targets:
                    self.remote_manager.update_targets(remote_targets)

                pending_commands = response.get("commands") or []
                for cmd in pending_commands:
                    await self._execute_command(cmd)

                now = time.monotonic()
                if now - self._last_update_check > 3600:
                    self._last_update_check = now
                    update = await self.updater.check_for_update()
                    if update.get("update_available"):
                        logger.info(
                            "Update available: %s -> %s",
                            update["current_version"],
                            update["latest_version"],
                        )

            except Exception as e:
                logger.warning("Heartbeat cycle failed: %s", e)

            await asyncio.sleep(self.config.heartbeat_interval)

    async def _inventory_loop(self) -> None:
        """Periodic inventory collection loop."""
        while self._running:
            try:
                await asyncio.sleep(
                    self.config.inventory_interval
                )

                if not self._running:
                    break

                inventory = self.inventory_collector.collect()
                plugin_inventory = (
                    await self.plugin_manager.collect_all_inventory()
                )
                if plugin_inventory:
                    inventory["plugins"] = plugin_inventory

                if self._remote_inventory_cache:
                    inventory["remote_targets"] = self._remote_inventory_cache

                await self.client.post(
                    f"/api/v1/agents/{self._agent_id}/inventory",
                    inventory,
                )
                logger.debug("Inventory reported to server")

            except Exception as e:
                logger.warning("Inventory cycle failed: %s", e)

    async def _result_reporting_loop(self) -> None:
        """Report buffered results when back online."""
        while self._running:
            try:
                while self.command_queue.get_results_count() > 0:
                    result = self.command_queue.dequeue_result()
                    if result:
                        await self.client.post(
                            f"/api/v1/agents/{self._agent_id}/command-result",
                            result,
                        )
                        logger.debug(
                            "Buffered result reported: cmd=%s",
                            result.get("command_id"),
                        )
            except Exception as e:
                logger.debug(
                    "Result reporting failed (will retry): %s", e
                )

            await asyncio.sleep(5)

    async def _remote_inventory_loop(self) -> None:
        """Periodic remote target inventory collection."""
        while self._running:
            try:
                await asyncio.sleep(self.config.remote_inventory_interval)
                if not self._running:
                    break
                if self.remote_manager.target_count == 0:
                    continue

                self._remote_inventory_cache = (
                    await self.remote_manager.collect_inventory()
                )
                logger.info(
                    "Remote inventory collected: %d targets",
                    len(self._remote_inventory_cache),
                )
            except Exception as e:
                logger.warning("Remote inventory cycle failed: %s", e)

    async def _execute_command(self, cmd: dict) -> None:
        """Execute a single command from the server."""
        command_id = cmd.get("id")
        logger.info(
            "Executing command %d: %s",
            command_id,
            cmd.get("command_type"),
        )

        try:
            command_type = cmd.get("command_type", "execute")

            if command_type == "remote_execute":
                target_id = cmd.get("target_id")
                command_text = cmd.get("command", "")
                if target_id is None and command_text.startswith("{"):
                    try:
                        payload = json.loads(command_text)
                        target_id = payload.get("target_id")
                        command_text = payload.get("command", "")
                    except (json.JSONDecodeError, AttributeError):
                        pass
                if target_id is None:
                    result = {
                        "success": False,
                        "stdout": "",
                        "stderr": "No target_id specified for remote_execute",
                        "exit_code": -1,
                    }
                else:
                    result = await self.remote_manager.execute_on_target(
                        target_id=target_id,
                        command=command_text,
                        timeout=cmd.get("timeout", self.config.command_timeout),
                    )
            else:
                result = await self.command_executor.execute(
                    command=cmd.get("command", ""),
                    command_type=command_type,
                    timeout=cmd.get("timeout", self.config.command_timeout),
                    file_path=cmd.get("file_path"),
                    file_name=cmd.get("file_name"),
                    file_content_b64=cmd.get("file_content_b64"),
                )

            report = {
                "command_id": command_id,
                "exit_code": result.get("exit_code"),
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr"),
                "success": result.get("success", False),
                "duration_ms": result.get("duration_ms"),
            }

            if result.get("file_content_b64"):
                report["file_content_b64"] = result[
                    "file_content_b64"
                ]

            try:
                await self.client.post(
                    f"/api/v1/agents/{self._agent_id}/command-result",
                    report,
                )
            except Exception:
                self.command_queue.queue_result(report)
                logger.info(
                    "Result buffered for command %d", command_id
                )

        except Exception as e:
            logger.error(
                "Command %d execution failed: %s", command_id, e
            )
            error_report = {
                "command_id": command_id,
                "success": False,
                "error_message": str(e),
                "exit_code": -1,
            }
            try:
                await self.client.post(
                    f"/api/v1/agents/{self._agent_id}/command-result",
                    error_report,
                )
            except Exception:
                self.command_queue.queue_result(error_report)

    def _determine_health(self, metrics: dict) -> str:
        """Determine agent health from metrics."""
        cpu = metrics.get("cpu_percent", 0)
        mem = metrics.get("memory_percent", 0)
        disk = metrics.get("disk_percent", 0)

        if cpu > 95 or mem > 95 or disk > 95:
            return "critical"
        if cpu > 85 or mem > 85 or disk > 90:
            return "warning"
        return "healthy"

    def _get_ip_address(self) -> str:
        """Get the primary IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
