"""
System Metrics Service

Sprint:
1.0.1 - Live System Metrics
"""

from __future__ import annotations

import platform
import socket
import time

import psutil


class SystemService:
    """Provides live system metrics."""

    @staticmethod
    def get_metrics() -> dict:
        boot_time = psutil.boot_time()

        uptime_seconds = int(time.time() - boot_time)

        memory = psutil.virtual_memory()

        disk = psutil.disk_usage("/")

        return {
            "hostname": socket.gethostname(),
            "operating_system": platform.platform(),
            "cpu_percent": psutil.cpu_percent(interval=0.2),
            "memory_percent": round(memory.percent, 1),
            "disk_percent": round(disk.percent, 1),
            "uptime_seconds": uptime_seconds,
        }


system_service = SystemService()
