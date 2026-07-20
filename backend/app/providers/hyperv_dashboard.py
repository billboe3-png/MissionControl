"""
Mission Control Virtualization Dashboard Provider

Provides aggregated virtualization data for the dashboard card.
Uses VirtualizationProvider — never depends on specific implementations.
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VirtualizationDashboardProvider:
    """Aggregate virtualization data for the dashboard."""

    async def get_virtualization_data(self, db: Session) -> dict:
        """Return summary data for the dashboard virtualization card."""
        try:
            from app.providers.hyperv.provider_factory import get_hyperv_provider

            provider = get_hyperv_provider(db)
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
                "hostname": summary.get("hostname", ""),
                "total_vms": summary.get("total_vms", 0),
                "running": summary.get("running", 0),
                "stopped": summary.get("stopped", 0),
                "paused": summary.get("paused", 0),
                "total_cpu": summary.get("total_cpu", 0),
                "total_memory_gb": summary.get("total_memory_gb", 0),
                "used_memory_gb": summary.get("used_memory_gb", 0),
                "total_storage_gb": summary.get("total_storage_gb", 0),
                "used_storage_gb": summary.get("used_storage_gb", 0),
            }
        except Exception as e:
            logger.warning("Dashboard: Hyper-V data failed: %s", e)
            return {
                "connected": False,
                "total_vms": 0,
                "running": 0,
                "stopped": 0,
                "total_memory_gb": 0,
                "used_memory_gb": 0,
                "error": str(e),
            }


virtualization_dashboard_provider = VirtualizationDashboardProvider()
