"""
Mission Control Recommendation Engine

Generates operational recommendations based on classified incidents,
correlated alerts, and infrastructure data.

Every recommendation includes: confidence, risk, reason, estimated impact.
AI NEVER executes changes. Recommendations require human approval.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class RiskLevel(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


RECOMMENDATION_TEMPLATES = {
    "restart_service": {
        "action": "Restart service",
        "category": "remediation",
        "risk": "medium",
        "estimated_impact": "Restarts the affected service to clear transient errors",
    },
    "health_check": {
        "action": "Run health check",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Gathers current health status without making changes",
    },
    "free_disk_space": {
        "action": "Free disk space",
        "category": "remediation",
        "risk": "medium",
        "estimated_impact": "Removes temporary files to reclaim disk space",
    },
    "check_dns": {
        "action": "Check DNS resolution",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Verifies DNS configuration and name resolution",
    },
    "investigate_replication": {
        "action": "Investigate replication status",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Checks replication health across domain controllers",
    },
    "verify_backups": {
        "action": "Verify backup status",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Confirms backups are current and restorable",
    },
    "restart_vm": {
        "action": "Restart virtual machine",
        "category": "remediation",
        "risk": "high",
        "estimated_impact": "Restarts the VM which causes brief service interruption",
    },
    "check_hyper_v_storage": {
        "action": "Check Hyper-V storage",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Validates Hyper-V storage health and capacity",
    },
    "review_failed_logins": {
        "action": "Review failed login activity",
        "category": "security",
        "risk": "low",
        "estimated_impact": (
            "Identifies potential brute-force or "
            "unauthorized access attempts"
        ),
    },
    "investigate_cpu_usage": {
        "action": "Investigate CPU usage",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Identifies processes consuming excessive CPU",
    },
    "check_network_connectivity": {
        "action": "Check network connectivity",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Verifies network path and latency to affected systems",
    },
    "scale_resources": {
        "action": "Scale resources",
        "category": "capacity",
        "risk": "high",
        "estimated_impact": "Increases allocated resources (CPU/memory/storage)",
    },
    "review_m365_service_health": {
        "action": "Review Microsoft 365 service health",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": "Checks M365 service status and advisories",
    },
    "investigate_ad_replication": {
        "action": "Investigate AD replication",
        "category": "diagnostic",
        "risk": "low",
        "estimated_impact": (
            "Checks Active Directory replication "
            "status between domain controllers"
        ),
    },
}


class RecommendationEngine:
    """Generates operational recommendations."""

    def generate(
        self, classified_incident: dict, context: dict | None = None
    ) -> list[dict]:
        """
        Generate recommendations for a classified incident.

        Args:
            classified_incident: output from IncidentClassifier.classify()
            context: optional additional context (system health, etc.)

        Returns:
            list of recommendation dicts, each with:
                - id: str
                - action: str
                - category: str
                - confidence: dict
                - risk: str
                - reason: str
                - estimated_impact: str
                - explanation: str
                - requires_approval: bool
        """
        source = classified_incident.get("source", "unknown")
        criticality = classified_incident.get("criticality", "medium")
        message = classified_incident.get("message", "")
        host_name = classified_incident.get("host_name", "Unknown")
        affected = classified_incident.get("affected_systems", [])
        msg_lower = message.lower()

        template_keys = self._select_templates(source, criticality, msg_lower, affected)
        recommendations = []

        for idx, template_key in enumerate(template_keys):
            template = RECOMMENDATION_TEMPLATES[template_key]
            confidence = self._calculate_recommendation_confidence(
                template_key, criticality, classified_incident.get("confidence", {})
            )
            explanation = self._build_explanation(
                template, host_name, message, criticality
            )

            recommendations.append(
                {
                    "id": f"rec_{host_name}_{template_key}_{idx}",
                    "action": template["action"],
                    "template_key": template_key,
                    "host_name": host_name,
                    "source": source,
                    "category": template["category"],
                    "confidence": confidence,
                    "risk": template["risk"],
                    "reason": (
                        f"Based on {criticality} incident"
                        f" from {source}: "
                        f"{message[:100]}"
                    ),
                    "estimated_impact": template["estimated_impact"],
                    "explanation": explanation,
                    "requires_approval": True,
                }
            )

        if not recommendations:
            from app.ai.confidence_engine import confidence_engine

            recommendations.append(
                {
                    "id": f"rec_{host_name}_investigate_0",
                    "action": "Investigate the reported issue",
                    "template_key": "health_check",
                    "category": "diagnostic",
                    "confidence": confidence_engine.calculate(
                        data_completeness=0.3,
                        pattern_match=0.3,
                        source_reliability=0.5,
                    ),
                    "risk": "low",
                    "reason": f"General incident from {source}: {message[:100]}",
                    "estimated_impact": (
                        "Initial investigation to understand"
                        " the scope of the issue"
                    ),
                    "explanation": f"The system detected an issue on {host_name}. "
                    f"Manual investigation is recommended.",
                    "requires_approval": True,
                }
            )

        return recommendations

    def generate_batch(self, classified_incidents: list[dict]) -> dict:
        """Generate recommendations for multiple incidents."""
        all_recs = []
        for inc in classified_incidents:
            recs = self.generate(inc)
            all_recs.extend(recs)

        by_risk = {"low": [], "medium": [], "high": [], "critical": []}
        for rec in all_recs:
            risk = rec.get("risk", "low")
            by_risk.setdefault(risk, []).append(rec)

        return {
            "recommendations": all_recs,
            "total": len(all_recs),
            "by_risk": {k: len(v) for k, v in by_risk.items()},
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _select_templates(
        self, source: str, criticality: str, message: str, affected: list
    ) -> list[str]:
        templates = []

        if any(w in message for w in ("disk", "storage full", "space")):
            templates.append("free_disk_space")
        if any(w in message for w in ("dns", "name resolution")):
            templates.append("check_dns")
        if any(w in message for w in ("replication", "replica")):
            templates.append("investigate_replication")
        if any(w in message for w in ("backup", "restoration")):
            templates.append("verify_backups")
        if any(w in message for w in ("cpu", "load average", "processor")):
            templates.append("investigate_cpu_usage")
        if any(w in message for w in ("network", "connectivity", "timeout")):
            templates.append("check_network_connectivity")
        if any(
            w in message for w in ("login", "logon", "authentication", "auth failed")
        ):
            templates.append("review_failed_logins")
        if any(w in message for w in ("memory", "ram", "oom")):
            templates.append("scale_resources")

        if source == "hyperv":
            if "vm" in message or "virtual" in message:
                templates.append("restart_vm")
            templates.append("check_hyper_v_storage")

        if source == "ad":
            templates.append("investigate_ad_replication")
            templates.append("review_failed_logins")

        if source == "m365":
            templates.append("review_m365_service_health")

        if criticality in ("critical", "high"):
            templates.insert(0, "restart_service")

        if not templates:
            templates.append("health_check")

        seen = set()
        unique = []
        for t in templates:
            if t not in seen and t in RECOMMENDATION_TEMPLATES:
                seen.add(t)
                unique.append(t)
        return unique[:5]

    def _calculate_recommendation_confidence(
        self, template_key: str, criticality: str, incident_confidence: dict
    ) -> dict:
        from app.ai.confidence_engine import confidence_engine

        base = incident_confidence.get("score", 0.5)
        template_confidence = {
            "health_check": 0.9,
            "check_dns": 0.8,
            "check_network_connectivity": 0.8,
            "investigate_replication": 0.7,
            "verify_backups": 0.8,
            "review_failed_logins": 0.85,
            "investigate_cpu_usage": 0.75,
            "check_hyper_v_storage": 0.8,
            "free_disk_space": 0.85,
            "restart_service": 0.7,
            "restart_vm": 0.65,
            "scale_resources": 0.6,
            "review_m365_service_health": 0.8,
            "investigate_ad_replication": 0.75,
        }

        t_conf = template_confidence.get(template_key, 0.5)
        combined = base * 0.5 + t_conf * 0.5

        return confidence_engine.calculate(
            data_completeness=combined,
            pattern_match=t_conf,
            source_reliability=0.8,
            historical_accuracy=base,
        )

    def _build_explanation(
        self, template: dict, host_name: str, message: str, criticality: str
    ) -> str:
        return (
            f"The system detected a {criticality} incident on {host_name}: "
            f'"{message[:120]}". '
            f"Recommended action: {template['action']}. "
            f"{template['estimated_impact']}. "
            f"This recommendation requires human approval before execution."
        )


recommendation_engine = RecommendationEngine()
