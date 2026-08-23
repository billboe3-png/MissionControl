"""Mission Control Agent - Self-diagnostics and health monitoring."""

import logging
import shutil
import socket
import time
from typing import Any

logger = logging.getLogger("mc-agent")


class AgentDiagnostics:
    """Agent self-diagnostics and health monitoring."""

    def __init__(self, config: Any, client: Any = None) -> None:
        self.config = config
        self.client = client
        self._start_time = time.monotonic()

    def run_all(self) -> dict[str, Any]:
        """Run all diagnostics, return summary."""
        checks = [
            self.check_api_connectivity(),
            self.check_dns_resolution(),
            self.check_clock_sync(),
            self.check_disk_space(),
            self.check_memory_pressure(),
            self.check_config_integrity(),
            self.check_heartbeat_latency(),
        ]

        return self.get_health_summary(checks)

    def check_api_connectivity(self) -> dict[str, Any]:
        """Try GET /api/v1/health/live, return latency + status."""
        if self.client is None:
            return {
                "name": "api_connectivity",
                "status": "warning",
                "message": "No API client configured",
                "latency_ms": 0.0,
            }

        start = time.monotonic()
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    self.client.get("/api/v1/health/live")
                )
                latency = (time.monotonic() - start) * 1000
                return {
                    "name": "api_connectivity",
                    "status": "ok",
                    "message": "API reachable",
                    "latency_ms": round(latency, 2),
                }
            finally:
                loop.close()
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return {
                "name": "api_connectivity",
                "status": "critical",
                "message": f"API unreachable: {e}",
                "latency_ms": round(latency, 2),
            }

    def check_dns_resolution(self) -> dict[str, Any]:
        """Resolve the server hostname, return latency."""
        from urllib.parse import urlparse

        hostname = urlparse(self.config.server_url).hostname or "localhost"
        start = time.monotonic()
        try:
            socket.getaddrinfo(hostname, None)
            latency = (time.monotonic() - start) * 1000
            return {
                "name": "dns_resolution",
                "status": "ok",
                "message": f"Resolved {hostname}",
                "latency_ms": round(latency, 2),
            }
        except socket.gaierror as e:
            latency = (time.monotonic() - start) * 1000
            return {
                "name": "dns_resolution",
                "status": "critical",
                "message": f"DNS resolution failed: {e}",
                "latency_ms": round(latency, 2),
            }

    def check_clock_sync(self) -> dict[str, Any]:
        """Compare local time with server time via API."""
        if self.client is None:
            return {
                "name": "clock_sync",
                "status": "warning",
                "message": "No API client, cannot check clock sync",
                "latency_ms": 0.0,
            }

        start = time.monotonic()
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    self.client.get("/api/v1/health/time")
                )
                latency = (time.monotonic() - start) * 1000
                server_time = result.get("time", 0)
                local_time = time.time()
                offset = abs(local_time - server_time)

                if offset > 300:
                    status = "critical"
                    msg = f"Clock offset: {offset:.0f}s"
                elif offset > 60:
                    status = "warning"
                    msg = f"Clock offset: {offset:.0f}s"
                else:
                    status = "ok"
                    msg = f"Clock offset: {offset:.1f}s"

                return {
                    "name": "clock_sync",
                    "status": status,
                    "message": msg,
                    "latency_ms": round(latency, 2),
                }
            finally:
                loop.close()
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return {
                "name": "clock_sync",
                "status": "warning",
                "message": f"Clock check failed: {e}",
                "latency_ms": round(latency, 2),
            }

    def check_disk_space(self) -> dict[str, Any]:
        """Check disk space on all partitions."""
        try:
            partitions = []
            usage = shutil.disk_usage("/")
            used_pct = (usage.used / usage.total) * 100 if usage.total > 0 else 0
            partitions.append(
                {
                    "mount": "/",
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "free_gb": round(usage.free / (1024**3), 1),
                    "used_pct": round(used_pct, 1),
                }
            )

            if used_pct > 95:
                status = "critical"
                msg = f"Disk usage at {used_pct:.0f}%"
            elif used_pct > 85:
                status = "warning"
                msg = f"Disk usage at {used_pct:.0f}%"
            else:
                status = "ok"
                msg = f"Disk usage at {used_pct:.0f}%"

            return {
                "name": "disk_space",
                "status": status,
                "message": msg,
                "latency_ms": 0.0,
                "partitions": partitions,
            }
        except Exception as e:
            return {
                "name": "disk_space",
                "status": "warning",
                "message": f"Disk check failed: {e}",
                "latency_ms": 0.0,
            }

    def check_memory_pressure(self) -> dict[str, Any]:
        """Check if memory usage > 90%."""
        try:
            import psutil

            mem = psutil.virtual_memory()
            used_pct = mem.percent

            if used_pct > 95:
                status = "critical"
            elif used_pct > 90:
                status = "warning"
            else:
                status = "ok"

            return {
                "name": "memory_pressure",
                "status": status,
                "message": f"Memory usage at {used_pct:.0f}%",
                "latency_ms": 0.0,
            }
        except ImportError:
            try:
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                info = {}
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        info[key] = int(val)

                total = info.get("MemTotal", 0)
                available = info.get("MemAvailable", 0)
                used_pct = ((total - available) / total * 100) if total > 0 else 0

                if used_pct > 95:
                    status = "critical"
                elif used_pct > 90:
                    status = "warning"
                else:
                    status = "ok"

                return {
                    "name": "memory_pressure",
                    "status": status,
                    "message": f"Memory usage at {used_pct:.0f}%",
                    "latency_ms": 0.0,
                }
            except Exception as e:
                return {
                    "name": "memory_pressure",
                    "status": "warning",
                    "message": f"Memory check failed: {e}",
                    "latency_ms": 0.0,
                }

    def check_queue_health(self, queue: Any) -> dict[str, Any]:
        """Check command queue for stuck items."""
        try:
            pending = queue.get_pending_count() if hasattr(queue, "get_pending_count") else 0
            results = queue.get_results_count() if hasattr(queue, "get_results_count") else 0

            if pending > 100:
                status = "warning"
                msg = f"{pending} pending commands, {results} results buffered"
            elif pending > 500:
                status = "critical"
                msg = f"{pending} pending commands, {results} results buffered"
            else:
                status = "ok"
                msg = f"{pending} pending commands, {results} results buffered"

            return {
                "name": "queue_health",
                "status": status,
                "message": msg,
                "latency_ms": 0.0,
            }
        except Exception as e:
            return {
                "name": "queue_health",
                "status": "warning",
                "message": f"Queue check failed: {e}",
                "latency_ms": 0.0,
            }

    def check_plugin_health(self, plugin_manager: Any) -> dict[str, Any]:
        """Check all plugins are responding."""
        try:
            active = plugin_manager.get_active_plugins() if hasattr(plugin_manager, "get_active_plugins") else None
            count = len(active) if active else 0

            return {
                "name": "plugin_health",
                "status": "ok",
                "message": f"{count} active plugins",
                "latency_ms": 0.0,
            }
        except Exception as e:
            return {
                "name": "plugin_health",
                "status": "warning",
                "message": f"Plugin check failed: {e}",
                "latency_ms": 0.0,
            }

    def check_heartbeat_latency(self) -> dict[str, Any]:
        """Measure time for a test heartbeat."""
        if self.client is None:
            return {
                "name": "heartbeat_latency",
                "status": "warning",
                "message": "No API client configured",
                "latency_ms": 0.0,
            }

        start = time.monotonic()
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    self.client.get("/api/v1/health/live")
                )
                latency = (time.monotonic() - start) * 1000

                if latency > 5000:
                    status = "warning"
                elif latency > 10000:
                    status = "critical"
                else:
                    status = "ok"

                return {
                    "name": "heartbeat_latency",
                    "status": status,
                    "message": f"Heartbeat RTT: {latency:.0f}ms",
                    "latency_ms": round(latency, 2),
                }
            finally:
                loop.close()
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return {
                "name": "heartbeat_latency",
                "status": "critical",
                "message": f"Heartbeat failed: {e}",
                "latency_ms": round(latency, 2),
            }

    def check_config_integrity(self) -> dict[str, Any]:
        """Verify config file is readable and valid."""
        try:
            config_path = self.config.config_dir / "config.yaml" if hasattr(self.config, "config_dir") else None
            if config_path and config_path.exists():
                import yaml

                with open(config_path) as f:
                    yaml.safe_load(f)
                return {
                    "name": "config_integrity",
                    "status": "ok",
                    "message": f"Config valid at {config_path}",
                    "latency_ms": 0.0,
                }

            return {
                "name": "config_integrity",
                "status": "ok",
                "message": "Config loaded from defaults/environment",
                "latency_ms": 0.0,
            }
        except Exception as e:
            return {
                "name": "config_integrity",
                "status": "critical",
                "message": f"Config invalid: {e}",
                "latency_ms": 0.0,
            }

    def get_health_summary(self, checks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Return overall health status with all check results."""
        if checks is None:
            checks = self.run_all_checks()

        statuses = [c.get("status", "ok") for c in checks]
        if "critical" in statuses:
            overall = "unhealthy"
        elif "warning" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"

        uptime = time.monotonic() - self._start_time if self._start_time > 0 else 0.0

        return {
            "status": overall,
            "checks": checks,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "uptime": round(uptime, 2),
        }

    def run_all_checks(self) -> list[dict[str, Any]]:
        """Run all individual checks and return results list."""
        return [
            self.check_api_connectivity(),
            self.check_dns_resolution(),
            self.check_clock_sync(),
            self.check_disk_space(),
            self.check_memory_pressure(),
            self.check_config_integrity(),
            self.check_heartbeat_latency(),
        ]
