"""
Hyper-V Plugin Sync

Background synchronization classes that pull data from Hyper-V hosts
(via the existing provider factory) and write to local cache tables.
"""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.plugins.installed.hyperv.models import (
    HyperVCheckpoint,
    HyperVHost,
    HyperVNetwork,
    HyperVVM,
    HyperVVolume,
)

if TYPE_CHECKING:
    from app.providers.hyperv.base_provider import HyperVProvider

logger = logging.getLogger("plugin.hyperv.sync")


class HostSync:
    """Synchronize Hyper-V host registrations from IntegrationProfile."""

    def sync(self, session: Session, host_id: int, hostname: str,
             transport: str = "winrm", port: int = 5985) -> int:
        """Upsert a host record. Returns 1 if upserted."""
        stmt = pg_insert(HyperVHost).values(
            name=hostname,
            hostname=hostname,
            transport=transport,
            port=port,
            enabled=True,
            last_sync_at=datetime.now(UTC),
            status="healthy",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["name"],
            set_={
                "hostname": hostname,
                "transport": transport,
                "port": port,
                "enabled": True,
                "last_sync_at": datetime.now(UTC),
                "status": "healthy",
            },
        )
        session.execute(stmt)
        session.commit()
        return 1


class VMSync:
    """Synchronize VM inventory from Hyper-V to local cache."""

    def sync(self, session: Session, client: "HyperVProvider", host_id: int) -> dict[str, int]:
        """Pull VMs and upsert into hyperv_vms."""
        result = client.get_vms()
        if not result.get("connected"):
            return {"synced": 0, "error": result.get("error", "unknown")}

        items = result.get("items", [])
        synced = 0

        for v in items:
            vm_id = str(v.get("id", ""))
            if not vm_id:
                continue

            stmt = pg_insert(HyperVVM).values(
                host_id=host_id,
                vm_id=vm_id,
                name=v.get("name", ""),
                state=v.get("state", "unknown"),
                cpu_count=v.get("cpu_count", 0),
                memory_assigned_mb=v.get("memory_assigned_mb", 0),
                memory_startup_mb=v.get("memory_startup_mb", 0),
                memory_demand_mb=v.get("memory_demand_mb", 0),
                uptime_seconds=v.get("uptime_seconds", 0),
                host_server=v.get("host_server", ""),
                guest_os=v.get("guest_os"),
                creation_time=v.get("creation_time"),
                last_checkpoint=v.get("last_checkpoint"),
                status_message=v.get("status_message"),
                integration_services_enabled=v.get("integration_services_enabled", False),
                cpu_usage_percent=v.get("cpu_usage_percent", 0.0),
                disk_read_mbps=v.get("disk_read_mbps", 0.0),
                disk_write_mbps=v.get("disk_write_mbps", 0.0),
                network_receive_mbps=v.get("network_receive_mbps", 0.0),
                network_send_mbps=v.get("network_send_mbps", 0.0),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["host_id", "vm_id"],
                set_={
                    "name": v.get("name", ""),
                    "state": v.get("state", "unknown"),
                    "cpu_count": v.get("cpu_count", 0),
                    "memory_assigned_mb": v.get("memory_assigned_mb", 0),
                    "uptime_seconds": v.get("uptime_seconds", 0),
                    "cpu_usage_percent": v.get("cpu_usage_percent", 0.0),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("VM sync: %d synced", synced)
        return {"synced": synced}


class NetworkSync:
    """Synchronize virtual switch data from Hyper-V to local cache."""

    def sync(self, session: Session, client: "HyperVProvider", host_id: int) -> dict[str, int]:
        """Pull networks and upsert into hyperv_networks."""
        result = client.get_networks()
        if not result.get("connected"):
            return {"synced": 0, "error": result.get("error", "unknown")}

        items = result.get("items", [])
        synced = 0

        for n in items:
            switch_id = str(n.get("id", ""))
            if not switch_id:
                continue

            stmt = pg_insert(HyperVNetwork).values(
                host_id=host_id,
                switch_id=switch_id,
                name=n.get("name", ""),
                switch_type=n.get("switch_type", "external"),
                allow_management_os=n.get("allow_management_os", True),
                status=n.get("status", "operational"),
                connected_vms=n.get("connected_vms", 0),
                net_adapter=n.get("net_adapter"),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["host_id", "switch_id"],
                set_={
                    "name": n.get("name", ""),
                    "switch_type": n.get("switch_type", "external"),
                    "allow_management_os": n.get("allow_management_os", True),
                    "status": n.get("status", "operational"),
                    "connected_vms": n.get("connected_vms", 0),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Network sync: %d synced", synced)
        return {"synced": synced}


class VolumeSync:
    """Synchronize virtual hard disk data from Hyper-V to local cache."""

    def sync(self, session: Session, client: "HyperVProvider", host_id: int) -> dict[str, int]:
        """Pull volumes and upsert into hyperv_volumes."""
        result = client.get_storage()
        if not result.get("connected"):
            return {"synced": 0, "error": result.get("error", "unknown")}

        items = result.get("items", [])
        synced = 0

        for v in items:
            disk_id = str(v.get("id", ""))
            if not disk_id:
                continue

            stmt = pg_insert(HyperVVolume).values(
                host_id=host_id,
                disk_id=disk_id,
                name=v.get("name", ""),
                path=v.get("path", ""),
                size_bytes=v.get("size_bytes", 0),
                used_bytes=v.get("used_bytes", 0),
                type=v.get("type", "vhdx"),
                vm_name=v.get("vm_name"),
                attached=v.get("attached", True),
                format=v.get("format"),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["host_id", "disk_id"],
                set_={
                    "name": v.get("name", ""),
                    "size_bytes": v.get("size_bytes", 0),
                    "used_bytes": v.get("used_bytes", 0),
                    "type": v.get("type", "vhdx"),
                    "attached": v.get("attached", True),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Volume sync: %d synced", synced)
        return {"synced": synced}


class CheckpointSync:
    """Synchronize checkpoint data from Hyper-V to local cache."""

    def sync(self, session: Session, client: "HyperVProvider", host_id: int) -> dict[str, int]:
        """Pull checkpoints and upsert into hyperv_checkpoints."""
        result = client.get_checkpoints()
        if not result.get("connected"):
            return {"synced": 0, "error": result.get("error", "unknown")}

        items = result.get("items", [])
        synced = 0

        for c in items:
            checkpoint_id = str(c.get("id", ""))
            if not checkpoint_id:
                continue

            stmt = pg_insert(HyperVCheckpoint).values(
                host_id=host_id,
                checkpoint_id=checkpoint_id,
                vm_id=str(c.get("vm_id", c.get("vmId", ""))),
                vm_name=c.get("vm_name", c.get("vmName", "")),
                name=c.get("name", ""),
                checkpoint_type=c.get("checkpoint_type", c.get("CheckpointType", "standard")),
                creation_time=c.get("creation_time", c.get("CreationTime")),
                size_bytes=c.get("size_bytes", c.get("Size", 0)),
                parent_checkpoint_id=str(c.get("parent_checkpoint_id", c.get("ParentCheckpointId", ""))),
                notes=c.get("notes", c.get("Notes")),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["host_id", "checkpoint_id"],
                set_={
                    "name": c.get("name", ""),
                    "size_bytes": c.get("size_bytes", c.get("Size", 0)),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Checkpoint sync: %d synced", synced)
        return {"synced": synced}
