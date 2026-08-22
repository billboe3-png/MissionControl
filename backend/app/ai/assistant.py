"""
AI Operations Assistant

Single entry point for all AI operations. No router may call an LLM directly.
The assistant coordinates: context building, incident analysis, correlation,
recommendations, summaries, and natural language queries.

AI NEVER executes infrastructure changes. Only advises, explains, summarizes,
recommends, prioritizes, and predicts.

Sprint 3.11.0 - AI Operations Assistant.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AIAssistant:
    """
    AI Operations Assistant — the single entry point for all AI analysis.

    Coordinates: context engine, correlation engine, incident classifier,
    recommendation engine, summarizer, prompts, and provider.
    """

    def __init__(self) -> None:
        from app.ai.context import context_builder
        from app.ai.correlation_engine import correlation_engine
        from app.ai.incident_classifier import incident_classifier
        from app.ai.recommendation_engine import recommendation_engine
        from app.ai.summarizer import incident_summarizer

        self._context = context_builder
        self._correlator = correlation_engine
        self._classifier = incident_classifier
        self._recommender = recommendation_engine
        self._summarizer = incident_summarizer

    # ------------------------------------------------------------------ #
    # Query                                                               #
    # ------------------------------------------------------------------ #

    async def query(self, question: str, db: Session) -> dict[str, Any]:
        """
        Answer a natural language question about the infrastructure.

        Returns:
            {
                "query": str,
                "answer": str,
                "sources": list[str],
                "confidence": dict,
                "related_data": dict,
                "suggested_actions": list[str],
            }
        """
        logger.info("AI Assistant query: %s", question[:100])

        context = await self._context.build(db)
        context_str = self._format_context(context)

        from app.ai.ai_provider import get_ai_provider
        from app.ai.prompts import SYSTEM_PROMPT, render_template

        provider = get_ai_provider()
        prompt = render_template("natural_language_query", {
            "query": question,
            "context_data": context_str,
        })

        result = await provider.complete(prompt, SYSTEM_PROMPT)

        if result.get("success"):
            answer = result["text"]
        else:
            answer = self._rule_based_query(question, context)

        return {
            "query": question,
            "answer": answer,
            "sources": list(context.get("sources", {}).keys()),
            "confidence": self._calculate_confidence(context),
            "related_data": self._extract_related(question, context),
            "suggested_actions": self._suggest_actions_from_query(question, context),
        }

    # ------------------------------------------------------------------ #
    # Dashboard Cards                                                     #
    # ------------------------------------------------------------------ #

    async def get_dashboard_cards(self, db: Session) -> dict[str, Any]:
        """Get all AI dashboard cards in a single call."""
        context = await self._context.build(db)
        alerts = context.get("alerts", [])

        classified = self._classifier.classify_batch(alerts)
        correlation = self._correlator.correlate(alerts)
        recommendations = self._recommender.generate_batch(classified)

        health = self._health_score(context)

        return {
            "health_score": health,
            "critical_incidents": [c for c in classified if c.get("criticality") == "critical"][:5],
            "likely_root_cause": correlation.get("root_events", [])[:3],
            "ai_priority_queue": self._priority_queue(classified),
            "recent_changes": self._recent_changes(context),
            "predicted_problems": self._predict_problems(classified, correlation),
            "infrastructure_health": health,
            "backup_risk": self._backup_risk(context),
            "network_risk": self._network_risk(context),
            "plugin_health": self._plugin_health(context),
            "recommendations": recommendations.get("recommendations", [])[:5],
            "correlation_summary": correlation.get("summary", {}),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Health Score                                                        #
    # ------------------------------------------------------------------ #

    async def get_health_score(self, db: Session) -> dict[str, Any]:
        """Calculate overall infrastructure health score."""
        context = await self._context.build(db)
        return self._health_score(context)

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _health_score(self, context: dict) -> dict[str, Any]:
        """Calculate health score from context."""
        sources = context.get("sources", {})
        factors: dict[str, float] = {}

        for name, data in sources.items():
            if isinstance(data, dict) and "error" not in data:
                if data.get("connected") is False or data.get("status") == "error":
                    factors[name] = 20.0
                elif data.get("status") == "degraded":
                    factors[name] = 60.0
                else:
                    factors[name] = 90.0
            else:
                factors[name] = 50.0

        score = sum(factors.values()) / len(factors) if factors else 50.0
        score = round(score, 1)

        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": score,
            "grade": grade,
            "factors": factors,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _priority_queue(self, classified: list[dict]) -> list[dict[str, Any]]:
        """Sort incidents by priority for the AI priority queue."""
        priority_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "P5": 4}
        sorted_incidents = sorted(
            classified,
            key=lambda x: priority_order.get(x.get("priority", "P5"), 5),
        )
        return [
            {
                "host_name": inc.get("host_name", "Unknown"),
                "message": inc.get("message", "")[:120],
                "priority": inc.get("priority"),
                "criticality": inc.get("criticality"),
                "source": inc.get("source"),
            }
            for inc in sorted_incidents[:10]
        ]

    def _recent_changes(self, context: dict) -> list[dict[str, Any]]:
        """Extract recent changes from context."""
        changes: list[dict[str, Any]] = []

        docker = context.get("sources", {}).get("docker", {})
        if isinstance(docker, dict) and docker.get("running"):
            changes.append({
                "type": "docker",
                "detail": f"{docker.get('running', 0)} containers running",
            })

        return changes[:5]

    def _predict_problems(self, classified: list[dict], correlation: dict) -> list[dict[str, Any]]:
        """Predict potential future problems."""
        predictions: list[dict[str, Any]] = []

        critical_count = sum(1 for c in classified if c.get("criticality") == "critical")
        if critical_count > 3:
            predictions.append({
                "prediction": "Multiple critical incidents may indicate cascading failure",
                "confidence": 0.75,
                "affected": [c.get("host_name", "") for c in classified if c.get("criticality") == "critical"][:5],
            })

        cascading = correlation.get("cascading_failures", [])
        if cascading:
            predictions.append({
                "prediction": "Cascading failure pattern detected — infrastructure instability likely",
                "confidence": 0.80,
                "affected": [],
            })

        return predictions[:5]

    def _backup_risk(self, context: dict) -> dict[str, Any]:
        """Assess backup risk from context."""
        veeam = context.get("sources", {}).get("veeam", {})
        if isinstance(veeam, dict) and veeam.get("connected") is not False:
            failed = veeam.get("failed_jobs", [])
            if failed:
                return {
                    "risk": "high",
                    "detail": f"{len(failed)} backup job(s) failing",
                    "confidence": 0.85,
                }
            return {"risk": "low", "detail": "Backups healthy", "confidence": 0.9}
        return {"risk": "unknown", "detail": "No backup data available", "confidence": 0.3}

    def _network_risk(self, context: dict) -> dict[str, Any]:
        """Assess network risk from context."""
        unifi = context.get("sources", {}).get("unifi", {})
        if isinstance(unifi, dict) and unifi.get("connected") is not False:
            offline = unifi.get("offline_devices", 0)
            if offline > 0:
                return {
                    "risk": "medium",
                    "detail": f"{offline} network device(s) offline",
                    "confidence": 0.80,
                }
            return {"risk": "low", "detail": "All network devices online", "confidence": 0.9}
        return {"risk": "unknown", "detail": "No network data available", "confidence": 0.3}

    def _plugin_health(self, context: dict) -> dict[str, Any]:
        """Assess overall plugin health."""
        sources = context.get("sources", {})
        plugin_sources = ["zabbix", "veeam", "unifi", "docker"]
        healthy = 0
        total = 0
        for name in plugin_sources:
            if name not in sources:
                continue
            data = sources[name]
            if not isinstance(data, dict):
                continue
            total += 1
            if (
                "error" not in data
                and data.get("connected") is not False
                and data.get("status") != "error"
            ):
                healthy += 1

        if total == 0:
            return {"status": "no_plugins", "healthy": 0, "total": 0}
        if healthy == total:
            return {"status": "healthy", "healthy": healthy, "total": total}
        return {"status": "degraded", "healthy": healthy, "total": total}

    def _calculate_confidence(self, context: dict) -> dict[str, Any]:
        """Calculate overall confidence for the analysis."""
        from app.ai.confidence_engine import confidence_engine

        sources = context.get("sources", {})
        available = sum(1 for v in sources.values() if isinstance(v, dict) and "error" not in v)
        total = len(sources) if sources else 1

        return confidence_engine.calculate(
            data_completeness=available / total,
            pattern_match=0.7,
            source_reliability=0.8,
        )

    def _format_context(self, context: dict) -> str:
        """Format context for LLM consumption."""
        parts = []
        for source_name, data in context.get("sources", {}).items():
            if isinstance(data, dict) and "error" not in data:
                parts.append(f"--- {source_name} ---")
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        parts.append(f"  {key}: {value}")
                    elif isinstance(value, list):
                        parts.append(f"  {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        parts.append(f"  {key}: {list(value.keys())[:10]}")
                parts.append("")
        return "\n".join(parts)

    def _extract_related(self, query: str, context: dict) -> dict[str, Any]:
        """Extract related data from context based on query keywords."""
        related: dict[str, Any] = {}
        keywords = query.lower().split()

        for source_name, data in context.get("sources", {}).items():
            if isinstance(data, dict):
                for key, value in data.items():
                    if (isinstance(value, str) and any(kw in value.lower() for kw in keywords)) or (isinstance(value, (int, float)) and any(kw in key.lower() for kw in keywords)):
                        related.setdefault(source_name, {})[key] = value

        return related

    def _suggest_actions_from_query(self, query: str, context: dict) -> list[str]:
        """Suggest actions based on the query topic."""
        query_lower = query.lower()
        actions: list[str] = []

        if "backup" in query_lower:
            actions.append("Check Veeam backup job status")
            actions.append("Verify repository capacity")
        if "docker" in query_lower or "container" in query_lower:
            actions.append("Review container health with docker ps")
            actions.append("Check container resource usage")
        if "agent" in query_lower or "offline" in query_lower:
            actions.append("Verify agent connectivity")
            actions.append("Check host network reachability")
        if "network" in query_lower or "unifi" in query_lower:
            actions.append("Review UniFi device status")
            actions.append("Check network device health")
        if "incident" in query_lower or "alert" in query_lower:
            actions.append("Review correlation engine output")
            actions.append("Check for cascading failures")

        if not actions:
            actions.append("Review AI recommendations dashboard")

        return actions

    def _rule_based_query(self, query: str, context: dict) -> str:
        """Fallback rule-based answers when no LLM is available."""
        query_lower = query.lower()
        sources = context.get("sources", {})

        if "backup" in query_lower:
            veeam = sources.get("veeam", {})
            if isinstance(veeam, dict):
                jobs = veeam.get("job_count", 0)
                repos = veeam.get("repository_count", 0)
                return (
                    f"Backup status: {jobs} jobs across {repos} repositories. "
                    f"Check the Veeam plugin dashboard for detailed status."
                )

        if "docker" in query_lower or "container" in query_lower:
            docker = sources.get("docker", {})
            if isinstance(docker, dict):
                running = docker.get("running", 0)
                unhealthy = docker.get("unhealthy", 0)
                return (
                    f"Docker: {running} running containers, "
                    f"{unhealthy} unhealthy. "
                    f"Check the Docker plugin dashboard for details."
                )

        if "agent" in query_lower or "offline" in query_lower:
            agents = sources.get("agents", {})
            if isinstance(agents, dict):
                total = agents.get("total", 0)
                online = agents.get("online", 0)
                return (
                    f"Agents: {online}/{total} online. "
                    f"Check the Fleet Management dashboard for agent details."
                )

        return (
            "I can help you analyze your infrastructure. "
            "Try asking about backups, Docker, agents, network, or incidents. "
            "Configure an AI provider in Settings for enhanced natural language analysis."
        )


ai_assistant = AIAssistant()
