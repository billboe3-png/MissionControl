"""
Mission Control Incident Classifier

Classifies incidents by criticality, business impact, and priority.
Evaluates affected systems, host importance, alert frequency,
and historical failures.

AI NEVER executes changes. Only classifies and recommends.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class Criticality(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BusinessImpact(StrEnum):
    CATASTROPHIC = "catastrophic"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    NONE = "none"


class IncidentPriority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"


CRITICALITY_WEIGHT = {
    Criticality.CRITICAL: 1.0,
    Criticality.HIGH: 0.8,
    Criticality.MEDIUM: 0.5,
    Criticality.LOW: 0.3,
    Criticality.INFO: 0.1,
}

BUSINESS_IMPACT_WEIGHT = {
    BusinessImpact.CATASTROPHIC: 1.0,
    BusinessImpact.MAJOR: 0.8,
    BusinessImpact.MODERATE: 0.5,
    BusinessImpact.MINOR: 0.3,
    BusinessImpact.NONE: 0.1,
}

IMPORTANCE_WEIGHT = {
    "domain_controller": 1.0,
    "database": 0.9,
    "exchange": 0.85,
    "file_server": 0.8,
    "web_server": 0.7,
    "hyperv_host": 0.75,
    "proxmox_host": 0.7,
    "zabbix_server": 0.6,
    "workstation": 0.3,
    "unknown": 0.5,
}


class IncidentClassifier:
    """Classifies incidents and assigns priorities."""

    def classify(self, incident: dict) -> dict:
        """
        Classify an incident and produce priority, confidence, reasoning.

        Args:
            incident: dict with keys:
                - source: str (zabbix, hyperv, proxmox, remote, ad, m365)
                - severity: str (critical, high, medium, low, info, warning)
                - message: str
                - affected_systems: list[str]
                - host_importance: str
                - alert_frequency: int (occurrences in last 24h)
                - historical_failures: int (similar incidents in last 30d)
                - host_name: str
                - tags: list[str]

        Returns:
            {
                "criticality": str,
                "business_impact": str,
                "priority": str,
                "confidence": dict,
                "reasoning": str,
                "suggested_actions": list[str],
            }
        """
        source = incident.get("source", "unknown")
        severity = incident.get("severity", "info").lower()
        message = incident.get("message", "")
        affected_systems = incident.get("affected_systems", [])
        host_importance = incident.get("host_importance", "unknown")
        alert_frequency = incident.get("alert_frequency", 0)
        historical_failures = incident.get("historical_failures", 0)
        host_name = incident.get("host_name", "Unknown")

        criticality = self._determine_criticality(severity, alert_frequency)
        business_impact = self._determine_business_impact(
            criticality, affected_systems, host_importance
        )
        priority = self._determine_priority(
            criticality, business_impact, alert_frequency, historical_failures
        )
        suggested_actions = self._suggest_actions(
            source, criticality, affected_systems, message
        )
        reasoning = self._build_reasoning(
            source,
            criticality,
            business_impact,
            host_name,
            affected_systems,
            alert_frequency,
            historical_failures,
        )

        from app.ai.confidence_engine import confidence_engine

        confidence = confidence_engine.calculate(
            data_completeness=self._data_completeness_score(incident),
            pattern_match=self._pattern_match_score(severity, alert_frequency),
            source_reliability=self._source_reliability(source),
            historical_accuracy=(
                min(1.0, historical_failures / 10) if historical_failures > 0 else 0.4
            ),
        )

        return {
            "source": source,
            "host_name": host_name,
            "message": message,
            "criticality": criticality,
            "business_impact": business_impact,
            "priority": priority,
            "confidence": confidence,
            "reasoning": reasoning,
            "suggested_actions": suggested_actions,
        }

    def classify_batch(self, incidents: list[dict]) -> list[dict]:
        """Classify multiple incidents."""
        return [self.classify(inc) for inc in incidents]

    def _determine_criticality(self, severity: str, frequency: int) -> str:
        severity_map = {
            "critical": Criticality.CRITICAL,
            "high": Criticality.HIGH,
            "warning": Criticality.MEDIUM,
            "medium": Criticality.MEDIUM,
            "low": Criticality.LOW,
            "info": Criticality.INFO,
        }
        base = severity_map.get(severity, Criticality.MEDIUM)
        if frequency > 10 and base != Criticality.CRITICAL:
            base = Criticality.HIGH
        elif frequency > 5 and base in (Criticality.LOW, Criticality.INFO):
            base = Criticality.MEDIUM
        return base

    def _determine_business_impact(
        self, criticality: str, affected_systems: list, host_importance: str
    ) -> str:
        imp_weight = IMPORTANCE_WEIGHT.get(host_importance, 0.5)
        if affected_systems:
            systems_factor = min(1.0, len(affected_systems) / 5)
        else:
            systems_factor = 0.2

        combined = (
            CRITICALITY_WEIGHT.get(Criticality(criticality), 0.5) * 0.5
            + imp_weight * 0.3
            + systems_factor * 0.2
        )

        if combined >= 0.8:
            return BusinessImpact.CATASTROPHIC
        if combined >= 0.6:
            return BusinessImpact.MAJOR
        if combined >= 0.4:
            return BusinessImpact.MODERATE
        if combined >= 0.2:
            return BusinessImpact.MINOR
        return BusinessImpact.NONE

    def _determine_priority(
        self, criticality: str, business_impact: str, frequency: int, historical: int
    ) -> str:
        score = (
            CRITICALITY_WEIGHT.get(Criticality(criticality), 0.5) * 0.4
            + BUSINESS_IMPACT_WEIGHT.get(BusinessImpact(business_impact), 0.5) * 0.3
            + min(1.0, frequency / 10) * 0.15
            + min(1.0, historical / 10) * 0.15
        )

        if score >= 0.8:
            return IncidentPriority.P1
        if score >= 0.6:
            return IncidentPriority.P2
        if score >= 0.4:
            return IncidentPriority.P3
        if score >= 0.2:
            return IncidentPriority.P4
        return IncidentPriority.P5

    def _suggest_actions(
        self, source: str, criticality: str, systems: list, message: str
    ) -> list[str]:
        actions = []
        msg_lower = message.lower()

        if criticality in ("critical", "high"):
            actions.append("Review incident immediately")

        if "disk" in msg_lower or "storage" in msg_lower:
            actions.append("Check disk space and clean up if needed")
        if "memory" in msg_lower or "ram" in msg_lower:
            actions.append("Investigate memory usage")
        if "cpu" in msg_lower or "load" in msg_lower:
            actions.append("Check CPU-intensive processes")
        if "network" in msg_lower or "connection" in msg_lower:
            actions.append("Verify network connectivity")
        if "dns" in msg_lower:
            actions.append("Check DNS resolution")
        if "replication" in msg_lower:
            actions.append("Investigate replication status")
        if "backup" in msg_lower:
            actions.append("Verify backup status")
        if "login" in msg_lower or "auth" in msg_lower:
            actions.append("Review authentication logs")
        if "service" in msg_lower or "restart" in msg_lower:
            actions.append("Consider restarting affected service")
        if "vm" in msg_lower or "virtual" in msg_lower:
            actions.append("Check virtual machine status")

        source_actions = {
            "zabbix": "Review Zabbix problem details",
            "hyperv": "Check Hyper-V host and VM health",
            "proxmox": "Check Proxmox host and CT/VM health",
            "remote": "Verify remote host accessibility",
            "ad": "Review Active Directory replication and health",
            "m365": "Check Microsoft 365 service health",
        }
        if source in source_actions:
            actions.append(source_actions[source])

        if not actions:
            actions.append("Investigate the reported issue")

        return actions

    def _build_reasoning(
        self,
        source,
        criticality,
        business_impact,
        host_name,
        systems,
        frequency,
        historical,
    ) -> str:
        parts = [
            f"Incident on {host_name} from {source}.",
            f"Criticality: {criticality}.",
            f"Business impact: {business_impact}.",
        ]
        if systems:
            parts.append(f"Affected systems: {', '.join(systems)}.")
        if frequency > 0:
            parts.append(f"Occurred {frequency} times in the last 24 hours.")
        if historical > 0:
            parts.append(f"Similar incidents: {historical} in the last 30 days.")
        return " ".join(parts)

    def _data_completeness_score(self, incident: dict) -> float:
        fields = ["source", "severity", "message", "host_name", "affected_systems"]
        present = sum(1 for f in fields if incident.get(f))
        return present / len(fields)

    def _pattern_match_score(self, severity: str, frequency: int) -> float:
        sev_score = {
            "critical": 0.9,
            "high": 0.7,
            "warning": 0.5,
            "medium": 0.5,
            "low": 0.3,
            "info": 0.1,
        }
        base = sev_score.get(severity, 0.5)
        freq_bonus = min(0.2, frequency * 0.02)
        return min(1.0, base + freq_bonus)

    def _source_reliability(self, source: str) -> float:
        reliability = {
            "zabbix": 0.9,
            "hyperv": 0.85,
            "proxmox": 0.8,
            "remote": 0.7,
            "ad": 0.85,
            "m365": 0.8,
        }
        return reliability.get(source, 0.5)


incident_classifier = IncidentClassifier()
