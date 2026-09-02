"""
D-Link DGS-1210 Repository - Database operations
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from .models import DLinkSwitch, DLinkRemoteTarget, DLinkMacEntry, DLinkVlan, DLinkPortVlan


class DLinkRepository:
    """Repository for D-Link switch data access."""

    # ---- DLinkSwitch ----

    def get_switch(self, db: Session, switch_id: int) -> Optional[DLinkSwitch]:
        return db.query(DLinkSwitch).filter(DLinkSwitch.id == switch_id).first()

    def get_switch_by_host(self, db: Session, host: str) -> Optional[DLinkSwitch]:
        return db.query(DLinkSwitch).filter(DLinkSwitch.host == host).first()

    def list_switches(
        self, db: Session, company_id: Optional[int] = None, site_id: Optional[int] = None,
        enabled_only: bool = False, limit: int = 100, offset: int = 0
    ) -> List[DLinkSwitch]:
        query = db.query(DLinkSwitch)
        if company_id is not None:
            query = query.filter(DLinkSwitch.company_id == company_id)
        if site_id is not None:
            query = query.filter(DLinkSwitch.site_id == site_id)
        if enabled_only:
            query = query.filter(DLinkSwitch.enabled == True)
        return query.order_by(DLinkSwitch.name).offset(offset).limit(limit).all()

    def count_switches(
        self, db: Session, company_id: Optional[int] = None, site_id: Optional[int] = None,
        enabled_only: bool = False
    ) -> int:
        query = db.query(DLinkSwitch)
        if company_id is not None:
            query = query.filter(DLinkSwitch.company_id == company_id)
        if site_id is not None:
            query = query.filter(DLinkSwitch.site_id == site_id)
        if enabled_only:
            query = query.filter(DLinkSwitch.enabled == True)
        return query.count()

    def create_switch(self, db: Session, **kwargs) -> DLinkSwitch:
        switch = DLinkSwitch(**kwargs)
        db.add(switch)
        db.flush()
        return switch

    def update_switch(self, db: Session, switch_id: int, **kwargs) -> Optional[DLinkSwitch]:
        switch = self.get_switch(db, switch_id)
        if not switch:
            return None
        for key, value in kwargs.items():
            if hasattr(switch, key):
                setattr(switch, key, value)
        switch.updated_at = datetime.utcnow()
        db.flush()
        return switch

    def delete_switch(self, db: Session, switch_id: int) -> bool:
        switch = self.get_switch(db, switch_id)
        if not switch:
            return False
        db.delete(switch)
        return True

    # ---- DLinkRemoteTarget ----

    def get_remote_target(self, db: Session, target_id: int) -> Optional[DLinkRemoteTarget]:
        return db.query(DLinkRemoteTarget).filter(DLinkRemoteTarget.id == target_id).first()

    def get_remote_targets_by_agent(self, db: Session, agent_id: int) -> List[DLinkRemoteTarget]:
        return db.query(DLinkRemoteTarget).filter(
            DLinkRemoteTarget.agent_id == agent_id,
            DLinkRemoteTarget.enabled == True
        ).all()

    def create_remote_target(self, db: Session, **kwargs) -> DLinkRemoteTarget:
        target = DLinkRemoteTarget(**kwargs)
        db.add(target)
        db.flush()
        return target

    def update_remote_target(self, db: Session, target_id: int, **kwargs) -> Optional[DLinkRemoteTarget]:
        target = self.get_remote_target(db, target_id)
        if not target:
            return None
        for key, value in kwargs.items():
            if hasattr(target, key):
                setattr(target, key, value)
        target.updated_at = datetime.utcnow()
        db.flush()
        return target

    def delete_remote_target(self, db: Session, target_id: int) -> bool:
        target = self.get_remote_target(db, target_id)
        if not target:
            return False
        db.delete(target)
        return True

    # ---- DLinkMacEntry ----

    def get_mac_entries(
        self, db: Session, switch_id: int, port: Optional[str] = None,
        vlan_id: Optional[int] = None, active_only: bool = True,
        limit: int = 500, offset: int = 0
    ) -> List[DLinkMacEntry]:
        query = db.query(DLinkMacEntry).filter(DLinkMacEntry.switch_id == switch_id)
        if active_only:
            query = query.filter(DLinkMacEntry.is_active == True)
        if port:
            query = query.filter(DLinkMacEntry.port == port)
        if vlan_id:
            query = query.filter(DLinkMacEntry.vlan_id == vlan_id)
        return query.order_by(DLinkMacEntry.last_seen.desc()).offset(offset).limit(limit).all()

    def count_mac_entries(
        self, db: Session, switch_id: int, port: Optional[str] = None,
        vlan_id: Optional[int] = None, active_only: bool = True
    ) -> int:
        query = db.query(DLinkMacEntry).filter(DLinkMacEntry.switch_id == switch_id)
        if active_only:
            query = query.filter(DLinkMacEntry.is_active == True)
        if port:
            query = query.filter(DLinkMacEntry.port == port)
        if vlan_id:
            query = query.filter(DLinkMacEntry.vlan_id == vlan_id)
        return query.count()

    def upsert_mac_entry(
        self, db: Session, switch_id: int, mac_address: str, vlan_id: int,
        port: str, type: str = "dynamic"
    ) -> DLinkMacEntry:
        entry = db.query(DLinkMacEntry).filter(
            DLinkMacEntry.switch_id == switch_id,
            DLinkMacEntry.mac_address == mac_address.lower(),
            DLinkMacEntry.vlan_id == vlan_id,
            DLinkMacEntry.port == port
        ).first()
        if entry:
            entry.last_seen = datetime.utcnow()
            entry.type = type
            entry.is_active = True
        else:
            entry = DLinkMacEntry(
                switch_id=switch_id,
                mac_address=mac_address.lower(),
                vlan_id=vlan_id,
                port=port,
                type=type
            )
            db.add(entry)
        db.flush()
        return entry

    def bulk_upsert_mac_entries(self, db: Session, switch_id: int, entries: List[dict]) -> int:
        """Bulk upsert MAC entries from inventory collection."""
        count = 0
        for e in entries:
            self.upsert_mac_entry(
                db, switch_id,
                e.get("mac_address", "").lower(),
                int(e.get("vlan_id", 1)),
                e.get("port", ""),
                e.get("type", "dynamic")
            )
            count += 1
        return count

    def mark_mac_entries_inactive(self, db: Session, switch_id: int, older_than: datetime) -> int:
        """Mark MAC entries not seen since older_than as inactive."""
        result = db.query(DLinkMacEntry).filter(
            DLinkMacEntry.switch_id == switch_id,
            DLinkMacEntry.is_active == True,
            DLinkMacEntry.last_seen < older_than
        ).update({DLinkMacEntry.is_active: False}, synchronize_session=False)
        return result

    # ---- DLinkVlan ----

    def get_vlans(self, db: Session, switch_id: int) -> List[DLinkVlan]:
        return db.query(DLinkVlan).filter(DLinkVlan.switch_id == switch_id).order_by(DLinkVlan.vlan_id).all()

    def get_vlan(self, db: Session, switch_id: int, vlan_id: int) -> Optional[DLinkVlan]:
        return db.query(DLinkVlan).filter(
            DLinkVlan.switch_id == switch_id,
            DLinkVlan.vlan_id == vlan_id
        ).first()

    def upsert_vlan(
        self, db: Session, switch_id: int, vlan_id: int, name: Optional[str],
        ports_tagged: Optional[str], ports_untagged: Optional[str], ports_forbidden: Optional[str]
    ) -> DLinkVlan:
        vlan = self.get_vlan(db, switch_id, vlan_id)
        if vlan:
            vlan.name = name
            vlan.ports_tagged = ports_tagged
            vlan.ports_untagged = ports_untagged
            vlan.ports_forbidden = ports_forbidden
            vlan.updated_at = datetime.utcnow()
        else:
            vlan = DLinkVlan(
                switch_id=switch_id,
                vlan_id=vlan_id,
                name=name,
                ports_tagged=ports_tagged,
                ports_untagged=ports_untagged,
                ports_forbidden=ports_forbidden
            )
            db.add(vlan)
        db.flush()
        return vlan

    def delete_vlan(self, db: Session, switch_id: int, vlan_id: int) -> bool:
        vlan = self.get_vlan(db, switch_id, vlan_id)
        if not vlan:
            return False
        db.delete(vlan)
        return True

    # ---- DLinkPortVlan ----

    def get_port_vlans(self, db: Session, switch_id: int) -> List[DLinkPortVlan]:
        return db.query(DLinkPortVlan).filter(
            DLinkPortVlan.switch_id == switch_id
        ).order_by(DLinkPortVlan.port).all()

    def get_port_vlan(self, db: Session, switch_id: int, port: str) -> Optional[DLinkPortVlan]:
        return db.query(DLinkPortVlan).filter(
            DLinkPortVlan.switch_id == switch_id,
            DLinkPortVlan.port == port
        ).first()

    def upsert_port_vlan(
        self, db: Session, switch_id: int, port: str, pvid: int,
        allowed_vlans: Optional[str], mode: str
    ) -> DLinkPortVlan:
        pv = self.get_port_vlan(db, switch_id, port)
        if pv:
            pv.pvid = pvid
            pv.allowed_vlans = allowed_vlans
            pv.mode = mode
            pv.updated_at = datetime.utcnow()
        else:
            pv = DLinkPortVlan(
                switch_id=switch_id,
                port=port,
                pvid=pvid,
                allowed_vlans=allowed_vlans,
                mode=mode
            )
            db.add(pv)
        db.flush()
        return pv


# Singleton instance
repository = DLinkRepository()