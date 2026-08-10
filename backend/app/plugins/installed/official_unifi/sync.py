"""
UniFi Plugin Sync

Background synchronization classes that pull data from UniFi controllers
and write to local cache tables.
"""

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.plugins.installed.official_unifi.models import (
    UniFiAlert,
    UniFiClient,
    UniFiController,
    UniFiDevice,
    UniFiSite,
    UniFiWirelessNetwork,
)

logger = logging.getLogger("plugin.unifi.sync")


def _extract_items(data: Any) -> list:
    """Extract items from UniFi API response."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", data.get("sites", []))
    return []


class ControllerSync:
    """Synchronize controller info to local cache."""

    def sync(self, session: Session, client: Any, controller_id: int) -> dict[str, int]:
        ctrl = session.get(UniFiController, controller_id)
        if ctrl:
            ctrl.status = "healthy"
            ctrl.last_sync_at = datetime.now(UTC)
            ctrl.last_error = None
        session.commit()
        return {"synced": 1}


class SiteSync:
    """Synchronize sites from UniFi API to local cache."""

    def sync(self, session: Session, client: Any, controller_id: int) -> dict[str, int]:
        raw_sites = client.get_sites_sync()
        items = _extract_items(raw_sites)
        synced = 0

        for s in items:
            unifi_id = str(s.get("_id", s.get("id", "")))
            if not unifi_id:
                continue

            name = s.get("name", s.get("desc", "Unknown"))
            desc = s.get("desc", s.get("description", ""))
            tz = s.get("timezone", "")
            isp = s.get("health", {}).get("wan", {}).get("isp_name", "") if isinstance(s.get("health"), dict) else ""
            wan_status = "unknown"

            stmt = select(UniFiSite).where(
                UniFiSite.controller_id == controller_id,
                UniFiSite.unifi_id == unifi_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.name = name
                existing.description = desc
                existing.timezone = tz or None
                existing.isp_name = isp or None
                existing.wan_status = wan_status
            else:
                session.add(UniFiSite(
                    controller_id=controller_id,
                    unifi_id=unifi_id,
                    name=name,
                    description=desc or None,
                    timezone=tz or None,
                    isp_name=isp or None,
                    wan_status=wan_status,
                ))
            synced += 1

        session.commit()
        logger.info("Site sync: %d sites synced", synced)
        return {"synced": synced}


class DeviceSync:
    """Synchronize devices from UniFi API to local cache."""

    DEVICE_TYPE_MAP: ClassVar[dict[str, str]] = {
        "usw": "switch",
        "uap": "access_point",
        "udm": "gateway",
        "udr": "gateway",
        "uxg": "gateway",
        "usg": "gateway",
        "udm-pro": "gateway",
        "udm-se": "gateway",
        "usw-pro": "switch",
        "usw-lite": "switch",
        "uos": "gateway",
        "u7": "access_point",
        "u6": "access_point",
        "u5": "access_point",
    }

    @staticmethod
    def _classify_device_type(d: dict) -> str:
        model = (d.get("model") or "").lower().strip()
        # Try prefix matching (first word before space or dash)
        for sep in (" ", "-"):
            prefix = model.split(sep)[0]
            if prefix in DeviceSync.DEVICE_TYPE_MAP:
                return DeviceSync.DEVICE_TYPE_MAP[prefix]
        # Fallback: full model match
        if model in DeviceSync.DEVICE_TYPE_MAP:
            return DeviceSync.DEVICE_TYPE_MAP[model]
        # Cloud console detection
        if d.get("isConsole") or d.get("productLine") == "console":
            return "gateway"
        return "unknown"

    def sync(self, session: Session, client: Any, controller_id: int) -> dict[str, int]:
        raw_devices = client.get_devices_sync()
        items = _extract_items(raw_devices)
        synced = 0

        for d in items:
            unifi_id = str(d.get("_id", d.get("id", "")))
            if not unifi_id:
                continue

            name = d.get("name", d.get("display_name", "Unknown"))
            model = d.get("model", "unknown")
            serial = d.get("serial", "")
            mac = d.get("mac", "")
            ip = d.get("ip", "")
            fw = d.get("version", d.get("firmware_version", ""))
            adoption = d.get("adoption", "pending")
            if isinstance(adoption, bool):
                adoption = "adopted" if adoption else "pending"
            online = d.get("state", 0)
            status = "online" if online == 1 else "offline"
            uptime = int(d.get("up_since", 0) or 0)
            cpu = float(d.get("system_stats", {}).get("cpu", 0) or 0)
            mem = float(d.get("system_stats", {}).get("mem", 0) or 0)
            temp = float(d.get("system_stats", {}).get("temperatures", [{}])[0].get("value", 0) or 0) if d.get("system_stats", {}).get("temperatures") else 0
            site_id = str(d.get("site_id", d.get("site", "")))
            dev_type = self._classify_device_type(d)

            stmt = select(UniFiDevice).where(
                UniFiDevice.controller_id == controller_id,
                UniFiDevice.unifi_id == unifi_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.name = name
                existing.model = model
                existing.serial = serial or None
                existing.mac_address = mac or None
                existing.ip_address = ip or None
                existing.firmware_version = fw or None
                existing.adoption_state = adoption
                existing.status = status
                existing.uptime_seconds = uptime
                existing.cpu_utilization = cpu
                existing.memory_utilization = mem
                existing.temperature_c = temp
                existing.site_id = site_id
                existing.device_type = dev_type
                existing.last_seen_at = datetime.now(UTC)
            else:
                session.add(UniFiDevice(
                    controller_id=controller_id,
                    unifi_id=unifi_id,
                    name=name,
                    model=model,
                    serial=serial or None,
                    mac_address=mac or None,
                    ip_address=ip or None,
                    firmware_version=fw or None,
                    adoption_state=adoption,
                    status=status,
                    uptime_seconds=uptime,
                    cpu_utilization=cpu,
                    memory_utilization=mem,
                    temperature_c=temp,
                    site_id=site_id,
                    device_type=dev_type,
                    last_seen_at=datetime.now(UTC),
                ))
            synced += 1

        session.commit()
        logger.info("Device sync: %d devices synced", synced)
        return {"synced": synced}


class ClientSync:
    """Synchronize clients from UniFi API to local cache."""

    def sync(self, session: Session, client: Any, controller_id: int) -> dict[str, int]:
        raw_clients = client.get_clients_sync()
        items = _extract_items(raw_clients)
        synced = 0

        for c in items:
            unifi_id = str(c.get("_id", c.get("id", "")))
            if not unifi_id:
                continue

            hostname = c.get("hostname", c.get("name", ""))
            mac = c.get("mac", "")
            ip = c.get("ip", "")
            vlan = str(c.get("vlan", ""))
            ap_name = c.get("ap_name", "")
            sw_name = c.get("sw_name", "")
            rx = int(c.get("rx_bytes", 0) or 0)
            tx = int(c.get("tx_bytes", 0) or 0)
            is_wired = c.get("is_wired", False)
            is_guest = c.get("is_guest", False)
            site_id = str(c.get("site_id", c.get("site", "")))

            stmt = select(UniFiClient).where(
                UniFiClient.controller_id == controller_id,
                UniFiClient.unifi_id == unifi_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.hostname = hostname or None
                existing.mac_address = mac
                existing.ip_address = ip or None
                existing.vlan = vlan or None
                existing.connected_ap_name = ap_name or None
                existing.connected_switch_name = sw_name or None
                existing.rx_bytes = rx
                existing.tx_bytes = tx
                existing.is_wired = is_wired
                existing.is_guest = is_guest
                existing.site_id = site_id
                existing.last_seen_at = datetime.now(UTC)
            else:
                session.add(UniFiClient(
                    controller_id=controller_id,
                    unifi_id=unifi_id,
                    hostname=hostname or None,
                    mac_address=mac,
                    ip_address=ip or None,
                    vlan=vlan or None,
                    connected_ap_name=ap_name or None,
                    connected_switch_name=sw_name or None,
                    rx_bytes=rx,
                    tx_bytes=tx,
                    is_wired=is_wired,
                    is_guest=is_guest,
                    site_id=site_id,
                    last_seen_at=datetime.now(UTC),
                ))
            synced += 1

        session.commit()
        logger.info("Client sync: %d clients synced", synced)
        return {"synced": synced}


class AlertSync:
    """Synchronize alerts from UniFi API to local cache."""

    def sync(self, session: Session, client: Any, controller_id: int) -> dict[str, int]:
        raw_alerts = client.get_alerts_sync()
        items = _extract_items(raw_alerts)
        synced = 0

        for a in items:
            unifi_id = str(a.get("_id", a.get("id", "")))
            if not unifi_id:
                continue

            severity = a.get("severity", "info")
            dev_name = a.get("device_name", a.get("hostname", ""))
            dev_id = a.get("device_id", a.get("key", ""))
            msg = a.get("msg", a.get("message", ""))
            ts_str = a.get("time", a.get("timestamp", ""))
            acked = a.get("acknowledged", False)
            site_id = str(a.get("site_id", a.get("site", "")))

            ts = None
            if ts_str:
                with contextlib.suppress(ValueError, TypeError):
                    ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))

            stmt = select(UniFiAlert).where(
                UniFiAlert.controller_id == controller_id,
                UniFiAlert.unifi_id == unifi_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if not existing:
                session.add(UniFiAlert(
                    controller_id=controller_id,
                    unifi_id=unifi_id,
                    site_id=site_id,
                    severity=severity,
                    device_name=dev_name or None,
                    device_id=str(dev_id) if dev_id else None,
                    message=msg,
                    timestamp=ts,
                    is_acknowledged=acked,
                ))
            synced += 1

        session.commit()
        logger.info("Alert sync: %d alerts synced", synced)
        return {"synced": synced}


class NetworkSync:
    """Synchronize wireless network configuration from UniFi API to local cache."""

    def sync(self, session: Session, client: Any, controller_id: int) -> dict[str, int]:
        raw_networks = client.get_networks_sync()
        items = _extract_items(raw_networks)
        synced = 0

        for n in items:
            unifi_id = str(n.get("_id", n.get("id", "")))
            if not unifi_id:
                continue

            ssid = n.get("name", n.get("ssid", ""))
            security = n.get("security", n.get("wpasec", "open"))
            vlan = str(n.get("vlan", ""))
            is_guest = n.get("is_guest", False)
            is_hidden = n.get("is_hidden", False)
            has_alerts = n.get("has_alerts", False)
            site_id = str(n.get("site_id", n.get("site", "")))

            stmt = select(UniFiWirelessNetwork).where(
                UniFiWirelessNetwork.controller_id == controller_id,
                UniFiWirelessNetwork.unifi_id == unifi_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.ssid = ssid
                existing.security = security
                existing.vlan = vlan or None
                existing.is_guest = is_guest
                existing.is_hidden = is_hidden
                existing.has_alerts = has_alerts
            else:
                session.add(UniFiWirelessNetwork(
                    controller_id=controller_id,
                    unifi_id=unifi_id,
                    site_id=site_id,
                    ssid=ssid,
                    security=security,
                    vlan=vlan or None,
                    is_guest=is_guest,
                    is_hidden=is_hidden,
                    has_alerts=has_alerts,
                ))
            synced += 1

        session.commit()
        logger.info("Network sync: %d wireless networks synced", synced)
        return {"synced": synced}
