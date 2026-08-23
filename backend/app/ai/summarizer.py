"""
AI Incident Summarizer

Generates human-readable incident summaries with explanations,
possible causes, recent events, and recommended actions.

AI NEVER executes infrastructure changes.
Only explains, summarizes, and recommends.

Sprint 3.11.0 - AI Operations Assistant.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IncidentSummarizer:
    """Generates incident summaries from classified alerts."""

    def summarize(self, alert: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Generate a full incident summary for a single alert.

        Returns:
            {
                "title": str,
                "explanation": str,
                "possible_causes": list[str],
                "recent_events": list[str],
                "recommended_actions": list[str],
                "affected_systems": list[str],
                "severity": str,
                "confidence": dict,
            }
        """
        source = alert.get("source", "unknown")
        host_name = alert.get("host_name", "Unknown")
        severity = alert.get("severity", "warning")
        message = alert.get("message", "")

        explanation = self._explain(source, host_name, message, alert)
        causes = self._possible_causes(source, message, alert)
        recent = self._recent_events(alert, context)
        actions = self._recommended_actions(source, severity, message, alert)
        affected = alert.get("affected_systems", [source])

        return {
            "title": f"{source.title()} incident on {host_name}",
            "explanation": explanation,
            "possible_causes": causes,
            "recent_events": recent,
            "recommended_actions": actions,
            "affected_systems": affected,
            "severity": severity,
            "confidence": self._confidence(alert, context),
        }

    def summarize_batch(self, alerts: list[dict[str, Any]], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Summarize multiple alerts."""
        return [self.summarize(a, context) for a in alerts[:20]]

    def _explain(self, source: str, host_name: str, message: str, alert: dict) -> str:
        """Generate a plain-English explanation."""
        templates = {
            "zabbix": (
                f"Zabbix monitoring detected an issue on {host_name}: "
                f'"{message}". This indicates a problem that requires attention.'
            ),
            "veeam": (
                f"Veeam backup reported an issue: \"{message}\". "
                f"This may affect backup and recovery capabilities."
            ),
            "docker": (
                f"Docker container issue detected on {host_name}: "
                f'"{message}". Container health or availability is impacted.'
            ),
            "unifi": (
                f"UniFi network device issue on {host_name}: "
                f'"{message}". Network connectivity may be affected.'
            ),
            "hyperv": (
                f"Hyper-V virtualization issue on {host_name}: "
                f'"{message}". VM availability may be impacted.'
            ),
        }
        return templates.get(source, f"Issue detected on {host_name}: {message}")

    def _possible_causes(self, source: str, message: str, alert: dict) -> list[str]:
        """Generate possible causes based on source and message."""
        msg_lower = message.lower()

        if "offline" in msg_lower or "unreachable" in msg_lower:
            return [
                "Server/network is down",
                "Firewall rule change blocking connectivity",
                "Agent or service has stopped",
                "DNS resolution failure",
                "Network infrastructure issue",
            ]
        if "disk" in msg_lower or "storage" in msg_lower:
            return [
                "Log files growing faster than expected",
                "Temporary files not being cleaned up",
                "Database growing beyond capacity",
                "Backup retention consuming excessive space",
            ]
        if "backup" in msg_lower or "job" in msg_lower:
            return [
                "Repository is full or offline",
                "Network connectivity to backup target lost",
                "VSS writer failure on source",
                "Backup service stopped or crashed",
                "License expired or nearing limit",
            ]
        if "cpu" in msg_lower or "memory" in msg_lower or "load" in msg_lower:
            return [
                "Resource-intensive process running",
                "Memory leak in application",
                "Insufficient resources allocated",
                "Runaway cron job or scheduled task",
            ]
        if "container" in msg_lower or "docker" in msg_lower:
            return [
                "Container crash loop",
                "Application error inside container",
                "Resource limits exceeded",
                "Image pull failure",
                "Volume mount issue",
            ]
        if "network" in msg_lower or "latency" in msg_lower:
            return [
                "WAN link degradation",
                "Router/switch issue",
                "DNS resolution delay",
                "Firewall throttling",
                "ISP outage",
            ]

        return [
            "Requires further investigation",
            "Check related logs and metrics",
            "Verify recent changes",
        ]

    def _recent_events(self, alert: dict, context: dict[str, Any] | None) -> list[str]:
        """Extract recent related events from context."""
        events: list[str] = []
        if not context:
            return events

        sources = context.get("sources", {})

        for source_name, source_data in sources.items():
            if not isinstance(source_data, dict):
                continue
            problems = source_data.get("problems", [])
            for p in problems[:3]:
                events.append(f"{source_name}: {p.get('name', p.get('message', ''))[:100]}")

        return events[:10]

    def _recommended_actions(self, source: str, severity: str, message: str, alert: dict) -> list[str]:
        """Generate recommended actions."""
        actions = []
        msg_lower = message.lower()

        if severity in ("critical", "high"):
            actions.append("Review incident immediately")

        actions.append("Verify network connectivity to affected system")

        if "offline" in msg_lower:
            actions.append("Ping or SSH to the host to confirm reachability")
            actions.append("Check if agent/service is running")
        elif "disk" in msg_lower:
            actions.append("Check disk usage with df -h")
            actions.append("Clean up temporary or log files")
        elif "backup" in msg_lower:
            actions.append("Check backup job logs in Veeam console")
            actions.append("Verify repository connectivity and free space")
        elif "container" in msg_lower:
            actions.append("Check container logs with docker logs")
            actions.append("Verify container health status")
        elif "cpu" in msg_lower or "memory" in msg_lower:
            actions.append("Check top processes consuming resources")
            actions.append("Review application logs for errors")

        if source == "zabbix":
            actions.append("Review Zabbix problem details and history")
        elif source == "veeam":
            actions.append("Check Veeam Backup & Replication console")
        elif source == "docker":
            actions.append("Run docker ps and docker stats for details")
        elif source == "unifi":
            actions.append("Check UniFi Site Manager for device status")

        actions.append("Document findings and update incident ticket")

        return actions

    def _confidence(self, alert: dict, context: dict[str, Any] | None) -> dict[str, Any]:
        """Calculate confidence for the summary."""
        from app.ai.confidence_engine import confidence_engine

        has_message = bool(alert.get("message"))
        has_host = bool(alert.get("host_name"))
        has_source = bool(alert.get("source"))
        has_context = context is not None

        return confidence_engine.calculate(
            data_completeness=sum([has_message, has_host, has_source, has_context]) / 4,
            pattern_match=0.7,
            source_reliability=0.8,
        )


incident_summarizer = IncidentSummarizer()
