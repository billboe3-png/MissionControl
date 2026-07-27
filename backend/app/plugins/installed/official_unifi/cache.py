"""
UniFi Plugin Cache

Provides convenient read access to cached UniFi data.
All queries use synchronous SQLAlchemy sessions.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.plugins.installed.official_unifi.models import (
    UniFiAlert,
    UniFiClient,
    UniFiController,
    UniFiDevice,
    UniFiSite,
    UniFiWirelessNetwork,
)

logger = logging.getLogger("plugin.unifi.cache")


def _controller_to_dict(c: UniFiController) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "url": c.url,
        "controller_type": c.controller_type,
        "enabled": c.enabled,
        "organization_name": c.organization_name,
        "version": c.version,
        "status": c.status,
        "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
        "last_error": c.last_error,
    }


def _site_to_dict(s: UniFiSite) -> dict[str, Any]:
    return {
        "id": s.id,
        "controller_id": s.controller_id,
        "unifi_id": s.unifi_id,
        "name": s.name,
        "description": s.description,
        "timezone": s.timezone,
        "isp_name": s.isp_name,
        "wan_status": s.wan_status,
        "num_devices": s.num_devices,
        "num_clients": s.num_clients,
    }


def _device_to_dict(d: UniFiDevice) -> dict[str, Any]:
    return {
        "id": d.id,
        "controller_id": d.controller_id,
        "site_id": d.site_id,
        "unifi_id": d.unifi_id,
        "name": d.name,
        "model": d.model,
        "serial": d.serial,
        "mac_address": d.mac_address,
        "ip_address": d.ip_address,
        "firmware_version": d.firmware_version,
        "adoption_state": d.adoption_state,
        "status": d.status,
        "uptime_seconds": d.uptime_seconds,
        "cpu_utilization": d.cpu_utilization,
        "memory_utilization": d.memory_utilization,
        "temperature_c": d.temperature_c,
        "device_type": d.device_type,
        "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
    }


def _client_to_dict(c: UniFiClient) -> dict[str, Any]:
    return {
        "id": c.id,
        "controller_id": c.controller_id,
        "site_id": c.site_id,
        "unifi_id": c.unifi_id,
        "hostname": c.hostname,
        "mac_address": c.mac_address,
        "ip_address": c.ip_address,
        "vlan": c.vlan,
        "connected_ap_name": c.connected_ap_name,
        "connected_switch_name": c.connected_switch_name,
        "rx_bytes": c.rx_bytes,
        "tx_bytes": c.tx_bytes,
        "is_wired": c.is_wired,
        "is_guest": c.is_guest,
        "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
    }


def _alert_to_dict(a: UniFiAlert) -> dict[str, Any]:
    return {
        "id": a.id,
        "controller_id": a.controller_id,
        "site_id": a.site_id,
        "unifi_id": a.unifi_id,
        "severity": a.severity,
        "device_name": a.device_name,
        "device_id": a.device_id,
        "message": a.message,
        "timestamp": a.timestamp.isoformat() if a.timestamp else None,
        "is_acknowledged": a.is_acknowledged,
    }


def _wn_to_dict(wn: UniFiWirelessNetwork) -> dict[str, Any]:
    return {
        "id": wn.id,
        "controller_id": wn.controller_id,
        "site_id": wn.site_id,
        "unifi_id": wn.unifi_id,
        "ssid": wn.ssid,
        "security": wn.security,
        "vlan": wn.vlan,
        "is_guest": wn.is_guest,
        "is_hidden": wn.is_hidden,
        "has_alerts": wn.has_alerts,
    }


class CacheManager:
    """Read-only access to cached UniFi data."""

    def get_controllers(self, db: Session) -> list[dict[str, Any]]:
        rows = db.execute(
            select(UniFiController).order_by(UniFiController.name)
        ).scalars().all()
        return [_controller_to_dict(r) for r in rows]

    def get_sites(self, db: Session, controller_id: int | None = None) -> list[dict[str, Any]]:
        stmt = select(UniFiSite)
        if controller_id:
            stmt = stmt.where(UniFiSite.controller_id == controller_id)
        rows = db.execute(stmt.order_by(UniFiSite.name)).scalars().all()
        return [_site_to_dict(r) for r in rows]

    def get_devices(
        self, db: Session, controller_id: int | None = None,
        site_id: str | None = None, device_type: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(UniFiDevice)
        if controller_id:
            stmt = stmt.where(UniFiDevice.controller_id == controller_id)
        if site_id:
            stmt = stmt.where(UniFiDevice.site_id == site_id)
        if device_type:
            stmt = stmt.where(UniFiDevice.device_type == device_type)
        rows = db.execute(stmt.order_by(UniFiDevice.name)).scalars().all()
        return [_device_to_dict(r) for r in rows]

    def get_clients(
        self, db: Session, controller_id: int | None = None,
        site_id: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(UniFiClient)
        if controller_id:
            stmt = stmt.where(UniFiClient.controller_id == controller_id)
        if site_id:
            stmt = stmt.where(UniFiClient.site_id == site_id)
        rows = db.execute(stmt.order_by(UniFiClient.hostname)).scalars().all()
        return [_client_to_dict(r) for r in rows]

    def get_alerts(
        self, db: Session, controller_id: int | None = None,
        site_id: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(UniFiAlert)
        if controller_id:
            stmt = stmt.where(UniFiAlert.controller_id == controller_id)
        if site_id:
            stmt = stmt.where(UniFiAlert.site_id == site_id)
        rows = db.execute(stmt.order_by(UniFiAlert.timestamp.desc())).scalars().all()
        return [_alert_to_dict(r) for r in rows]

    def get_wireless(
        self, db: Session, controller_id: int | None = None,
        site_id: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(UniFiWirelessNetwork)
        if controller_id:
            stmt = stmt.where(UniFiWirelessNetwork.controller_id == controller_id)
        if site_id:
            stmt = stmt.where(UniFiWirelessNetwork.site_id == site_id)
        rows = db.execute(stmt.order_by(UniFiWirelessNetwork.ssid)).scalars().all()
        return [_wn_to_dict(r) for r in rows]

    def get_access_points(self, db: Session, **kwargs: Any) -> list[dict[str, Any]]:
        return self.get_devices(db, device_type="access_point", **kwargs)

    def get_switches(self, db: Session, **kwargs: Any) -> list[dict[str, Any]]:
        return self.get_devices(db, device_type="switch", **kwargs)

    def get_gateways(self, db: Session, **kwargs: Any) -> list[dict[str, Any]]:
        return self.get_devices(db, device_type="gateway", **kwargs)

    def get_summary(self, db: Session) -> dict[str, Any]:
        controller_count = (db.execute(
            select(func.count(UniFiController.id))
        ).scalar()) or 0

        site_count = (db.execute(
            select(func.count(UniFiSite.id))
        ).scalar()) or 0

        device_count = (db.execute(
            select(func.count(UniFiDevice.id))
        ).scalar()) or 0

        online_devices = (db.execute(
            select(func.count(UniFiDevice.id)).where(UniFiDevice.status == "online")
        ).scalar()) or 0

        offline_devices = device_count - online_devices

        client_count = (db.execute(
            select(func.count(UniFiClient.id))
        ).scalar()) or 0

        alert_count = (db.execute(
            select(func.count(UniFiAlert.id))
        ).scalar()) or 0

        unack_alerts = (db.execute(
            select(func.count(UniFiAlert.id)).where(UniFiAlert.is_acknowledged.is_(False))
        ).scalar()) or 0

        wireless_count = (db.execute(
            select(func.count(UniFiWirelessNetwork.id))
        ).scalar()) or 0

        ap_count = (db.execute(
            select(func.count(UniFiDevice.id)).where(UniFiDevice.device_type == "access_point")
        ).scalar()) or 0

        switch_count = (db.execute(
            select(func.count(UniFiDevice.id)).where(UniFiDevice.device_type == "switch")
        ).scalar()) or 0

        gateway_count = (db.execute(
            select(func.count(UniFiDevice.id)).where(UniFiDevice.device_type == "gateway")
        ).scalar()) or 0

        online_ap = (db.execute(
            select(func.count(UniFiDevice.id)).where(
                UniFiDevice.device_type == "access_point",
                UniFiDevice.status == "online",
            )
        ).scalar()) or 0

        online_switch = (db.execute(
            select(func.count(UniFiDevice.id)).where(
                UniFiDevice.device_type == "switch",
                UniFiDevice.status == "online",
            )
        ).scalar()) or 0

        online_gateway = (db.execute(
            select(func.count(UniFiDevice.id)).where(
                UniFiDevice.device_type == "gateway",
                UniFiDevice.status == "online",
            )
        ).scalar()) or 0

        healthy_controllers = (db.execute(
            select(func.count(UniFiController.id)).where(UniFiController.status == "healthy")
        ).scalar()) or 0

        return {
            "controller_count": controller_count,
            "controllers_healthy": healthy_controllers,
            "site_count": site_count,
            "device_count": device_count,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "client_count": client_count,
            "alert_count": alert_count,
            "unacknowledged_alerts": unack_alerts,
            "wireless_network_count": wireless_count,
            "ap_count": ap_count,
            "online_ap": online_ap,
            "switch_count": switch_count,
            "online_switch": online_switch,
            "gateway_count": gateway_count,
            "online_gateway": online_gateway,
        }

    def get_devices_by_status(self, db: Session) -> dict[str, int]:
        rows = db.execute(
            select(UniFiDevice.status, func.count(UniFiDevice.id))
            .group_by(UniFiDevice.status)
        ).all()
        return {row[0]: row[1] for row in rows}

    def get_devices_by_type(self, db: Session) -> dict[str, int]:
        rows = db.execute(
            select(UniFiDevice.device_type, func.count(UniFiDevice.id))
            .group_by(UniFiDevice.device_type)
        ).all()
        return {row[0]: row[1] for row in rows}

    def get_last_sync(self, db: Session) -> str | None:
        latest = db.execute(
            select(func.max(UniFiController.last_sync_at))
        ).scalar()
        return latest.isoformat() if latest else None


cache_manager = CacheManager()
