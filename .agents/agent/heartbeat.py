"""Mission Control Agent - Heartbeat system."""

import logging
import platform
import socket
import time

import psutil

from agent.client import AgentClient
from agent.config import AgentSettings

logger = logging.getLogger("mc-agent")

HEARTBEAT_MODES = {
    "normal": 30,
    "high_frequency": 10,
    "maintenance": 120,
    "low_bandwidth": 300,
}


class HeartbeatConfig:
    """Configurable heartbeat interval settings."""

    def __init__(self, mode: str = "normal"):
        self.modes = dict(HEARTBEAT_MODES)
        self.current_mode = mode if mode in self.modes else "normal"

    @property
    def interval(self) -> int:
        """Get current heartbeat interval in seconds."""
        return self.modes[self.current_mode]

    def set_mode(self, mode: str) -> None:
        """Switch heartbeat mode."""
        if mode not in self.modes:
            logger.warning("Unknown heartbeat mode '%s', keeping '%s'", mode, self.current_mode)
            return
        self.current_mode = mode
        logger.info("Heartbeat mode set to '%s' (interval=%ds)", mode, self.modes[mode])

    def register_mode(self, name: str, interval: int) -> None:
        """Register a custom heartbeat mode."""
        self.modes[name] = interval


class HeartbeatManager:
    """Manages periodic heartbeats to Mission Control server."""

    def __init__(self, client: AgentClient, config: AgentSettings):
        self.client = client
        self.config = config
        self._running = False
        self._hb_config = HeartbeatConfig()

    @property
    def heartbeat_config(self) -> HeartbeatConfig:
        return self._hb_config

    def set_mode(self, mode: str) -> None:
        """Switch heartbeat mode."""
        self._hb_config.set_mode(mode)

    @staticmethod
    def _collect_system_metrics() -> dict:
        """Collect full system metrics for heartbeat payload."""
        metrics: dict = {}

        try:
            metrics["cpu_percent"] = psutil.cpu_percent(interval=0)
        except Exception:
            metrics["cpu_percent"] = None

        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        metrics["cpu_temperature"] = entries[0].current
                        break
                else:
                    metrics["cpu_temperature"] = None
            else:
                metrics["cpu_temperature"] = None
        except (AttributeError, Exception):
            metrics["cpu_temperature"] = None

        try:
            mem = psutil.virtual_memory()
            metrics["memory_percent"] = mem.percent
        except Exception:
            metrics["memory_percent"] = None

        try:
            swap = psutil.swap_memory()
            metrics["swap_percent"] = swap.percent
        except Exception:
            metrics["swap_percent"] = None

        try:
            if platform.system() != "Windows":
                metrics["disk_percent"] = psutil.disk_usage("/").percent
            else:
                metrics["disk_percent"] = psutil.disk_usage("C:\\").percent
        except Exception:
            metrics["disk_percent"] = None

        try:
            net = psutil.net_io_counters()
            metrics["network_throughput"] = {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
            }
        except Exception:
            metrics["network_throughput"] = None

        try:
            boot = psutil.boot_time()
            metrics["uptime_seconds"] = int(time.time() - boot) if boot else 0
        except Exception:
            metrics["uptime_seconds"] = 0

        return metrics

    @staticmethod
    def _collect_os_info() -> dict:
        """Collect OS information."""
        info = {
            "hostname": socket.gethostname(),
            "os_version": platform.platform(),
            "kernel_version": platform.release(),
            "architecture": platform.machine(),
        }

        try:
            if platform.system() == "Linux":
                import os
                if os.path.exists("/etc/os-release"):
                    with open("/etc/os-release") as f:
                        for line in f:
                            if line.startswith("PRETTY_NAME="):
                                info["os_version"] = line.split("=", 1)[1].strip().strip('"')
                                break
        except Exception:
            pass

        return info

    @staticmethod
    def _collect_runtime_status() -> dict:
        """Collect runtime status information."""
        return {
            "pending_commands": 0,
            "running_commands": 0,
            "automation_status": "active",
            "health_status": "healthy",
        }

    @staticmethod
    def _collect_inventory_summary() -> dict:
        """Collect inventory summary information."""
        return {
            "inventory_version": 0,
            "installed_plugins": "",
            "agent_version": None,
            "pending_updates": 0,
        }

    @staticmethod
    def _collect_config_status() -> dict:
        """Collect configuration status."""
        return {
            "heartbeat_interval": HEARTBEAT_MODES.get("normal", 30),
            "maintenance_mode": False,
        }

    async def send_heartbeat(
        self,
        agent_id: int,
        health: str = "healthy",
        cpu_percent: float | None = None,
        memory_percent: float | None = None,
        disk_percent: float | None = None,
        agent_version: str | None = None,
        active_plugins: str | None = None,
        pending_commands: int | None = None,
        running_commands: int | None = None,
        automation_status: str | None = None,
        inventory_version: int | None = None,
        installed_plugins: str | None = None,
        pending_updates: int | None = None,
        heartbeat_interval: int | None = None,
        maintenance_mode: bool | None = None,
    ) -> dict:
        """Send a single heartbeat and receive pending commands."""
        system_metrics = self._collect_system_metrics()
        os_info = self._collect_os_info()
        runtime = self._collect_runtime_status()
        inventory = self._collect_inventory_summary()
        config_status = self._collect_config_status()

        payload = {
            "agent_id": agent_id,
            "health": health,
            "cpu_percent": cpu_percent if cpu_percent is not None else system_metrics.get("cpu_percent"),
            "cpu_temperature": system_metrics.get("cpu_temperature"),
            "memory_percent": memory_percent if memory_percent is not None else system_metrics.get("memory_percent"),
            "swap_percent": system_metrics.get("swap_percent"),
            "disk_percent": disk_percent if disk_percent is not None else system_metrics.get("disk_percent"),
            "network_throughput": system_metrics.get("network_throughput"),
            "uptime_seconds": system_metrics.get("uptime_seconds"),
            "hostname": os_info.get("hostname"),
            "os_version": os_info.get("os_version"),
            "kernel_version": os_info.get("kernel_version"),
            "architecture": os_info.get("architecture"),
            "pending_commands": pending_commands if pending_commands is not None else runtime["pending_commands"],
            "running_commands": running_commands if running_commands is not None else runtime["running_commands"],
            "automation_status": automation_status or runtime["automation_status"],
            "health_status": health,
            "inventory_version": inventory_version if inventory_version is not None else inventory["inventory_version"],
            "installed_plugins": installed_plugins if installed_plugins is not None else inventory["installed_plugins"],
            "agent_version": agent_version or inventory.get("agent_version"),
            "pending_updates": pending_updates if pending_updates is not None else inventory["pending_updates"],
            "heartbeat_interval": heartbeat_interval if heartbeat_interval is not None else self._hb_config.interval,
            "maintenance_mode": maintenance_mode if maintenance_mode is not None else config_status["maintenance_mode"],
        }

        if active_plugins is not None:
            payload["active_plugins"] = active_plugins

        try:
            result = await self.client.post(
                "/api/v1/agents/heartbeat", payload
            )
            logger.debug(
                "Heartbeat sent for agent %d, %d pending commands",
                agent_id,
                len(result.get("commands") or []),
            )
            return result
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)
            raise
