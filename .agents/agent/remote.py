"""Mission Control Agent - Remote target manager."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from .connectors.base import RemoteConnector

logger = logging.getLogger("mc-agent")


def _parse_plugins(raw: Any) -> set[str] | None:
    """Return the set of plugin keys for a target.

    Returns None when the target has no plugin selection (collect everything).
    """
    if not raw:
        return None
    if isinstance(raw, list):
        return {str(p).strip() for p in raw if str(p).strip()}
    return {p.strip() for p in str(raw).split(",") if p.strip()}


def _create_connector(target: dict[str, Any]) -> RemoteConnector | None:
    """Factory: create the right connector based on protocol."""
    protocol = target.get("protocol", "psremoting")

    if protocol == "psremoting":
        from .connectors.psremoting import PSRemotingConnector

        return PSRemotingConnector(target)
    elif protocol == "ssh":
        from .connectors.ssh import SSHConnector

        return SSHConnector(target)
    elif protocol == "winrm":
        from .connectors.winrm_connector import WinRMConnector

        return WinRMConnector(target)
    else:
        logger.warning("Unknown protocol '%s' for target %s", protocol, target.get("name"))
        return None


class RemoteManager:
    """Manages connections to remote targets relayed through the agent."""

    def __init__(self):
        self._targets: dict[int, dict[str, Any]] = {}
        self._connectors: dict[int, RemoteConnector] = {}

    def update_targets(self, targets: list[dict]) -> None:
        """Update target list from heartbeat response."""
        new_ids = {t["id"] for t in targets}

        for tid in list(self._connectors.keys()):
            if tid not in new_ids:
                connector = self._connectors.pop(tid, None)
                if connector:
                    self._tasks.append(asyncio.create_task(connector.disconnect()))
                del self._targets[tid]

        for target in targets:
            tid = target["id"]
            old = self._targets.get(tid)
            self._targets[tid] = target
            if tid in self._connectors:
                if old and (
                    old.get("hostname") != target.get("hostname")
                    or old.get("password") != target.get("password")
                    or old.get("port") != target.get("port")
                    or old.get("username") != target.get("username")
                    or old.get("protocol") != target.get("protocol")
                ):
                    old_conn = self._connectors.pop(tid)
                    self._tasks.append(asyncio.create_task(old_conn.disconnect()))
                    connector = _create_connector(target)
                    if connector:
                        self._connectors[tid] = connector
            else:
                connector = _create_connector(target)
                if connector:
                    self._connectors[tid] = connector

        logger.info(
            "Remote targets updated: %d active (%d total)",
            len(self._connectors),
            len(targets),
        )

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect inventory from all targets concurrently."""
        if not self._connectors:
            return {}

        results: dict[str, Any] = {}

        async def _collect_one(target_id: int, connector: RemoteConnector):
            target = self._targets[target_id]
            key = f"target-{target_id}"
            try:
                conn_test = await connector.test_connection()
                if not conn_test.get("connected"):
                    results[key] = {
                        "hostname": target["hostname"],
                        "protocol": target["protocol"],
                        "collected_at": datetime.now(UTC).isoformat(),
                        "status": "offline",
                        "error": conn_test.get("error", "Connection failed"),
                        "inventory": {},
                    }
                    return

                system = await connector.collect_system_inventory()
                services = await connector.collect_services()

                plugins = _parse_plugins(target.get("target_plugins"))
                hyperv = (
                    await connector.collect_hyperv_inventory()
                    if plugins is None or "hyperv" in plugins
                    else None
                )
                proxmox = (
                    await connector.collect_proxmox_inventory()
                    if plugins is None or "proxmox" in plugins
                    else None
                )
                veeam = (
                    await connector.collect_veeam_inventory()
                    if plugins is None or "veeam" in plugins
                    else None
                )

                inventory: dict[str, Any] = {
                    "system": system,
                    "services": services,
                }
                if hyperv:
                    inventory["hyperv"] = hyperv
                if proxmox:
                    inventory["proxmox"] = proxmox
                if veeam:
                    inventory["veeam"] = veeam

                results[key] = {
                    "hostname": target["hostname"],
                    "protocol": target["protocol"],
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "online",
                    "error": None,
                    "inventory": inventory,
                }

            except Exception as e:
                logger.error("Failed to collect from target %s: %s", target["hostname"], e)
                results[key] = {
                    "hostname": target["hostname"],
                    "protocol": target["protocol"],
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "error",
                    "error": str(e),
                    "inventory": {},
                }

        tasks = [
            _collect_one(tid, conn)
            for tid, conn in self._connectors.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def execute_on_target(
        self, target_id: int, command: str, timeout: int = 60
    ) -> dict:
        """Execute a command on a specific target."""
        connector = self._connectors.get(target_id)
        if connector is None:
            target = self._targets.get(target_id)
            hostname = target["hostname"] if target else "unknown"
            return {
                "success": False,
                "stdout": "",
                "stderr": f"No connector for target {target_id} ({hostname})",
                "exit_code": -1,
            }
        return await connector.execute(command, timeout=timeout)

    @property
    def target_count(self) -> int:
        return len(self._connectors)

    @property
    def targets(self) -> dict[int, dict[str, Any]]:
        return dict(self._targets)
