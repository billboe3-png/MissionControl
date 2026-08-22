"""
Mission Control Environment Validation

Extended startup validation covering system resources,
versions, connectivity, and deployment readiness.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_PORTS = [8000, 3000, 5432, 6379]


def _result(name: str, status: str, message: str, details: str = "") -> dict:
    """Build a standardised check result."""
    return {
        "name": name,
        "status": status,
        "message": message,
        "details": details,
    }


class EnvironmentValidator:
    """Runs a suite of pre-flight checks against the host environment."""

    # ------------------------------------------------------------------ #
    # Aggregate                                                            #
    # ------------------------------------------------------------------ #

    def validate_all(self) -> list[dict]:
        """Run every individual check and return combined results."""
        results: list[dict] = []
        for method in (
            self.check_system,
            self.check_python,
            self.check_docker,
            self.check_postgres,
            self.check_redis,
            self.check_ports,
            self.check_permissions,
            self.check_tls,
            self.check_firewall,
        ):
            try:
                results.append(method())
            except Exception as exc:
                results.append(
                    _result(
                        method.__name__,
                        "critical",
                        f"Check raised an exception: {exc}",
                    )
                )
        return results

    def get_readiness_score(self) -> tuple[int, list[dict]]:
        """Return (score 0-100, list of issues).

        Each check contributes to the score:
            info     — no impact
            warning  — deducts 5 points
            critical — deducts 25 points
        """
        results = self.validate_all()
        issues = [r for r in results if r["status"] in ("warning", "critical")]

        score = 100
        for issue in issues:
            if issue["status"] == "critical":
                score -= 25
            elif issue["status"] == "warning":
                score -= 5

        return max(0, score), issues

    # ------------------------------------------------------------------ #
    # System                                                               #
    # ------------------------------------------------------------------ #

    def check_system(self) -> dict:
        """Detect CPU architecture, available RAM, and disk space."""
        arch = platform.machine()
        uname = platform.uname()

        ram_mb = self._get_ram_mb()
        disk_free_gb = self._get_disk_free_gb(".")

        details_parts = [
            f"System: {uname.system} {uname.release}",
            f"Arch: {arch}",
            f"RAM: {ram_mb} MB" if ram_mb else "RAM: unknown",
        ]
        if disk_free_gb is not None:
            details_parts.append(f"Free disk: {disk_free_gb:.1f} GB")

        status = "info"
        if ram_mb and ram_mb < 512:
            status = "warning"
        if disk_free_gb is not None and disk_free_gb < 2:
            status = "warning"

        return _result(
            "system",
            status,
            f"{uname.system} {arch}",
            "; ".join(details_parts),
        )

    @staticmethod
    def _get_ram_mb() -> int | None:
        """Return total physical RAM in MB, or None on failure."""
        try:
            # POSIX: try os.sysconf
            if hasattr(os, "sysconf"):
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                return int((pages * page_size) / (1024 * 1024))
        except (OSError, ValueError, OverflowError):
            pass

        try:
            import psutil  # type: ignore[import-untyped]

            return int(psutil.virtual_memory().total / (1024 * 1024))
        except ImportError:
            pass

        # Windows fallback via ctypes
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.GetPhysDllMemoryLengthEx = getattr(
                kernel32, "GetPhysDllMemoryLengthEx", None
            )
            # Fallback: use GlobalMemoryStatusEx
            import ctypes.wintypes  # type: ignore[import-not-found]

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.wintypes.DWORD),
                    ("dwMemoryLoad", ctypes.wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                return int(mem.ullTotalPhys / (1024 * 1024))
        except Exception as exc:
            logger.debug("Could not read Windows memory stats: %s", exc)

        return None

    @staticmethod
    def _get_disk_free_gb(path: str) -> float | None:
        """Return free disk space in GB for the given path, or None."""
        try:
            usage = shutil.disk_usage(path)
            return usage.free / (1024 ** 3)
        except OSError:
            return None

    # ------------------------------------------------------------------ #
    # Docker                                                               #
    # ------------------------------------------------------------------ #

    def check_docker(self) -> dict:
        """Check Docker and Docker Compose availability."""
        docker_version = self._get_cmd_version(["docker", "--version"])
        compose_version = self._get_cmd_version(
            ["docker", "compose", "version"]
        )

        if not docker_version:
            return _result(
                "docker",
                "warning",
                "Docker not found",
                "Docker is recommended for containerised deployments",
            )

        details = f"Docker: {docker_version}"
        status = "info"
        if compose_version:
            details += f"; Compose: {compose_version}"
        else:
            details += "; Docker Compose: not found"
            status = "warning"

        return _result("docker", status, f"Docker {docker_version}", details)

    # ------------------------------------------------------------------ #
    # Python                                                               #
    # ------------------------------------------------------------------ #

    def check_python(self) -> dict:
        """Check Python version and required packages."""
        ver = platform.python_version()
        required = ["fastapi", "sqlalchemy", "pydantic", "uvicorn"]
        missing: list[str] = []

        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)

        status = "info"
        details = f"Python {ver}"
        if missing:
            status = "warning"
            details += f"; missing: {', '.join(missing)}"

        return _result("python", status, f"Python {ver}", details)

    # ------------------------------------------------------------------ #
    # PostgreSQL                                                           #
    # ------------------------------------------------------------------ #

    def check_postgres(self) -> dict:
        """Test PostgreSQL connectivity and retrieve version."""
        try:
            import psycopg  # type: ignore[import-untyped]

            conn = psycopg.connect(
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                user=os.environ.get("POSTGRES_USER", ""),
                password=os.environ.get("POSTGRES_PASSWORD", ""),
                dbname=os.environ.get("POSTGRES_DB", "mission_control"),
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
            conn.close()
            return _result("postgres", "info", "Connected", version)
        except ImportError:
            return _result(
                "postgres",
                "warning",
                "psycopg not installed",
                "Cannot validate PostgreSQL connectivity",
            )
        except Exception as exc:
            return _result(
                "postgres",
                "critical",
                "PostgreSQL unreachable",
                str(exc),
            )

    # ------------------------------------------------------------------ #
    # Redis                                                                #
    # ------------------------------------------------------------------ #

    def check_redis(self) -> dict:
        """Test Redis connectivity and retrieve version."""
        try:
            import redis  # type: ignore[import-untyped]

            client = redis.Redis(
                host=os.environ.get("REDIS_HOST", "redis"),
                port=int(os.environ.get("REDIS_PORT", "6379")),
                socket_connect_timeout=5,
            )
            info = client.info("server")
            version = info.get("redis_version", "unknown")
            client.close()
            return _result(
                "redis", "info", f"Redis {version}", f"Version: {version}"
            )
        except ImportError:
            return _result(
                "redis",
                "warning",
                "redis package not installed",
                "Cannot validate Redis connectivity",
            )
        except Exception as exc:
            return _result(
                "redis",
                "critical",
                "Redis unreachable",
                str(exc),
            )

    # ------------------------------------------------------------------ #
    # Ports                                                                #
    # ------------------------------------------------------------------ #

    def check_ports(self, ports: list[int] | None = None) -> dict:
        """Check whether the given ports are reachable (in-use).

        Returns a *warning* if any port is unreachable and *info* if all
        are reachable.
        """
        if ports is None:
            ports = list(_DEFAULT_PORTS)

        reachable: list[int] = []
        unreachable: list[int] = []

        for port in ports:
            if self._is_port_reachable("127.0.0.1", port, timeout=2):
                reachable.append(port)
            else:
                unreachable.append(port)

        if unreachable:
            return _result(
                "ports",
                "warning",
                f"Unreachable ports: {unreachable}",
                f"Reachable: {reachable}; Unreachable: {unreachable}",
            )
        return _result(
            "ports",
            "info",
            "All checked ports reachable",
            f"Ports: {reachable}",
        )

    @staticmethod
    def _is_port_reachable(
        host: str, port: int, timeout: float = 2.0
    ) -> bool:
        """Return True if *host:port* accepts a TCP connection."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, TimeoutError):
            return False

    # ------------------------------------------------------------------ #
    # Permissions                                                          #
    # ------------------------------------------------------------------ #

    def check_permissions(self) -> dict:
        """Verify write access to key directories."""
        dirs_to_check = [
            Path("uploads"),
            Path("logs"),
            Path("plugins"),
            Path("backups"),
        ]

        writable: list[str] = []
        readonly: list[str] = []

        for d in dirs_to_check:
            if d.exists():
                if os.access(d, os.W_OK):
                    writable.append(str(d))
                else:
                    readonly.append(str(d))
            else:
                # Directory doesn't exist yet — check parent writability
                parent = d.parent
                if os.access(parent, os.W_OK):
                    writable.append(f"{d} (will create)")
                else:
                    readonly.append(str(d))

        status = "info"
        if readonly:
            status = "warning"

        return _result(
            "permissions",
            status,
            "Write access OK" if not readonly else f"Read-only: {readonly}",
            f"Writable: {writable}" + (f"; Read-only: {readonly}" if readonly else ""),
        )

    # ------------------------------------------------------------------ #
    # TLS                                                                  #
    # ------------------------------------------------------------------ #

    def check_tls(self) -> dict:
        """Check for TLS certificate files (informational)."""
        cert_paths = [
            Path("certs/cert.pem"),
            Path("certs/server.crt"),
            Path("/etc/ssl/certs/missioncontrol.pem"),
        ]

        found = [str(p) for p in cert_paths if p.exists()]

        if found:
            return _result(
                "tls",
                "info",
                "TLS certificates found",
                f"Found: {found}",
            )
        return _result(
            "tls",
            "info",
            "No TLS certificates detected",
            "TLS certificates are optional for development",
        )

    # ------------------------------------------------------------------ #
    # Firewall                                                             #
    # ------------------------------------------------------------------ #

    def check_firewall(self) -> dict:
        """Basic firewall detection (informational)."""
        system = platform.system()

        if system == "Linux":
            return self._check_firewall_linux()
        elif system == "Windows":
            return self._check_firewall_windows()
        else:
            return _result(
                "firewall",
                "info",
                f"Firewall detection not implemented for {system}",
                "",
            )

    def _check_firewall_linux(self) -> dict:
        """Detect iptables / ufw / firewalld on Linux."""
        for cmd_name, label in [
            (["ufw", "status"], "ufw"),
            (["firewall-cmd", "--state"], "firewalld"),
            (["iptables", "-L", "-n"], "iptables"),
        ]:
            output = self._get_cmd_output(cmd_name)
            if output is not None:
                active = "active" in output.lower() or "running" in output.lower()
                return _result(
                    "firewall",
                    "info",
                    f"Detected {label}" + (" (active)" if active else ""),
                    output.strip()[:500],
                )

        return _result(
            "firewall",
            "info",
            "No common Linux firewall detected",
            "",
        )

    def _check_firewall_windows(self) -> dict:
        """Detect Windows Firewall status."""
        output = self._get_cmd_output(
            ["netsh", "advfirewall", "show", "allprofiles", "state"]
        )
        if output is not None:
            active = "ON" in output.upper()
            return _result(
                "firewall",
                "info",
                f"Windows Firewall {'active' if active else 'inactive'}",
                output.strip()[:500],
            )
        return _result(
            "firewall",
            "info",
            "Could not query Windows Firewall",
            "",
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_cmd_version(cmd: list[str]) -> str | None:
        """Run a command and return its first line, or None on failure."""
        try:
            result = subprocess.run(  # noqa: S603 - cmd is a static list, no shell, no user input
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32"
                    else 0
                ),
            )
            output = (result.stdout or result.stderr or "").strip()
            return output.splitlines()[0] if output else None
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return None

    @staticmethod
    def _get_cmd_output(cmd: list[str]) -> str | None:
        """Run a command and return its combined output, or None."""
        try:
            result = subprocess.run(  # noqa: S603 - cmd is a static list, no shell, no user input
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32"
                    else 0
                ),
            )
            return (result.stdout or result.stderr or "").strip() or None
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return None
