"""
Zabbix Plugin Sync

Background synchronization classes that pull data from Zabbix
and write to local cache tables.
"""

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.plugins.installed.zabbix.api import SEVERITY_MAP
from app.plugins.installed.zabbix.models import (
    ZabbixEvent,
    ZabbixHost,
    ZabbixProblem,
)

if TYPE_CHECKING:
    from app.plugins.installed.zabbix.api import ZabbixApiClient

logger = logging.getLogger("plugin.zabbix.sync")


class InventorySync:
    """Synchronize host inventory from Zabbix to local cache."""

    def sync(
        self,
        session: Session,
        client: "ZabbixApiClient",
        server_id: int,
    ) -> dict[str, int]:
        """Pull hosts from Zabbix and upsert into zabbix_hosts."""
        raw_hosts = client.get_hosts_sync()
        synced = 0
        skipped = 0

        for h in raw_hosts:
            hostid = str(h.get("hostid", ""))
            if not hostid:
                skipped += 1
                continue

            interfaces = h.get("interfaces", [])
            ip = interfaces[0].get("ip") if interfaces else None
            groups = json.dumps([g.get("name", "") for g in h.get("groups", [])])
            templates = json.dumps([t.get("name", "") for t in h.get("parentTemplates", [])])
            status = "enabled" if h.get("status") == "0" else "disabled"
            # A disabled host is not monitored, so availability is neutral.
            if status == "disabled":
                available = "disabled"
            else:
                # Zabbix 7.0 availability codes: 0=unknown, 1=available, 2=unavailable.
                # The legacy per-interface 'available' field is gone. Only code 2
                # means truly down; 0 (unknown) is normal for SNMP/ICMP/agentless
                # hosts that are up and being monitored, so treat it as available.
                _av = None
                for _k in ("active_available", "passive_available", "available",
                           "available_snmp", "available_http", "available_ipmi",
                           "available_jmx"):
                    if h.get(_k) in (2, "2"):
                        _av = "unavailable"
                        break
                    if h.get(_k) in (0, "0", 1, "1"):
                        _av = "available"
                        break
                available = _av if _av is not None else "available"

            stmt = pg_insert(ZabbixHost).values(
                server_id=server_id,
                zabbix_hostid=hostid,
                host=h.get("host", ""),
                name=h.get("name", ""),
                status=status,
                available=available,
                interface_ip=ip,
                groups_json=groups,
                templates_json=templates,
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["server_id", "zabbix_hostid"],
                set_={
                    "host": h.get("host", ""),
                    "name": h.get("name", ""),
                    "status": status,
                    "available": available,
                    "interface_ip": ip,
                    "groups_json": groups,
                    "templates_json": templates,
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Inventory sync: %d synced, %d skipped", synced, skipped)
        return {"synced": synced, "skipped": skipped}


class ProblemSync:
    """Synchronize active problems from Zabbix to local cache."""

    def sync(
        self,
        session: Session,
        client: "ZabbixApiClient",
        server_id: int,
        limit: int = 100,
    ) -> dict[str, int]:
        """Pull problems and upsert into zabbix_problems."""
        raw_problems = client.get_problems_sync(limit=limit)

        result = session.execute(
            select(ZabbixProblem).where(ZabbixProblem.server_id == server_id)
        )
        existing = {row.zabbix_eventid: row for row in result.scalars()}
        seen_ids: set[str] = set()
        synced = 0

        for p in raw_problems:
            eventid = str(p.get("eventid", ""))
            if not eventid:
                continue
            seen_ids.add(eventid)
            hosts = p.get("hosts", [])
            host = hosts[0].get("host", "") if hosts else ""
            hostid = hosts[0].get("hostid", "") if hosts else ""

            stmt = pg_insert(ZabbixProblem).values(
                server_id=server_id,
                zabbix_eventid=eventid,
                name=p.get("name", ""),
                severity=SEVERITY_MAP.get(int(p.get("severity", 0)), "not_classified"),
                acknowledged=p.get("acknowledged") == "1",
                host=host,
                zabbix_hostid=hostid,
                timestamp=p.get("clock"),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["server_id", "zabbix_eventid"],
                set_={
                    "name": p.get("name", ""),
                    "severity": SEVERITY_MAP.get(int(p.get("severity", 0)), "not_classified"),
                    "acknowledged": p.get("acknowledged") == "1",
                    "host": host,
                    "zabbix_hostid": hostid,
                    "timestamp": p.get("clock"),
                    "resolved_at": None,
                },
            )
            session.execute(stmt)
            synced += 1

        for eventid, row in existing.items():
            if eventid not in seen_ids and row.resolved_at is None:
                row.resolved_at = datetime.now(UTC)

        session.commit()
        logger.info("Problem sync: %d active, %d resolved", synced, len(existing) - len(seen_ids & existing.keys()))
        return {"synced": synced, "total_active": len(seen_ids)}


class EventSync:
    """Synchronize recent events from Zabbix to local cache."""

    def sync(
        self,
        session: Session,
        client: "ZabbixApiClient",
        server_id: int,
        limit: int = 100,
    ) -> dict[str, int]:
        """Pull events and insert into zabbix_events (append-only)."""
        raw_events = client.get_events_sync(limit=limit)
        inserted = 0

        for e in raw_events:
            eventid = str(e.get("eventid", ""))
            if not eventid:
                continue
            hosts = e.get("hosts", [])
            host = hosts[0].get("host", "") if hosts else ""
            hostid = hosts[0].get("hostid", "") if hosts else ""
            status = "PROBLEM" if e.get("value") == "1" else "OK"

            existing = session.execute(
                select(ZabbixEvent).where(
                    ZabbixEvent.server_id == server_id,
                    ZabbixEvent.zabbix_eventid == eventid,
                )
            )
            if existing.scalar_one_or_none():
                continue

            event = ZabbixEvent(
                server_id=server_id,
                zabbix_eventid=eventid,
                name=e.get("name", ""),
                severity=SEVERITY_MAP.get(int(e.get("severity", 0)), "not_classified"),
                status=status,
                host=host,
                zabbix_hostid=hostid,
                timestamp=e.get("clock"),
            )
            session.add(event)
            inserted += 1

        session.commit()
        logger.info("Event sync: %d new events", inserted)
        return {"inserted": inserted}
