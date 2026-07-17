"""
Mission Control Remote Provider Factory

Singleton factory that returns the correct provider
based on connection type.

Sprint 2.1.8 - Remote Operations Finalization.
"""

import logging
from datetime import UTC, datetime

from app.providers.remote.base_provider import RemoteBaseProvider
from app.providers.remote.ssh_provider import SSHProvider
from app.providers.remote.winrm_provider import WinRMProvider

logger = logging.getLogger(__name__)

_ssh_provider: SSHProvider | None = None
_winrm_provider: WinRMProvider | None = None

_metrics: dict = {
    "total_commands_executed": 0,
    "total_commands_failed": 0,
    "latencies": [],
    "last_activity": None,
}


def get_remote_provider(connection_type: str) -> RemoteBaseProvider:
    """
    Return the correct provider based on connection type.

    Supported types:
    - 'ssh' -> SSHProvider
    - 'winrm' -> WinRMProvider

    Raises ValueError for unsupported types.
    """
    global _ssh_provider
    global _winrm_provider

    if connection_type == "ssh":
        if _ssh_provider is None:
            _ssh_provider = SSHProvider()
            logger.info("Created singleton SSHProvider")
        return _ssh_provider

    if connection_type == "winrm":
        if _winrm_provider is None:
            _winrm_provider = WinRMProvider()
            logger.info("Created singleton WinRMProvider")
        return _winrm_provider

    raise ValueError(
        f"Unsupported connection type: {connection_type}. "
        f"Supported types: ssh, winrm"
    )


def record_command_executed(
    success: bool, duration_ms: int
) -> None:
    """Record a command execution for metrics."""
    _metrics["total_commands_executed"] += 1
    if not success:
        _metrics["total_commands_failed"] += 1
    _metrics["latencies"].append(duration_ms)
    if len(_metrics["latencies"]) > 1000:
        _metrics["latencies"] = _metrics["latencies"][-500:]
    _metrics["last_activity"] = datetime.now(UTC).isoformat()


def get_session_metrics() -> dict:
    """Return current session metrics."""
    ssh_sessions = 0
    winrm_sessions = 0

    if _ssh_provider is not None:
        ssh_sessions = len(getattr(_ssh_provider, "_clients", {}))

    avg_latency = 0.0
    if _metrics["latencies"]:
        avg_latency = sum(_metrics["latencies"]) / len(_metrics["latencies"])

    pool_size = 0
    try:
        from app.core.config import get_settings
        pool_size = get_settings().remote_connection_pool_size
    except Exception:
        pool_size = 5

    return {
        "active_ssh_sessions": ssh_sessions,
        "active_winrm_sessions": winrm_sessions,
        "connection_pool_size": pool_size,
        "connection_pool_used": ssh_sessions + winrm_sessions,
        "average_latency_ms": round(avg_latency, 2),
        "total_commands_executed": _metrics["total_commands_executed"],
        "total_commands_failed": _metrics["total_commands_failed"],
        "last_activity": _metrics["last_activity"],
    }
