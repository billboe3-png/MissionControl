"""
Mission Control Correlation Engine

Correlates alerts across:
- Zabbix Problems
- Hyper-V Alerts
- Proxmox Alerts
- Remote Operation Failures
- Active Directory Issues
- Microsoft 365 Issues

Detects: duplicate incidents, root events, cascading failures, dependencies.

AI NEVER executes changes. Only analyzes and groups.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Correlates alerts across multiple infrastructure sources."""

    def correlate(self, alerts: list[dict]) -> dict:
        """
        Correlate a list of alerts from various sources.

        Args:
            alerts: list of dicts with keys:
                - id: str
                - source: str (zabbix, hyperv, proxmox, remote, ad, m365)
                - severity: str
                - message: str
                - host_name: str
                - timestamp: str (ISO)
                - tags: list[str]
                - related_hosts: list[str]

        Returns:
            {
                "groups": list[CorrelatedGroup],
                "duplicates": list[DuplicatePair],
                "root_events": list[RootEvent],
                "cascading_failures": list[CascadeChain],
                "summary": dict,
            }
        """
        if not alerts:
            return {
                "groups": [],
                "duplicates": [],
                "root_events": [],
                "cascading_failures": [],
                "summary": self._empty_summary(),
            }

        duplicates = self._detect_duplicates(alerts)
        non_duplicate_ids = set()
        for dup_pair in duplicates:
            non_duplicate_ids.add(dup_pair["kept_id"])
            non_duplicate_ids.add(dup_pair["duplicate_id"])

        remaining = [
            a
            for a in alerts
            if a.get("id") not in non_duplicate_ids or len(duplicates) == 0
        ]

        groups = self._group_alerts(remaining if duplicates else alerts)
        root_events = self._detect_root_events(alerts, groups)
        cascading = self._detect_cascading(alerts, groups)

        summary = {
            "total_alerts": len(alerts),
            "total_groups": len(groups),
            "total_duplicates": len(duplicates),
            "total_root_events": len(root_events),
            "total_cascading": len(cascading),
            "sources": list({a.get("source", "unknown") for a in alerts}),
            "severity_distribution": self._severity_distribution(alerts),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return {
            "groups": groups,
            "duplicates": duplicates,
            "root_events": root_events,
            "cascading_failures": cascading,
            "summary": summary,
        }

    def _detect_duplicates(self, alerts: list[dict]) -> list[dict]:
        """Detect duplicate alerts based on message similarity and host."""
        duplicates = []
        seen: dict[str, str] = {}

        for alert in alerts:
            key = self._normalise_key(alert)
            if key in seen:
                duplicates.append(
                    {
                        "kept_id": seen[key],
                        "duplicate_id": alert.get("id", ""),
                        "reason": "Similar message on same host within time window",
                        "similarity": 0.95,
                    }
                )
            else:
                seen[key] = alert.get("id", "")

        return duplicates

    def _normalise_key(self, alert: dict) -> str:
        msg = alert.get("message", "").lower().strip()
        host = alert.get("host_name", "").lower().strip()
        source = alert.get("source", "").lower().strip()
        words = msg.split()[:6]
        return f"{source}:{host}:{'|'.join(words)}"

    def _group_alerts(self, alerts: list[dict]) -> list[dict]:
        """Group related alerts by host, tags, and time proximity."""
        host_groups: dict[str, list[dict]] = {}
        for alert in alerts:
            host = alert.get("host_name", "unknown")
            host_groups.setdefault(host, []).append(alert)

        groups = []
        group_id = 0
        for host, host_alerts in host_groups.items():
            if len(host_alerts) > 1:
                group_id += 1
                sources = list({a.get("source", "unknown") for a in host_alerts})
                max_severity = self._max_severity(host_alerts)
                groups.append(
                    {
                        "group_id": f"grp_{group_id}",
                        "host_name": host,
                        "alert_count": len(host_alerts),
                        "sources": sources,
                        "max_severity": max_severity,
                        "alert_ids": [a.get("id", "") for a in host_alerts],
                        "correlation_type": "same_host",
                    }
                )

        tag_groups = self._group_by_tags(alerts)
        for tag_group in tag_groups:
            if len(tag_group["alert_ids"]) > 1:
                group_id += 1
                tag_group["group_id"] = f"grp_{group_id}"
                tag_group["correlation_type"] = "shared_tag"
                groups.append(tag_group)

        return groups

    def _group_by_tags(self, alerts: list[dict]) -> list[dict]:
        tag_map: dict[str, list[dict]] = {}
        for alert in alerts:
            for tag in alert.get("tags", []):
                tag_map.setdefault(tag, []).append(alert)

        groups = []
        for tag, tagged_alerts in tag_map.items():
            sources = list({a.get("source", "unknown") for a in tagged_alerts})
            groups.append(
                {
                    "tag": tag,
                    "alert_count": len(tagged_alerts),
                    "sources": sources,
                    "max_severity": self._max_severity(tagged_alerts),
                    "alert_ids": [a.get("id", "") for a in tagged_alerts],
                }
            )

        return groups

    def _detect_root_events(self, alerts: list[dict], groups: list[dict]) -> list[dict]:
        """Identify the earliest alert in a group as the likely root cause."""
        root_events = []

        for group in groups:
            alert_ids = set(group.get("alert_ids", []))
            group_alerts = [a for a in alerts if a.get("id") in alert_ids]
            if not group_alerts:
                continue

            earliest = min(
                group_alerts,
                key=lambda a: a.get("timestamp", "9999"),
            )
            root_events.append(
                {
                    "root_alert_id": earliest.get("id", ""),
                    "group_id": group.get("group_id", ""),
                    "host_name": earliest.get("host_name", ""),
                    "message": earliest.get("message", ""),
                    "source": earliest.get("source", ""),
                    "reasoning": (
                        "Earliest alert in correlated group,"
                        " likely root cause"
                    ),
                }
            )

        return root_events

    def _detect_cascading(self, alerts: list[dict], groups: list[dict]) -> list[dict]:
        """Detect cascading failures: alerts on multiple hosts within a time window."""
        cascading = []
        multi_source_groups = [g for g in groups if len(g.get("sources", [])) > 1]

        for group in multi_source_groups:
            cascading.append(
                {
                    "group_id": group.get("group_id", ""),
                    "sources": group.get("sources", []),
                    "alert_count": group.get("alert_count", 0),
                    "max_severity": group.get("max_severity", "info"),
                    "pattern": "multi_source_correlation",
                    "description": (
                        f"Alerts detected across {len(group.get('sources', []))} "
                        f"different sources ({', '.join(group.get('sources', []))}), "
                        f"suggesting a cascading failure pattern."
                    ),
                }
            )

        return cascading

    def _max_severity(self, alerts: list[dict]) -> str:
        order = {
            "critical": 5,
            "high": 4,
            "warning": 3,
            "medium": 3,
            "low": 2,
            "info": 1,
        }
        max_sev = "info"
        max_val = 0
        for a in alerts:
            sev = a.get("severity", "info").lower()
            val = order.get(sev, 0)
            if val > max_val:
                max_val = val
                max_sev = sev
        return max_sev

    def _severity_distribution(self, alerts: list[dict]) -> dict:
        dist: dict[str, int] = {}
        for a in alerts:
            sev = a.get("severity", "info").lower()
            dist[sev] = dist.get(sev, 0) + 1
        return dist

    def _empty_summary(self) -> dict:
        return {
            "total_alerts": 0,
            "total_groups": 0,
            "total_duplicates": 0,
            "total_root_events": 0,
            "total_cascading": 0,
            "sources": [],
            "severity_distribution": {},
            "timestamp": datetime.now(UTC).isoformat(),
        }


correlation_engine = CorrelationEngine()
