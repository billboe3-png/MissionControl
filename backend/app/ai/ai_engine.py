"""
Mission Control AI Engine

Central orchestrator for AI operations. Coordinates:
- Incident classification
- Alert correlation
- Recommendation generation
- Confidence scoring
- Natural language processing

AI NEVER executes infrastructure changes.
AI only observes, analyzes, prioritizes, and recommends.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class AIEngine:
    """
    Central AI engine that orchestrates all AI operations.

    Coordinates incident classification, alert correlation,
    recommendation generation, and natural language search.
    """

    def __init__(self):
        from app.ai.confidence_engine import confidence_engine
        from app.ai.correlation_engine import correlation_engine
        from app.ai.incident_classifier import incident_classifier
        from app.ai.recommendation_engine import recommendation_engine

        self._classifier = incident_classifier
        self._correlator = correlation_engine
        self._recommender = recommendation_engine
        self._confidence = confidence_engine

    async def analyze_incidents(self, alerts: list[dict]) -> dict:
        """
        Full analysis pipeline: classify, correlate, recommend.

        Args:
            alerts: raw alerts from all sources

        Returns:
            {
                "classified": list[classified_incident],
                "correlation": correlation_result,
                "recommendations": recommendation_result,
                "health_score": dict,
                "top_risks": list,
                "summary": dict,
            }
        """
        logger.info("AI Engine: analyzing %d alerts", len(alerts))

        classified = self._classifier.classify_batch(alerts)
        correlation = self._correlator.correlate(alerts)

        all_classified = classified
        recommendations = self._recommender.generate_batch(all_classified)

        health_score = self._calculate_health_score(classified, correlation)
        top_risks = self._extract_top_risks(classified, recommendations)

        summary = {
            "total_alerts": len(alerts),
            "classified_count": len(classified),
            "critical_count": sum(
                1 for c in classified if c.get("criticality") == "critical"
            ),
            "high_count": sum(1 for c in classified if c.get("criticality") == "high"),
            "recommendation_count": recommendations.get("total", 0),
            "health_score": health_score.get("score", 0),
            "correlation_groups": correlation.get("summary", {}).get("total_groups", 0),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return {
            "classified": classified,
            "correlation": correlation,
            "recommendations": recommendations,
            "health_score": health_score,
            "top_risks": top_risks,
            "summary": summary,
        }

    async def natural_language_search(self, query: str, context_data: dict) -> dict:
        """
        Process a natural language query against available context data.

        Args:
            query: user's natural language question
            context_data: infrastructure data from providers

        Returns:
            {
                "query": str,
                "answer": str,
                "sources": list[str],
                "confidence": dict,
                "related_data": dict,
            }
        """
        logger.info("AI Engine: processing NL query: %s", query[:100])

        from app.ai.ai_provider import get_ai_provider

        provider = get_ai_provider()

        system_prompt = (
            "You are Mission Control AI Operations assistant. "
            "Analyze the provided infrastructure data and answer the user's question. "
            "Be concise and specific. Focus on actionable insights. "
            "Never recommend executing changes directly."
        )

        prompt = self._build_search_prompt(query, context_data)

        result = await provider.complete(prompt, system_prompt)

        if result.get("success"):
            return {
                "query": query,
                "answer": result["text"],
                "sources": list(context_data.keys()),
                "confidence": self._confidence.calculate(
                    data_completeness=0.8,
                    pattern_match=0.7,
                    source_reliability=0.8,
                ),
                "related_data": self._extract_related(query, context_data),
            }

        return {
            "query": query,
            "answer": self._rule_based_search(query, context_data),
            "sources": list(context_data.keys()),
            "confidence": self._confidence.calculate(
                data_completeness=0.5,
                pattern_match=0.4,
                source_reliability=0.5,
            ),
            "related_data": self._extract_related(query, context_data),
        }

    async def get_health_score(self, context_data: dict) -> dict:
        """
        Calculate overall system health score from context data.

        Returns:
            {
                "score": float (0-100),
                "grade": str (A-F),
                "factors": dict,
                "breakdown": list[dict],
            }
        """
        factors = {}
        breakdown = []

        for source_name, source_data in context_data.items():
            if isinstance(source_data, dict):
                source_health = self._evaluate_source_health(source_name, source_data)
                factors[source_name] = source_health["score"]
                breakdown.append(
                    {
                        "source": source_name,
                        "score": source_health["score"],
                        "status": source_health["status"],
                        "details": source_health.get("details", ""),
                    }
                )

        if not factors:
            score = 50.0
        else:
            score = sum(factors.values()) / len(factors)

        score = round(score, 1)
        grade = self._score_to_grade(score)

        return {
            "score": score,
            "grade": grade,
            "factors": factors,
            "breakdown": breakdown,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def get_ai_overview(self, context_data: dict) -> dict:
        """Get comprehensive AI overview for dashboard."""
        alerts = context_data.get("alerts", [])
        analysis = await self.analyze_incidents(alerts)
        health = await self.get_health_score(context_data)

        return {
            "health_score": health,
            "critical_incidents": analysis["summary"]["critical_count"],
            "high_incidents": analysis["summary"]["high_count"],
            "correlated_alerts": analysis["correlation"]["summary"]["total_groups"],
            "recommendations": analysis["recommendations"]["total"],
            "top_risks": analysis["top_risks"],
            "summary": analysis["summary"],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _calculate_health_score(self, classified: list, correlation: dict) -> dict:
        if not classified:
            return {"score": 100.0, "grade": "A", "factors": {}}

        critical = sum(1 for c in classified if c.get("criticality") == "critical")
        high = sum(1 for c in classified if c.get("criticality") == "high")
        medium = sum(1 for c in classified if c.get("criticality") == "medium")
        total = len(classified)

        penalty = critical * 15 + high * 8 + medium * 3
        score = max(0.0, 100.0 - penalty)
        grade = self._score_to_grade(score)

        return {
            "score": score,
            "grade": grade,
            "factors": {
                "critical_incidents": critical,
                "high_incidents": high,
                "medium_incidents": medium,
                "total_incidents": total,
                "correlation_groups": correlation.get("summary", {}).get(
                    "total_groups", 0
                ),
            },
        }

    def _extract_top_risks(self, classified: list, recommendations: dict) -> list[dict]:
        risks = []
        for inc in classified:
            if inc.get("criticality") in ("critical", "high"):
                risks.append(
                    {
                        "source": inc.get("source", "unknown"),
                        "host_name": inc.get("host_name", "Unknown"),
                        "message": inc.get("message", "")[:150],
                        "criticality": inc.get("criticality"),
                        "priority": inc.get("priority"),
                        "business_impact": inc.get("business_impact"),
                    }
                )

        risks.sort(
            key=lambda r: {"critical": 0, "high": 1}.get(r.get("criticality"), 2)
        )
        return risks[:10]

    def _build_search_prompt(self, query: str, context_data: dict) -> str:
        parts = [f"User question: {query}\n"]
        parts.append("Available infrastructure data:\n")

        for source, data in context_data.items():
            if isinstance(data, dict):
                parts.append(f"--- {source} ---")
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        parts.append(f"  {key}: {value}")
                    elif isinstance(value, list) and len(value) <= 20:
                        parts.append(f"  {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        parts.append(f"  {key}: {list(value.keys())[:10]}")
                parts.append("")

        return "\n".join(parts)

    def _rule_based_search(self, query: str, context_data: dict) -> str:
        query_lower = query.lower()

        if "disk" in query_lower and ("low" in query_lower or "space" in query_lower):
            return self._search_disk(query_lower, context_data)
        if "server" in query_lower and (
            "unhealthy" in query_lower or "health" in query_lower
        ):
            return self._search_health(query_lower, context_data)
        if "fail" in query_lower or "overnight" in query_lower:
            return self._search_failures(query_lower, context_data)
        if "exchange" in query_lower or "slow" in query_lower:
            return self._search_exchange(query_lower, context_data)
        if "hyper-v" in query_lower or "hyperv" in query_lower:
            return self._search_hyperv(query_lower, context_data)
        if "active directory" in query_lower or "ad " in query_lower:
            return self._search_ad(query_lower, context_data)

        return (
            "I can help you analyze your infrastructure. "
            "Try asking about disk space, server health, failures, "
            "Exchange, Hyper-V, or Active Directory."
        )

    def _search_disk(self, query: str, data: dict) -> str:
        system = data.get("system", {})
        if isinstance(system, dict):
            disk_pct = system.get("disk_percent", 0)
            if disk_pct > 90:
                return f"Warning: Disk usage is at {disk_pct}%. Consider freeing space."
            if disk_pct > 75:
                return f"Disk usage is at {disk_pct}%. Monitor for further growth."
            return f"Disk usage is at {disk_pct}%. No immediate concern."
        return "System disk data not available."

    def _search_health(self, query: str, data: dict) -> str:
        health = data.get("health", {})
        if isinstance(health, dict):
            unhealthy = []
            for svc, info in health.items():
                if isinstance(info, dict) and info.get("status") != "healthy":
                    unhealthy.append(svc)
            if unhealthy:
                msg = (
                    f"Unhealthy services: "
                    f"{', '.join(unhealthy)}. "
                    f"Investigate immediately."
                )
                return msg
            return "All monitored services are healthy."
        return "Health data not available."

    def _search_failures(self, query: str, data: dict) -> str:
        zabbix = data.get("zabbix", {})
        if isinstance(zabbix, dict):
            problems = zabbix.get("problem_count", 0)
            if problems > 0:
                return (
                    f"{problems} active problems detected "
                    f"in Zabbix. Review the monitoring "
                    f"dashboard."
                )
            return "No active problems detected."
        return "Monitoring data not available."

    def _search_exchange(self, query: str, data: dict) -> str:
        return (
            "Exchange performance analysis requires integration with Exchange "
            "monitoring. Check Zabbix for Exchange-related triggers and metrics."
        )

    def _search_hyperv(self, query: str, data: dict) -> str:
        hyperv = data.get("hyperv", {})
        if isinstance(hyperv, dict):
            connected = hyperv.get("connected", False)
            if not connected:
                return (
                    "Hyper-V integration is not connected."
                    " Configure in Settings > Integrations."
                )
            running = hyperv.get("running", 0)
            stopped = hyperv.get("stopped", 0)
            total = running + stopped
            mem_used = hyperv.get("used_memory_gb", 0)
            mem_total = hyperv.get("total_memory_gb", 0)
            return (
                f"Hyper-V: {running} running, "
                f"{stopped} stopped out of {total} VMs. "
                f"Memory: {mem_used:.1f}/{mem_total:.1f} GB."
            )
        return "Hyper-V data not available."

    def _search_ad(self, query: str, data: dict) -> str:
        return (
            "Active Directory health requires AD integration. "
            "Configure in Settings > Integrations to enable AD monitoring."
        )

    def _extract_related(self, query: str, context_data: dict) -> dict:
        related = {}
        query_lower = query.lower()
        for key, value in context_data.items():
            if isinstance(value, dict):
                for field, val in value.items():
                    if isinstance(val, str) and any(
                        w in val.lower() for w in query_lower.split()
                    ):
                        related.setdefault(key, {})[field] = val
        return related

    def _evaluate_source_health(self, source_name: str, data: dict) -> dict:
        if "status" in data:
            status = data["status"]
            if status == "healthy":
                return {"score": 100.0, "status": "healthy"}
            if status == "degraded":
                return {"score": 60.0, "status": "degraded"}
            return {"score": 20.0, "status": "unhealthy"}

        if "connected" in data:
            if data["connected"]:
                return {"score": 90.0, "status": "connected"}
            return {"score": 30.0, "status": "disconnected"}

        if "available" in data:
            if data["available"]:
                return {"score": 90.0, "status": "available"}
            return {"score": 30.0, "status": "unavailable"}

        return {"score": 70.0, "status": "unknown", "details": "Insufficient data"}

    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"


ai_engine = AIEngine()
