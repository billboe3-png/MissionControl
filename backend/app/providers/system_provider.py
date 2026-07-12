"""
Mission Control System Provider

Returns live OS and hardware metrics using psutil.
No shell commands. No subprocess calls.
"""

import logging
import platform

import psutil

logger = logging.getLogger(__name__)


class SystemProvider:
    """Return live system metrics from the host machine."""

    def get_system_info(self) -> dict:
        """Return hostname, OS, platform, CPU, memory, disk, and uptime."""
        boot_time = psutil.boot_time()
        uptime_seconds = psutil.time.time() - boot_time

        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=True)

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "platform": platform.platform(),
            "cpu_count": cpu_count,
            "cpu_percent": round(cpu_percent, 1),
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": round(memory.percent, 1),
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": round(disk.percent, 1),
            "uptime_seconds": int(uptime_seconds),
            "boot_time": int(boot_time),
        }


system_provider = SystemProvider()
