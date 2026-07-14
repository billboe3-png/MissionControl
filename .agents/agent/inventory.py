"""Mission Control Agent - Inventory collection."""

import asyncio
import json
import logging
import platform
import socket
from typing import Any

import psutil

logger = logging.getLogger("mc-agent")


class InventoryCollector:
    """Collects system inventory data from the local machine."""

    def collect(self) -> dict[str, Any]:
        """Gather comprehensive system inventory."""
        try:
            inventory = {
                "system": self._collect_system(),
                "cpu": self._collect_cpu(),
                "memory": self._collect_memory(),
                "disks": self._collect_disks(),
                "network": self._collect_network(),
                "services": self._collect_services(),
                "docker": self._collect_docker(),
                "software": self._collect_software(),
            }
            return inventory
        except Exception as e:
            logger.error("Inventory collection failed: %s", e)
            return {"error": str(e)}

    def collect_health_metrics(self) -> dict[str, float]:
        """Collect current health metrics (CPU, memory, disk)."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent
                if platform.system() != "Windows"
                else psutil.disk_usage("C:\\").percent,
            }
        except Exception:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
            }

    def _collect_system(self) -> dict[str, Any]:
        """Collect basic system information."""
        boot = psutil.boot_time()
        uptime = psutil.time.time() - boot if boot else 0
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "python_version": platform.python_version(),
            "uptime_seconds": int(uptime),
            "boot_time": boot,
        }

    def _collect_cpu(self) -> dict[str, Any]:
        """Collect CPU information."""
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.5),
            "freq": self._get_cpu_freq(),
            "load_average": self._get_load_average(),
        }

    def _get_cpu_freq(self) -> dict[str, Any] | None:
        try:
            freq = psutil.cpu_freq()
            if freq:
                return {
                    "current": freq.current,
                    "min": freq.min,
                    "max": freq.max,
                }
        except Exception:
            pass
        return None

    def _get_load_average(self) -> list[float] | None:
        try:
            if hasattr(os, "getloadavg"):
                return list(os.getloadavg())
        except Exception:
            pass
        return None

    def _collect_memory(self) -> dict[str, Any]:
        """Collect memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent,
        }

    def _collect_disks(self) -> list[dict[str, Any]]:
        """Collect disk information."""
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    }
                )
            except PermissionError:
                continue
        return disks

    def _collect_network(self) -> dict[str, Any]:
        """Collect network information."""
        interfaces = {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io = psutil.net_io_counters()

        for name, addr_list in addrs.items():
            iface = {"addresses": [], "is_up": False}
            if name in stats:
                iface["is_up"] = stats[name].isup
                iface["speed"] = stats[name].speed
            for addr in addr_list:
                iface["addresses"].append(
                    {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                    }
                )
            interfaces[name] = iface

        return {
            "interfaces": interfaces,
            "io": {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
            }
            if io
            else {},
        }

    def _collect_services(self) -> list[dict[str, Any]]:
        """Collect running services/processes."""
        services = []
        try:
            for proc in psutil.process_iter(
                ["pid", "name", "status", "cpu_percent", "memory_percent"]
            ):
                info = proc.info
                if info["status"] == psutil.STATUS_RUNNING:
                    services.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"],
                            "status": info["status"],
                            "cpu_percent": info.get("cpu_percent"),
                            "memory_percent": info.get("memory_percent"),
                        }
                    )
        except Exception as e:
            logger.warning("Service collection failed: %s", e)
        return services[:100]

    def _collect_docker(self) -> dict[str, Any]:
        """Collect Docker information if available."""
        try:
            import docker

            client = docker.from_env()
            info = client.info()
            containers = client.containers.list(all=True)
            return {
                "available": True,
                "version": info.get("ServerVersion", "unknown"),
                "container_count": len(containers),
                "containers": [
                    {
                        "id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": str(c.image.tags)
                        if c.image.tags
                        else str(c.image.id)[:12],
                    }
                    for c in containers[:50]
                ],
            }
        except Exception:
            return {"available": False}

    def _collect_software(self) -> dict[str, Any]:
        """Collect installed software/packages."""
        system = platform.system()
        result = {"system": system, "packages": []}

        if system == "Linux":
            result["packages"] = self._get_linux_packages()
        elif system == "Windows":
            result["packages"] = self._get_windows_packages()
        elif system == "Darwin":
            result["packages"] = self._get_macos_packages()

        return result

    def _get_linux_packages(self) -> list[str]:
        """Get installed packages on Linux."""
        try:
            import subprocess

            out = subprocess.check_output(
                ["dpkg", "--get-selections"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode()
            return [
                line.split()[0]
                for line in out.strip().split("\n")
                if line.strip() and "install" in line
            ][:200]
        except Exception:
            pass

        try:
            import subprocess

            out = subprocess.check_output(
                ["rpm", "-qa", "--queryformat", "%{NAME}\n"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode()
            return out.strip().split("\n")[:200]
        except Exception:
            pass

        return []

    def _get_windows_packages(self) -> list[str]:
        """Get installed packages on Windows."""
        try:
            import subprocess

            out = subprocess.check_output(
                [
                    "powershell",
                    "-Command",
                    "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object -ExpandProperty DisplayName",
                ],
                timeout=30,
                stderr=subprocess.DEVNULL,
            ).decode()
            return [
                p.strip()
                for p in out.strip().split("\n")
                if p.strip()
            ][:200]
        except Exception:
            return []

    def _get_macos_packages(self) -> list[str]:
        """Get installed packages on macOS."""
        try:
            import subprocess

            out = subprocess.check_output(
                ["brew", "list", "--formula"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode()
            return out.strip().split("\n")[:200]
        except Exception:
            return []
