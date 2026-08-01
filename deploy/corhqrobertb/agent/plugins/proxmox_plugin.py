#!/usr/bin/env python3
"""Mission Control Agent - Proxmox VE plugin."""

import json
import logging
import os
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class ProxmoxPlugin(AgentPlugin):
    """Collect Proxmox VE inventory from the local host."""

    plugin_name = "proxmox"
    platform_hint = "linux"

    async def collect(self, context: dict[str, Any]) -> dict[str, Any]:
        """Collect Proxmox cluster/node/VM/LXC inventory."""
        base_url = os.getenv("MC_PROXMOX_BASE_URL", "").strip()
        token = os.getenv("MC_PROXMOX_TOKEN", "").strip()
        if not base_url or not token:
            logger.info(
                "Proxmox plugin not configured (set MC_PROXMOX_BASE_URL/TOKEN)"
            )
            return {"available": False}

        logger.debug("Proxmox plugin target=%s", base_url)
        return {
            "available": True,
            "cluster_name": None,
            "version": None,
            "nodes_total": 0,
            "nodes_online": 0,
            "total_vms": 0,
            "running_vms": 0,
            "total_lxc": 0,
            "running_lxc": 0,
            "storage_count": 0,
            "nodes": [],
            "vms": [],
            "lxcs": [],
            "storage": [],
            "error": "Not implemented",
        }
