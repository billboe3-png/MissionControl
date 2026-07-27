"""
AI Operations Assistant Tests

Tests for: context builder, correlation engine, incident summaries,
recommendations, prompts, provider abstraction, dashboard integration,
natural language queries.
"""

import pytest

# ------------------------------------------------------------------ #
# Context Builder                                                      #
# ------------------------------------------------------------------ #


class TestContextBuilder:
    """Tests for AI context engine."""

    def test_context_builder_import(self):
        from app.ai.context import ContextBuilder, context_builder

        assert isinstance(context_builder, ContextBuilder)

    @pytest.mark.asyncio
    async def test_context_build_minimal(self):
        from unittest.mock import MagicMock

        from app.ai.context import ContextBuilder

        builder = ContextBuilder()

        mock_db = MagicMock()
        context = await builder.build(mock_db)

        assert "timestamp" in context
        assert "sources" in context
        assert "alerts" in context
        assert "summary" in context
        assert isinstance(context["sources"], dict)

    def test_extract_all_alerts_empty(self):
        from app.ai.context import ContextBuilder

        builder = ContextBuilder()
        alerts = builder._extract_all_alerts({})
        assert alerts == []

    def test_build_summary(self):
        from app.ai.context import ContextBuilder

        builder = ContextBuilder()
        sources = {
            "zabbix": {"connected": True},
            "veeam": {"error": "timeout"},
        }
        summary = builder._build_summary(sources)
        assert summary["zabbix"] == "available"
        assert summary["veeam"] == "error"


# ------------------------------------------------------------------ #
# Prompt Library                                                       #
# ------------------------------------------------------------------ #


class TestPromptLibrary:
    """Tests for AI prompt templates."""

    def test_all_templates_exist(self):
        from app.ai.prompts import TEMPLATES

        expected = [
            "alert_summary",
            "incident_summary",
            "backup_analysis",
            "infrastructure_summary",
            "executive_summary",
            "daily_report",
            "weekly_report",
            "root_cause_analysis",
            "maintenance_recommendation",
            "capacity_planning",
            "natural_language_query",
        ]
        for name in expected:
            assert name in TEMPLATES, f"Missing template: {name}"

    def test_render(self):
        from app.ai.prompts import render

        result = render("Hello {name}, severity is {sev}", {"name": "SRV-01", "sev": "critical"})
        assert result == "Hello SRV-01, severity is critical"

    def test_get_template(self):
        from app.ai.prompts import get_template

        tpl = get_template("incident_summary")
        assert "{source}" in tpl
        assert "{host_name}" in tpl

    def test_get_template_missing(self):
        from app.ai.prompts import get_template

        assert get_template("nonexistent") == ""

    def test_render_template(self):
        from app.ai.prompts import render_template

        result = render_template("incident_summary", {
            "source": "zabbix",
            "host_name": "SRV-01",
            "severity": "critical",
            "message": "CPU at 99%",
            "affected_systems": "database, web",
        })
        assert "zabbix" in result
        assert "SRV-01" in result
        assert "CPU at 99%" in result

    def test_system_prompt_exists(self):
        from app.ai.prompts import SYSTEM_PROMPT

        assert "Mission Control" in SYSTEM_PROMPT
        assert "NEVER execute" in SYSTEM_PROMPT


# ------------------------------------------------------------------ #
# Incident Summarizer                                                  #
# ------------------------------------------------------------------ #


class TestIncidentSummarizer:
    """Tests for AI incident summarizer."""

    def test_summarize_basic(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        alert = {
            "source": "zabbix",
            "host_name": "SRV-01",
            "severity": "critical",
            "message": "CPU usage at 99%",
            "affected_systems": ["monitoring"],
        }
        result = summarizer.summarize(alert)

        assert "title" in result
        assert "explanation" in result
        assert "possible_causes" in result
        assert "recommended_actions" in result
        assert "confidence" in result
        assert result["severity"] == "critical"
        assert len(result["possible_causes"]) > 0
        assert len(result["recommended_actions"]) > 0

    def test_summarize_batch(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        alerts = [
            {"source": "zabbix", "host_name": "H1", "severity": "warning", "message": "disk full"},
            {"source": "docker", "host_name": "H2", "severity": "critical", "message": "container offline"},
        ]
        results = summarizer.summarize_batch(alerts)
        assert len(results) == 2

    def test_possible_causes_offline(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        causes = summarizer._possible_causes("zabbix", "Server offline", {})
        assert any("down" in c.lower() or "firewall" in c.lower() or "agent" in c.lower() for c in causes)

    def test_possible_causes_disk(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        causes = summarizer._possible_causes("zabbix", "Disk space critical", {})
        assert any("log" in c.lower() or "temp" in c.lower() for c in causes)

    def test_possible_causes_backup(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        causes = summarizer._possible_causes("veeam", "Backup job failed", {})
        assert len(causes) >= 3

    def test_recommended_actions_offline(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        actions = summarizer._recommended_actions("zabbix", "critical", "Server offline", {})
        assert len(actions) >= 3
        assert any("ping" in a.lower() or "network" in a.lower() for a in actions)

    def test_summarize_confidence(self):
        from app.ai.summarizer import IncidentSummarizer

        summarizer = IncidentSummarizer()
        alert = {"source": "zabbix", "host_name": "H1", "severity": "warning", "message": "test"}
        result = summarizer.summarize(alert)
        assert "score" in result["confidence"]
        assert 0 <= result["confidence"]["score"] <= 1


# ------------------------------------------------------------------ #
# Correlation Engine                                                   #
# ------------------------------------------------------------------ #


class TestCorrelationEngine:
    """Tests for correlation engine."""

    def test_correlate_empty(self):
        from app.ai.correlation_engine import CorrelationEngine

        engine = CorrelationEngine()
        result = engine.correlate([])
        assert result["groups"] == []
        assert result["summary"]["total_alerts"] == 0

    def test_correlate_single_alert(self):
        from app.ai.correlation_engine import CorrelationEngine

        engine = CorrelationEngine()
        alerts = [{"id": "1", "source": "zabbix", "severity": "warning", "message": "test", "host_name": "H1"}]
        result = engine.correlate(alerts)
        assert result["summary"]["total_alerts"] == 1

    def test_correlate_same_host(self):
        from app.ai.correlation_engine import CorrelationEngine

        engine = CorrelationEngine()
        alerts = [
            {"id": "1", "source": "zabbix", "severity": "warning", "message": "disk full", "host_name": "SRV-01", "timestamp": "2026-01-01T00:00:00"},
            {"id": "2", "source": "docker", "severity": "critical", "message": "container down", "host_name": "SRV-01", "timestamp": "2026-01-01T00:01:00"},
        ]
        result = engine.correlate(alerts)
        host_groups = [g for g in result["groups"] if g.get("correlation_type") == "same_host"]
        assert len(host_groups) >= 1

    def test_detect_duplicates(self):
        from app.ai.correlation_engine import CorrelationEngine

        engine = CorrelationEngine()
        alerts = [
            {"id": "1", "source": "zabbix", "host_name": "H1", "message": "disk full on server"},
            {"id": "2", "source": "zabbix", "host_name": "H1", "message": "disk full on server"},
        ]
        dups = engine._detect_duplicates(alerts)
        assert len(dups) == 1


# ------------------------------------------------------------------ #
# Recommendation Engine                                                #
# ------------------------------------------------------------------ #


class TestRecommendationEngine:
    """Tests for recommendation engine."""

    def test_generate_disk_alert(self):
        from app.ai.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        incident = {
            "source": "zabbix",
            "criticality": "warning",
            "message": "Disk space critical on SRV-01",
            "host_name": "SRV-01",
            "affected_systems": ["storage"],
            "confidence": {"score": 0.7},
        }
        recs = engine.generate(incident)
        assert len(recs) > 0
        assert any("disk" in r.get("action", "").lower() or "free" in r.get("action", "").lower() for r in recs)

    def test_generate_batch(self):
        from app.ai.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        incidents = [
            {"source": "zabbix", "criticality": "critical", "message": "CPU critical", "host_name": "H1", "affected_systems": [], "confidence": {}},
            {"source": "docker", "criticality": "warning", "message": "container unhealthy", "host_name": "H2", "affected_systems": [], "confidence": {}},
        ]
        result = engine.generate_batch(incidents)
        assert result["total"] > 0
        assert "by_risk" in result

    def test_recommendation_has_explanation(self):
        from app.ai.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        incident = {
            "source": "zabbix",
            "criticality": "high",
            "message": "Network timeout",
            "host_name": "SRV-01",
            "affected_systems": ["network"],
            "confidence": {"score": 0.6},
        }
        recs = engine.generate(incident)
        for rec in recs:
            assert "explanation" in rec
            assert "confidence" in rec
            assert "requires_approval" in rec
            assert rec["requires_approval"] is True


# ------------------------------------------------------------------ #
# Incident Classifier                                                  #
# ------------------------------------------------------------------ #


class TestIncidentClassifier:
    """Tests for incident classifier."""

    def test_classify_critical(self):
        from app.ai.incident_classifier import IncidentClassifier

        classifier = IncidentClassifier()
        incident = {
            "source": "zabbix",
            "severity": "critical",
            "message": "Server unreachable",
            "host_name": "DC-01",
            "affected_systems": ["domain_controller"],
            "host_importance": "domain_controller",
            "alert_frequency": 5,
            "historical_failures": 2,
        }
        result = classifier.classify(incident)
        assert result["criticality"] in ("critical", "high")
        assert result["priority"] in ("P1", "P2")
        assert "score" in result["confidence"]
        assert len(result["suggested_actions"]) > 0
        assert len(result["reasoning"]) > 0

    def test_classify_low(self):
        from app.ai.incident_classifier import IncidentClassifier

        classifier = IncidentClassifier()
        incident = {
            "source": "zabbix",
            "severity": "info",
            "message": "Scheduled maintenance",
            "host_name": "SRV-02",
            "affected_systems": [],
            "host_importance": "workstation",
            "alert_frequency": 0,
            "historical_failures": 0,
        }
        result = classifier.classify(incident)
        assert result["criticality"] in ("info", "low")
        assert result["priority"] in ("P4", "P5")


# ------------------------------------------------------------------ #
# Confidence Engine                                                    #
# ------------------------------------------------------------------ #


class TestConfidenceEngine:
    """Tests for confidence engine."""

    def test_calculate(self):
        from app.ai.confidence_engine import ConfidenceEngine

        engine = ConfidenceEngine()
        result = engine.calculate(
            data_completeness=0.9,
            pattern_match=0.8,
            source_reliability=0.7,
            historical_accuracy=0.6,
        )
        assert 0 <= result["score"] <= 1
        assert result["level"] in ("very_high", "high", "medium", "low", "very_low")
        assert "factors" in result

    def test_from_data_fields(self):
        from app.ai.confidence_engine import ConfidenceEngine

        engine = ConfidenceEngine()
        result = engine.from_data_fields([True, True, True, False])
        assert 0 <= result["score"] <= 1

    def test_from_alert_count(self):
        from app.ai.confidence_engine import ConfidenceEngine

        engine = ConfidenceEngine()
        result = engine.from_alert_count(critical=5, warning=3, info=1)
        assert 0 <= result["score"] <= 1


# ------------------------------------------------------------------ #
# AI Provider                                                          #
# ------------------------------------------------------------------ #


class TestAIProvider:
    """Tests for AI provider abstraction."""

    def test_rule_based_provider(self):
        from app.ai.ai_provider import RuleBasedProvider

        provider = RuleBasedProvider()
        import asyncio
        info = asyncio.get_event_loop().run_until_complete(provider.get_provider_info())
        assert info["type"] == "rule_based"
        assert info["offline_capable"] is True

    def test_provider_types_registry(self):
        from app.ai.ai_provider import AI_PROVIDER_TYPES

        expected = ["ollama", "openai", "azure_openai", "anthropic", "local", "lm_studio", "openrouter", "rule_based"]
        for name in expected:
            assert name in AI_PROVIDER_TYPES

    def test_get_ai_provider_returns_rule_based(self):
        from app.ai.ai_provider import get_ai_provider, reset_ai_provider

        reset_ai_provider()
        provider = get_ai_provider()
        assert provider is not None

    def test_ollama_provider_init(self):
        from app.ai.ai_provider import OllamaProvider

        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")
        assert provider._model == "llama3"

    def test_lm_studio_provider_init(self):
        from app.ai.ai_provider import LMStudioProvider

        provider = LMStudioProvider(base_url="http://localhost:1234", model="test")
        assert provider._model == "test"

    def test_openrouter_provider_init(self):
        from app.ai.ai_provider import OpenRouterProvider

        provider = OpenRouterProvider(api_key="key123", model="test-model")
        assert provider._model == "test-model"


# ------------------------------------------------------------------ #
# AI Assistant                                                         #
# ------------------------------------------------------------------ #


class TestAIAssistant:
    """Tests for AI Operations Assistant."""

    def test_assistant_import(self):
        from app.ai.assistant import AIAssistant, ai_assistant

        assert isinstance(ai_assistant, AIAssistant)

    @pytest.mark.asyncio
    async def test_health_score(self):
        from unittest.mock import MagicMock

        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        mock_db = MagicMock()
        score = await assistant.get_health_score(mock_db)
        assert "score" in score
        assert "grade" in score
        assert 0 <= score["score"] <= 100

    def test_health_score_empty(self):
        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        score = assistant._health_score({"sources": {}})
        assert score["score"] == 50.0

    def test_priority_queue(self):
        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        classified = [
            {"host_name": "H1", "message": "test1", "priority": "P3", "criticality": "medium", "source": "zabbix"},
            {"host_name": "H2", "message": "test2", "priority": "P1", "criticality": "critical", "source": "docker"},
        ]
        queue = assistant._priority_queue(classified)
        assert len(queue) == 2
        assert queue[0]["priority"] == "P1"

    def test_backup_risk(self):
        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        risk = assistant._backup_risk({"sources": {"veeam": {"connected": True, "failed_jobs": [{"name": "job1"}]}}})
        assert risk["risk"] == "high"

    def test_network_risk(self):
        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        risk = assistant._network_risk({"sources": {"unifi": {"connected": True, "offline_devices": 3}}})
        assert risk["risk"] == "medium"

    def test_plugin_health(self):
        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        health = assistant._plugin_health({"sources": {"zabbix": {"connected": True}, "docker": {"error": "fail"}}})
        assert health["total"] == 2
        assert health["healthy"] == 1

    def test_rule_based_query_backup(self):
        from app.ai.assistant import AIAssistant

        assistant = AIAssistant()
        context = {"sources": {"veeam": {"job_count": 5, "repository_count": 2}}}
        answer = assistant._rule_based_query("Why are backups failing?", context)
        assert "backup" in answer.lower() or "5" in answer


# ------------------------------------------------------------------ #
# AI Engine                                                            #
# ------------------------------------------------------------------ #


class TestAIEngine:
    """Tests for AI engine."""

    def test_analyze_empty(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(engine.analyze_incidents([]))
        assert result["summary"]["total_alerts"] == 0
        assert result["health_score"]["score"] == 100.0

    def test_health_score_grades(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        assert engine._score_to_grade(95) == "A"
        assert engine._score_to_grade(85) == "B"
        assert engine._score_to_grade(75) == "C"
        assert engine._score_to_grade(65) == "D"
        assert engine._score_to_grade(50) == "F"


# ------------------------------------------------------------------ #
# AI Service                                                           #
# ------------------------------------------------------------------ #


class TestAIService:
    """Tests for AI service layer."""

    def test_service_import(self):
        from app.ai.ai_service import AIService, ai_service

        assert isinstance(ai_service, AIService)

    @pytest.mark.asyncio
    async def test_get_history(self):
        from app.ai.ai_service import AIService

        service = AIService()
        from unittest.mock import MagicMock
        result = await service.get_history(MagicMock())
        assert "analyses" in result
        assert result["total"] == 0
