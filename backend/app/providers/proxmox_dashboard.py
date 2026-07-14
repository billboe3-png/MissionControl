"""
Mission Control Proxmox Dashboard Provider

Provides aggregated Proxmox data for the dashboard card.
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProxmoxDashboardProvider:
    """Aggregate Proxmox data for the dashboard."""

    async def get_proxmox_data(self, db: Session) -> dict:
        """Return summary data for the dashboard Proxmox card."""
        try:
            from app.providers.proxmox.provider_factory import get_proxmox_provider

            provider = get_proxmox_provider(db)
            summary = await provider.get_summary()

            if not summary.get("connected"):
                return {
                    "connected": False,
                    "total_vms": 0,
                    "running": 0,
                    "stopped": 0,
                    "total_memory_gb": 0,
                    "used_memory_gb": 0,
                    "error": summary.get("error"),
                }

            return {
                "connected": True,
                "cluster_name": summary.get("cluster_name"),
                "nodes_online": summary.get("nodes_online", 0),
                "nodes_total": summary.get("nodes_total", 0),
                "total_vms": summary.get("total_vms", 0),
                "running": summary.get("running", 0),
                "stopped": summary.get("stopped", 0),
                "paused": summary.get("paused", 0),
                "total_lxc": summary.get("total_lxc", 0),
                "running_lxc": summary.get("running_lxc", 0),
                "stopped_lxc": summary.get("stopped_lxc", 0),
                "total_cpu": summary.get("total_cpu", 0),
                "total_memory_gb": summary.get("total_memory_gb", 0),
                "used_memory_gb": summary.get("used_memory_gb", 0),
                "total_storage_gb": summary.get("total_storage_gb", 0),
                "used_storage_gb": summary.get("used_storage_gb", 0),
            }
        except Exception as e:
            logger.warning("Dashboard: Proxmox data failed: %s", e)
            return {
                "connected": False,
                "total_vms": 0,
                "running": 0,
                "stopped": 0,
                "total_memory_gb": 0,
                "used_memory_gb": 0,
                "error": str(e),
            }


proxmox_dashboard_provider = ProxmoxDashboardProvider()
