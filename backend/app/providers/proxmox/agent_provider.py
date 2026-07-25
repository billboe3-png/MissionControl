"""
Mission Control Agent Proxmox Provider

Reads Proxmox inventory from agent-collected remote target data
stored in Agent.inventory_json.  Implements ProxmoxProvider so
the existing Proxmox pages work transparently for agent-relayed hosts.

Write operations (start/stop/restart VMs, LXC actions, snapshots)
dispatch commands to the agent via the server's command queue.
"""

import json
import logging

from .base_provider import ProxmoxProvider

logger = logging.getLogger(__name__)


class AgentProxmoxProvider(ProxmoxProvider):
    """Proxmox provider backed by agent remote inventory data."""

    def __init__(
        self,
        inventory: dict,
        target_hostname: str = "",
        agent_id: int | None = None,
        target_id: int | None = None,
        dispatch_cmd: callable | None = None,
    ) -> None:
        self._inventory = inventory or {}
        self._hostname = target_hostname
        self._agent_id = agent_id
        self._target_id = target_id
        self._dispatch_cmd = dispatch_cmd

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

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

    async def _dispatch(self, command_str: str) -> dict:
        if not self._dispatch_cmd:
            return {"success": False, "error": "No agent dispatch available for this host"}
        try:
            return await self._dispatch_cmd(command_str)
        except Exception as e:
            logger.exception("Agent dispatch failed for target %s", self._target_id)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    # Connection / summary                                                #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        return {
            "connected": True,
            "latency_ms": 0,
            "message": f"Agent-relayed connection to {self._hostname}",
            "hostname": self._hostname,
            "version": "agent",
        }

    async def get_summary(self) -> dict:
        vms = self._get_items("vms")
        lxc = self._get_items("lxc")
        nodes = self._get_items("nodes")
        running_vms = sum(1 for v in vms if (v.get("status") or "").lower() == "running")
        stopped_vms = sum(1 for v in vms if (v.get("status") or "").lower() == "stopped")
        return {
            "connected": True,
            "hostname": self._hostname,
            "cluster": self._hostname,
            "version": "agent",
            "nodes": len(nodes),
            "qemu": len(vms),
            "lxc": len(lxc),
            "running": running_vms,
            "stopped": stopped_vms,
            "total_memory_gb": 0,
            "used_memory_gb": 0,
            "total_storage_gb": 0,
            "used_storage_gb": 0,
            "cpu_usage_percent": 0,
        }

    # ------------------------------------------------------------------ #
    # Nodes                                                               #
    # ------------------------------------------------------------------ #

    async def get_nodes(self) -> dict:
        nodes = self._get_items("nodes")
        return {"connected": True, "count": len(nodes), "items": nodes}

    # ------------------------------------------------------------------ #
    # VMs                                                                 #
    # ------------------------------------------------------------------ #

    async def get_vms(self) -> dict:
        vms = self._get_items("vms")
        items = [
            {
                "vmid": v.get("vmid", v.get("id", "")),
                "name": v.get("name", ""),
                "status": v.get("status", "unknown"),
                "node": v.get("node", ""),
                "cpu": float(v.get("cpu", 0)),
                "cpus": int(v.get("cpus", 0)),
                "maxmem": int(v.get("maxmem", 0)),
                "mem": int(v.get("mem", 0)),
                "maxdisk": int(v.get("maxdisk", 0)),
                "disk": int(v.get("disk", 0)),
                "uptime": int(v.get("uptime", 0)),
                "template": v.get("template", 0),
            }
            for v in vms
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_vm_detail(self, vm_id: str) -> dict:
        vms = self._get_items("vms")
        for v in vms:
            vid = str(v.get("vmid", v.get("id", "")))
            if vid == vm_id or v.get("name") == vm_id:
                return {"connected": True, "item": v}
        return {"connected": False, "error": "VM not found in agent inventory"}

    # ------------------------------------------------------------------ #
    # VM actions (dispatched to agent via command queue)                  #
    # ------------------------------------------------------------------ #

    async def start_vm(self, vm_id: str) -> dict:
        return await self._dispatch(f"start_vm:{vm_id}")

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        return await self._dispatch(f"stop_vm:{vm_id}" + (":force" if force else ""))

    async def restart_vm(self, vm_id: str) -> dict:
        return await self._dispatch(f"restart_vm:{vm_id}")

    async def pause_vm(self, vm_id: str) -> dict:
        return await self._dispatch(f"suspend_vm:{vm_id}")

    async def resume_vm(self, vm_id: str) -> dict:
        return await self._dispatch(f"resume_vm:{vm_id}")

    # ------------------------------------------------------------------ #
    # LXC                                                                 #
    # ------------------------------------------------------------------ #

    async def get_lxc_containers(self) -> dict:
        containers = self._get_items("lxc")
        items = [
            {
                "vmid": c.get("vmid", c.get("id", "")),
                "name": c.get("name", ""),
                "status": c.get("status", "unknown"),
                "node": c.get("node", ""),
                "cpu": float(c.get("cpu", 0)),
                "cpus": int(c.get("cpus", 0)),
                "maxmem": int(c.get("maxmem", 0)),
                "mem": int(c.get("mem", 0)),
                "maxdisk": int(c.get("maxdisk", 0)),
                "disk": int(c.get("disk", 0)),
                "uptime": int(c.get("uptime", 0)),
            }
            for c in containers
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_lxc_detail(self, vm_id: str) -> dict:
        containers = self._get_items("lxc")
        for c in containers:
            cid = str(c.get("vmid", c.get("id", "")))
            if cid == vm_id or c.get("name") == vm_id:
                return {"connected": True, "item": c}
        return {"connected": False, "error": "LXC container not found in agent inventory"}

    async def start_lxc(self, vm_id: str) -> dict:
        return await self._dispatch(f"start_lxc:{vm_id}")

    async def stop_lxc(self, vm_id: str) -> dict:
        return await self._dispatch(f"stop_lxc:{vm_id}")

    async def get_lxc_templates(self, node: str | None = None) -> dict:
        return {"connected": True, "count": 0, "items": []}

    async def create_lxc(self, config: dict) -> dict:
        return {"success": False, "error": "LXC creation not supported via agent relay"}

    async def delete_lxc(self, vm_id: str, purge: bool = False) -> dict:
        return await self._dispatch(f"delete_lxc:{vm_id}" + (":purge" if purge else ""))

    async def clone_lxc(self, vm_id: str, new_vmid: str | None = None, hostname: str | None = None) -> dict:
        return {"success": False, "error": "LXC cloning not supported via agent relay"}

    # ------------------------------------------------------------------ #
    # Networks                                                            #
    # ------------------------------------------------------------------ #

    async def get_networks(self) -> dict:
        networks = self._get_items("networks")
        items = [
            {
                "iface": n.get("iface", n.get("name", "")),
                "node": n.get("node", ""),
                "type": n.get("type", "unknown"),
                "active": n.get("active", False),
                "address": n.get("address", ""),
                "netmask": n.get("netmask", ""),
                "bridge_ports": n.get("bridge_ports", ""),
            }
            for n in networks
        ]
        return {"connected": True, "count": len(items), "items": items}

    # ------------------------------------------------------------------ #
    # Storage                                                             #
    # ------------------------------------------------------------------ #

    async def get_storage(self) -> dict:
        storage = self._get_items("storage")
        items = [
            {
                "storage": s.get("storage", s.get("name", "")),
                "node": s.get("node", ""),
                "type": s.get("type", ""),
                "content": s.get("content", ""),
                "active": s.get("active", True),
                "total": int(s.get("total", 0)),
                "used": int(s.get("used", 0)),
                "avail": int(s.get("avail", 0)),
            }
            for s in storage
        ]
        return {"connected": True, "count": len(items), "items": items}

    # ------------------------------------------------------------------ #
    # Tasks                                                               #
    # ------------------------------------------------------------------ #

    async def get_tasks(self, node: str | None = None) -> dict:
        tasks = self._get_items("tasks")
        if node:
            tasks = [t for t in tasks if t.get("node") == node]
        return {"connected": True, "count": len(tasks), "items": tasks[:50]}

    # ------------------------------------------------------------------ #
    # Snapshots                                                           #
    # ------------------------------------------------------------------ #

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        return {"connected": True, "count": 0, "items": []}

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        name_flag = f":{name}" if name else ""
        return await self._dispatch(f"create_snapshot:{vm_id}{name_flag}")

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        return await self._dispatch(f"delete_snapshot:{vm_id}:{snapshot_id}")

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def get_health(self) -> dict:
        nodes = self._get_items("nodes")
        return {
            "connected": True,
            "status": "healthy",
            "nodes": [
                {
                    "name": n.get("node", n.get("name", "")),
                    "status": n.get("status", "unknown"),
                    "cpu_percent": float(n.get("cpu", 0)) * 100,
                    "memory_percent": 0,
                    "uptime_seconds": int(n.get("uptime", 0)),
                    "vm_count": 0,
                    "version": "agent",
                }
                for n in nodes
            ],
        }
