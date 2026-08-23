"""
Mission Control Agent Active Directory Provider

Reads Active Directory data from agent-collected inventory
stored in Agent.inventory_json.  Implements ActiveDirectoryProvider
so the existing AD pages work transparently for agent-relayed hosts.

Write operations (password reset, unlock, enable/disable, rename, group
membership) are dispatched to the agent via the AgentCommand queue using
the ``active_directory`` namespace, mirroring the Veeam SSH-relay pattern.
"""

import asyncio
import json
import logging
import time
from typing import Any

from .base_provider import ActiveDirectoryProvider

logger = logging.getLogger(__name__)


class AgentActiveDirectoryProvider(ActiveDirectoryProvider):
    """Active Directory provider backed by agent inventory data."""

    def __init__(
        self,
        inventory: dict,
        hostname: str = "agent",
        db: Any = None,
        agent_id: int | None = None,
        target_id: int | None = None,
    ) -> None:
        self._inventory = inventory or {}
        self._hostname = hostname
        self._db = db
        self._agent_id = agent_id
        self._target_id = target_id

    def _is_available(self) -> bool:
        return bool(self._inventory.get("available", True))

    def _relay_error(self) -> str:
        return self._inventory.get("error") or "AD relay unavailable"

    def _get_items(self, key: str) -> list[dict]:
        raw = self._inventory.get(key, [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = []
        if isinstance(raw, dict):
            raw = [raw]
        return raw

    async def test_connection(self) -> dict:
        if not self._is_available():
            return {
                "connected": False,
                "error": self._relay_error(),
            }
        return {
            "connected": True,
            "message": "Agent-relayed Active Directory data",
            "server": self._hostname,
        }

    async def get_summary(self) -> dict:
        if not self._is_available():
            return {
                "connected": False,
                "domain": {"name": "", "base_dn": ""},
                "user_count": 0,
                "group_count": 0,
                "computer_count": 0,
                "error": self._relay_error(),
            }
        users = self._get_items("users")
        groups = self._get_items("groups")
        devices = self._get_items("devices")
        dom_raw = self._inventory.get("domain")
        domain_info = (
            dom_raw
            if isinstance(dom_raw, dict)
            else {"name": str(dom_raw or self._hostname), "base_dn": ""}
        )
        return {
            "connected": True,
            "domain": domain_info,
            "user_count": len(users),
            "group_count": len(groups),
            "computer_count": len(devices),
        }

    async def get_users(self) -> dict:
        if not self._is_available():
            return {
                "connected": False,
                "users": [],
                "total_count": 0,
                "error": self._relay_error(),
            }
        users = self._get_items("users")
        formatted = []
        for u in users:
            formatted.append(
                {
                    "sam_account_name": u.get("sam_account_name")
                    or u.get("sam")
                    or "",
                    "display_name": u.get("display_name")
                    or u.get("sam_account_name")
                    or "",
                    "email": u.get("email"),
                    "department": u.get("department"),
                    "title": u.get("title"),
                    "enabled": u.get("enabled", True),
                    "distinguished_name": u.get("distinguished_name"),
                }
            )
        return {"connected": True, "users": formatted, "total_count": len(formatted)}

    async def get_groups(self) -> dict:
        if not self._is_available():
            return {
                "connected": False,
                "groups": [],
                "total_count": 0,
                "error": self._relay_error(),
            }
        groups = self._get_items("groups")
        formatted = [
            {"name": g.get("name") or g.get("sam") or "", "description": g.get("description")}
            for g in groups
        ]
        return {"connected": True, "groups": formatted, "total_count": len(formatted)}

    async def get_devices(self) -> dict:
        if not self._is_available():
            return {
                "connected": False,
                "devices": [],
                "total_count": 0,
                "error": self._relay_error(),
            }
        devices = self._get_items("devices")
        formatted = [
            {
                "name": d.get("name") or d.get("sam") or "",
                "dns_name": d.get("dns_name"),
                "os_version": d.get("os_version"),
            }
            for d in devices
        ]
        return {"connected": True, "devices": formatted, "total_count": len(formatted)}

    async def get_health(self) -> dict:
        if not self._is_available():
            return {
                "connected": False,
                "status": "unknown",
                "replication": {
                    "status": "unknown",
                    "pending_replications": 0,
                    "failed_replications": 0,
                },
                "error": self._relay_error(),
            }
        health_inv = self._inventory.get("health") or {}
        repl = health_inv.get("replication") or {
            "status": "healthy",
            "pending_replications": 0,
            "failed_replications": 0,
        }
        return {
            "connected": True,
            "status": health_inv.get("status", "healthy"),
            "replication": repl,
        }

    def _purge_command(self, cand: Any) -> None:
        # Purge the command row — it contains plaintext secrets (e.g. new_password). Known limitation: the row is briefly at rest during the poll window.
        try:
            self._db.delete(cand)
            self._db.commit()
        except Exception:
            logger.warning(
                "Failed to purge agent command row %s",
                getattr(cand, "id", None),
                exc_info=True,
            )

    async def _dispatch_cmd(self, op: str, params: dict) -> dict:
        if not self._db or not self._agent_id:
            return {"success": False, "error": "No DB or agent_id for write operation"}

        from app.repositories.agent_repository import AgentCommandRepository

        payload = {
            "namespace": "active_directory",
            "op": op,
            "params": {"target_id": self._target_id or 1, **params},
        }
        cmd = await asyncio.to_thread(
            AgentCommandRepository.create,
            self._db,
            agent_id=self._agent_id,
            command_type="remote_execute",
            command=json.dumps(payload),
            timeout=60,
        )

        # Wait window covers the agent poll interval, the PowerShell
        # execution and the post-command inventory refresh; queued
        # duplicates from impatient clicks also drain within this budget.
        start = time.monotonic()
        while time.monotonic() - start < 90:
            if callable(getattr(self._db, "expire_all", None)):
                self._db.expire_all()
            cand = AgentCommandRepository.get_by_id(self._db, cmd.id)
            if cand and cand.status in ("completed", "failed"):
                if cand.status == "failed" or cand.exit_code != 0:
                    self._purge_command(cand)
                    return {
                        "success": False,
                        "error": cand.stderr
                        or cand.error_message
                        or "Command failed",
                    }
                try:
                    result = json.loads(cand.stdout or "{}")
                    self._purge_command(cand)
                    return result
                except Exception:
                    self._purge_command(cand)
                    return {"success": True, "output": cand.stdout}
            await asyncio.sleep(1.0)
        return {"success": False, "error": "Command timed out waiting for agent"}

    async def reset_password(self, sam_account_name: str, new_password: str) -> dict:
        return await self._dispatch_cmd(
            "reset-password",
            {"sam_account_name": sam_account_name, "new_password": new_password},
        )

    async def unlock_account(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("unlock", {"sam_account_name": sam_account_name})

    async def enable_account(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("enable", {"sam_account_name": sam_account_name})

    async def disable_account(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("disable", {"sam_account_name": sam_account_name})

    async def rename_user(
        self,
        sam_account_name: str,
        new_display_name: str,
        new_first_name: str | None = None,
        new_last_name: str | None = None,
    ) -> dict:
        return await self._dispatch_cmd(
            "rename",
            {
                "sam_account_name": sam_account_name,
                "display_name": new_display_name,
            },
        )

    async def get_user_groups(self, sam_account_name: str) -> dict:
        result = await self._dispatch_cmd(
            "get-user-groups", {"sam_account_name": sam_account_name}
        )
        groups = result.get("groups") or []
        if not groups and isinstance(result.get("output"), str):
            try:
                parsed = json.loads(result["output"])
                if isinstance(parsed, list):
                    groups = parsed
                elif isinstance(parsed, dict) and parsed.get("groups"):
                    groups = parsed["groups"]
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "connected": bool(result.get("success", False)),
            "groups": groups,
            "error": result.get("error"),
        }

    async def add_to_group(self, sam_account_name: str, group_name: str) -> dict:
        return await self._dispatch_cmd(
            "add-to-group",
            {"sam_account_name": sam_account_name, "group_name": group_name},
        )

    async def remove_from_group(self, sam_account_name: str, group_name: str) -> dict:
        return await self._dispatch_cmd(
            "remove-from-group",
            {"sam_account_name": sam_account_name, "group_name": group_name},
        )