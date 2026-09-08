"""
D-Link DGS-1210 Sync - Background inventory collection
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.plugins.installed.official_dlink.models import DLinkSwitch
from app.plugins.installed.official_dlink.repository import repository
from app.plugins.installed.official_dlink.service import dlink_service

logger = logging.getLogger("plugin.dlink.sync")


class DLinkSync:
    """Background sync service for D-Link switches."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, interval: int = 300):
        """Start the periodic sync task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._sync_loop(interval))
        logger.info(f"D-Link sync started with interval {interval}s")

    async def stop(self):
        """Stop the sync task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("D-Link sync stopped")

    async def _sync_loop(self, interval: int):
        """Main sync loop."""
        while self._running:
            try:
                await self._sync_all_switches()
            except Exception as e:
                logger.exception("Error in D-Link sync loop")
            await asyncio.sleep(interval)

    async def _sync_all_switches(self):
        """Sync all enabled switches."""
        db = SessionLocal()
        try:
            switches = db.query(DLinkSwitch).filter(
                DLinkSwitch.enabled == True,
                DLinkSwitch.remote_target_id.isnot(None)
            ).all()

            for switch in switches:
                if not self._running:
                    break
                try:
                    await self._sync_switch(switch.id)
                except Exception as e:
                    logger.exception(f"Error syncing switch {switch.id}")
        finally:
            db.close()

    async def _sync_switch(self, switch_id: int):
        """Sync a single switch."""
        db = SessionLocal()
        try:
            switch = repository.get_switch(db, switch_id)
            if not switch or not switch.enabled:
                return

            logger.info(f"Syncing D-Link switch {switch.name} ({switch.host})")

            # Collect inventory (updates switch info)
            await dlink_service.collect_inventory(db, switch_id)

            # Collect MAC table
            mac_result = await dlink_service.collect_mac_table(db, switch_id)
            if mac_result.get("success") and "mac_table" in mac_result:
                repository.bulk_upsert_mac_entries(db, switch_id, mac_result["mac_table"])
                # Mark old entries as inactive
                repository.mark_mac_entries_inactive(
                    db, switch_id,
                    datetime.utcnow().replace(second=0, microsecond=0)
                )
                db.commit()

            # Collect VLANs
            vlan_result = await dlink_service.collect_vlans(db, switch_id)
            if vlan_result.get("success") and "vlans" in vlan_result:
                for v in vlan_result["vlans"]:
                    repository.upsert_vlan(
                        db, switch_id,
                        v.get("vlan_id"),
                        v.get("name"),
                        v.get("ports_tagged"),
                        v.get("ports_untagged"),
                        v.get("ports_forbidden")
                    )
                db.commit()

            # Collect Port VLANs
            pv_result = await dlink_service.collect_port_vlans(db, switch_id)
            if pv_result.get("success") and "port_vlans" in pv_result:
                for pv in pv_result["port_vlans"]:
                    repository.upsert_port_vlan(
                        db, switch_id,
                        pv.get("port"),
                        pv.get("pvid", 1),
                        pv.get("allowed_vlans"),
                        pv.get("mode", "access")
                    )
                db.commit()

            logger.info(f"Sync completed for switch {switch.name}")

        except Exception as e:
            logger.exception(f"Error syncing switch {switch_id}")
        finally:
            db.close()

    async def sync_switch_now(self, switch_id: int) -> Dict[str, Any]:
        """Trigger immediate sync for a switch."""
        db = SessionLocal()
        try:
            switch = repository.get_switch(db, switch_id)
            if not switch:
                return {"success": False, "error": "Switch not found"}

            await self._sync_switch(switch_id)
            return {"success": True, "message": "Sync completed"}
        finally:
            db.close()


# Singleton instance
sync_service = DLinkSync()