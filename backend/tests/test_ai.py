"""
Mission Control AI Operations Engine Tests

Tests for all AI subsystems:
- ConfidenceEngine
- IncidentClassifier
- CorrelationEngine
- RecommendationEngine
- AIEngine (orchestrator)
- AI Provider factory and RuleBasedProvider
- AI Router endpoints (integration)
"""

import pytest

from app.ai.confidence_engine import ConfidenceEngine
from app.ai.correlation_engine import CorrelationEngine
from app.ai.incident_classifier import IncidentClassifier
from app.ai.recommendation_engine import RecommendationEngine

# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def classifier():
    return IncidentClassifier()


@pytest.fixture
def correlator():
    return CorrelationEngine()


@pytest.fixture
def recommender():
    return RecommendationEngine()


@pytest.fixture
def confidence():
    return ConfidenceEngine()


@pytest.fixture
def sample_critical_alert():
    return {
        "id": "alert_1",
        "source": "zabbix",
        "severity": "critical",
        "message": "Disk space critically low on file server",
        "host_name": "DC01",
        "affected_systems": ["file_server", "database"],
        "host_importance": "domain_controller",
        "alert_frequency": 15,
        "historical_failures": 8,
        "timestamp": "2026-01-15T10:00:00Z",
        "tags": ["disk", "storage"],
        "related_hosts": ["DC02"],
    }


@pytest.fixture
def sample_medium_alert():
    return {
        "id": "alert_2",
        "source": "hyperv",
        "severity": "medium",
        "message": "VM backup verification warning",
        "host_name": "HV01",
        "affected_systems": ["virtualization"],
        "host_importance": "hyperv_host",
        "alert_frequency": 2,
        "historical_failures": 1,
        "timestamp": "2026-01-15T10:05:00Z",
        "tags": ["backup"],
        "related_hosts": [],
    }


@pytest.fixture
def sample_low_alert():
    return {
        "id": "alert_3",
        "source": "remote",
        "severity": "low",
        "message": "Informational status check",
        "host_name": "WEB01",
        "affected_systems": [],
        "host_importance": "workstation",
        "alert_frequency": 0,
        "historical_failures": 0,
        "timestamp": "2026-01-15T10:10:00Z",
        "tags": [],
        "related_hosts": [],
    }


@pytest.fixture
def multiple_alerts(sample_critical_alert, sample_medium_alert, sample_low_alert):
    return [sample_critical_alert, sample_medium_alert, sample_low_alert]


# ------------------------------------------------------------------ #
# ConfidenceEngine Tests                                              #
# ------------------------------------------------------------------ #


class TestConfidenceEngine:

    def test_calculate_all_high(self, confidence):
        result = confidence.calculate(
            data_completeness=1.0,
            pattern_match=1.0,
            source_reliability=1.0,
            historical_accuracy=1.0,
        )
        assert result["score"] == pytest.approx(1.0, abs=0.01)
        assert result["level"] == "very_high"
        assert all(v == 1.0 for v in result["factors"].values())

    def test_calculate_all_zero(self, confidence):
        result = confidence.calculate()
        assert result["score"] == pytest.approx(0.0, abs=0.01)
        assert result["level"] == "very_low"

    def test_calculate_mixed(self, confidence):
        result = confidence.calculate(
            data_completeness=0.8,
            pattern_match=0.6,
            source_reliability=0.9,
            historical_accuracy=0.7,
        )
        expected = 0.8 * 0.30 + 0.6 * 0.30 + 0.9 * 0.20 + 0.7 * 0.20
        assert result["score"] == pytest.approx(expected, abs=0.01)
        assert result["score"] > 0.5
        assert result["level"] in ("medium", "high", "very_high")

    def test_clamping_above_one(self, confidence):
        result = confidence.calculate(data_completeness=5.0, pattern_match=5.0)
        assert result["score"] <= 1.0
        assert result["factors"]["data_completeness"] == 1.0
        assert result["factors"]["pattern_match"] == 1.0

    def test_clamping_below_zero(self, confidence):
        result = confidence.calculate(data_completeness=-3.0, pattern_match=-1.0)
        assert result["score"] >= 0.0
        assert result["factors"]["data_completeness"] == 0.0
        assert result["factors"]["pattern_match"] == 0.0

    def test_score_to_level_thresholds(self, confidence):
        assert confidence._score_to_level(0.95) == "very_high"
        assert confidence._score_to_level(0.85) == "very_high"
        assert confidence._score_to_level(0.70) == "high"
        assert confidence._score_to_level(0.50) == "medium"
        assert confidence._score_to_level(0.30) == "low"
        assert confidence._score_to_level(0.10) == "very_low"

    def test_from_data_fields_all_true(self, confidence):
        result = confidence.from_data_fields([True, True, True, True])
        assert result["factors"]["data_completeness"] == 1.0
        assert result["score"] == pytest.approx(0.3, abs=0.01)

    def test_from_data_fields_all_false(self, confidence):
        result = confidence.from_data_fields([False, False, False])
        assert result["score"] == pytest.approx(0.0, abs=0.01)

    def test_from_data_fields_empty(self, confidence):
        result = confidence.from_data_fields([])
        assert result["score"] == pytest.approx(0.0, abs=0.01)

    def test_from_alert_count_critical(self, confidence):
        result = confidence.from_alert_count(critical=10, warning=0, info=0)
        assert result["score"] > 0.7

    def test_from_alert_count_zero(self, confidence):
        result = confidence.from_alert_count(critical=0, warning=0, info=0)
        assert result["score"] == pytest.approx(0.3, abs=0.01)


# ------------------------------------------------------------------ #
# IncidentClassifier Tests                                            #
# ------------------------------------------------------------------ #


class TestIncidentClassifier:

    def test_classify_critical_disk(self, classifier, sample_critical_alert):
        result = classifier.classify(sample_critical_alert)
        assert result["criticality"] == "critical"
        assert result["priority"] in ("P1", "P2")
        assert result["source"] == "zabbix"
        assert result["host_name"] == "DC01"
        assert result["confidence"]["score"] > 0.5
        assert len(result["suggested_actions"]) > 0
        assert len(result["reasoning"]) > 0

    def test_classify_medium(self, classifier, sample_medium_alert):
        result = classifier.classify(sample_medium_alert)
        assert result["criticality"] in ("medium", "low")
        assert result["priority"] in ("P3", "P4", "P5")
        assert result["source"] == "hyperv"

    def test_classify_low_info(self, classifier, sample_low_alert):
        result = classifier.classify(sample_low_alert)
        assert result["criticality"] in ("low", "info")
        assert result["priority"] in ("P4", "P5")
        assert result["source"] == "remote"

    def test_classify_empty_incident(self, classifier):
        result = classifier.classify({})
        assert result["criticality"] in ("medium", "info")
        assert result["priority"] in ("P3", "P4", "P5")
        assert result["source"] == "unknown"

    def test_classify_batch(self, classifier, multiple_alerts):
        results = classifier.classify_batch(multiple_alerts)
        assert len(results) == 3
        assert all("criticality" in r for r in results)
        assert all("priority" in r for r in results)
        assert all("confidence" in r for r in results)

    def test_criticality_frequency_escalation(self, classifier):
        low_alert = {
            "source": "zabbix",
            "severity": "low",
            "message": "Disk space warning",
            "host_name": "SRV01",
            "alert_frequency": 15,
        }
        result = classifier.classify(low_alert)
        assert result["criticality"] in ("high", "medium")

    def test_criticality_frequency_mild_escalation(self, classifier):
        low_alert = {
            "source": "zabbix",
            "severity": "info",
            "message": "Routine check",
            "host_name": "SRV01",
            "alert_frequency": 7,
        }
        result = classifier.classify(low_alert)
        assert result["criticality"] in ("medium", "low")

    def test_business_impact_domain_controller(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "high",
            "message": "Authentication service failure",
            "host_name": "DC01",
            "affected_systems": ["ad", "dns", "file_server"],
            "host_importance": "domain_controller",
        }
        result = classifier.classify(incident)
        assert result["business_impact"] in ("catastrophic", "major")

    def test_business_impact_workstation(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "low",
            "message": "Minor performance warning",
            "host_name": "PC01",
            "affected_systems": [],
            "host_importance": "workstation",
        }
        result = classifier.classify(incident)
        assert result["business_impact"] in ("minor", "none")

    def test_priority_score_thresholds(self, classifier):
        p1_incident = {
            "source": "zabbix",
            "severity": "critical",
            "message": "Complete outage",
            "host_name": "DC01",
            "affected_systems": ["ad", "dns", "sql", "file_server", "web"],
            "host_importance": "domain_controller",
            "alert_frequency": 20,
            "historical_failures": 15,
        }
        result = classifier.classify(p1_incident)
        assert result["priority"] == "P1"

    def test_suggest_actions_disk(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "high",
            "message": "Disk space critically low on volume C:",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("disk" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_memory(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "high",
            "message": "Memory utilization above 95%",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("memory" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_network(self, classifier):
        incident = {
            "source": "remote",
            "severity": "critical",
            "message": "Network connectivity lost to remote host",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("network" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_dns(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "high",
            "message": "DNS resolution failing",
            "host_name": "DC01",
        }
        result = classifier.classify(incident)
        assert any("dns" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_replication(self, classifier):
        incident = {
            "source": "ad",
            "severity": "high",
            "message": "AD replication latency detected",
            "host_name": "DC01",
        }
        result = classifier.classify(incident)
        assert any("replication" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_vm(self, classifier):
        incident = {
            "source": "hyperv",
            "severity": "medium",
            "message": "VM heartbeat lost",
            "host_name": "HV01",
        }
        result = classifier.classify(incident)
        assert any("virtual machine" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_login(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "warning",
            "message": "Multiple failed login attempts detected",
            "host_name": "DC01",
        }
        result = classifier.classify(incident)
        assert any("authentication" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_backup(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "medium",
            "message": "Backup job failed last night",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("backup" in a.lower() for a in result["suggested_actions"])

    def test_suggest_actions_cpu(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "warning",
            "message": "CPU load average above 90%",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("cpu" in a.lower() for a in result["suggested_actions"])

    def test_source_actions_zabbix(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "medium",
            "message": "General monitoring alert",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("zabbix" in a.lower() for a in result["suggested_actions"])

    def test_source_actions_hyperv(self, classifier):
        incident = {
            "source": "hyperv",
            "severity": "medium",
            "message": "VM status change",
            "host_name": "HV01",
        }
        result = classifier.classify(incident)
        assert any("hyper-v" in a.lower() for a in result["suggested_actions"])

    def test_source_actions_proxmox(self, classifier):
        incident = {
            "source": "proxmox",
            "severity": "medium",
            "message": "Node health degraded",
            "host_name": "PROX01",
        }
        result = classifier.classify(incident)
        assert any("proxmox" in a.lower() for a in result["suggested_actions"])

    def test_source_actions_ad(self, classifier):
        incident = {
            "source": "ad",
            "severity": "medium",
            "message": "General AD alert",
            "host_name": "DC01",
        }
        result = classifier.classify(incident)
        assert any("active directory" in a.lower() for a in result["suggested_actions"])

    def test_source_actions_m365(self, classifier):
        incident = {
            "source": "m365",
            "severity": "medium",
            "message": "Teams connectivity issue",
            "host_name": "cloud",
        }
        result = classifier.classify(incident)
        assert any("microsoft 365" in a.lower() for a in result["suggested_actions"])

    def test_source_actions_remote(self, classifier):
        incident = {
            "source": "remote",
            "severity": "medium",
            "message": "Remote host unreachable",
            "host_name": "SRV01",
        }
        result = classifier.classify(incident)
        assert any("remote" in a.lower() for a in result["suggested_actions"])

    def test_reasoning_includes_host_name(self, classifier, sample_critical_alert):
        result = classifier.classify(sample_critical_alert)
        assert "DC01" in result["reasoning"]

    def test_reasoning_includes_frequency(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "high",
            "message": "Something",
            "host_name": "SRV01",
            "alert_frequency": 10,
        }
        result = classifier.classify(incident)
        assert "10 times" in result["reasoning"]

    def test_reasoning_includes_historical(self, classifier):
        incident = {
            "source": "zabbix",
            "severity": "high",
            "message": "Something",
            "host_name": "SRV01",
            "historical_failures": 5,
        }
        result = classifier.classify(incident)
        assert "5 in the last 30 days" in result["reasoning"]

    def test_confidence_in_result(self, classifier, sample_critical_alert):
        result = classifier.classify(sample_critical_alert)
        assert "score" in result["confidence"]
        assert "level" in result["confidence"]
        assert "factors" in result["confidence"]
        assert 0.0 <= result["confidence"]["score"] <= 1.0


# ------------------------------------------------------------------ #
# CorrelationEngine Tests                                             #
# ------------------------------------------------------------------ #


class TestCorrelationEngine:

    def test_correlate_empty(self, correlator):
        result = correlator.correlate([])
        assert result["groups"] == []
        assert result["duplicates"] == []
        assert result["root_events"] == []
        assert result["cascading_failures"] == []
        assert result["summary"]["total_alerts"] == 0

    def test_correlate_single_alert(self, correlator, sample_critical_alert):
        result = correlator.correlate([sample_critical_alert])
        assert result["summary"]["total_alerts"] == 1
        assert result["summary"]["total_duplicates"] == 0

    def test_detect_duplicates(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "Disk space low on SRV01",
                "host_name": "SRV01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": [],
            },
            {
                "id": "a2",
                "source": "zabbix",
                "message": "Disk space low on SRV01",
                "host_name": "SRV01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:01:00Z",
                "tags": [],
            },
        ]
        result = correlator.correlate(alerts)
        assert len(result["duplicates"]) == 1
        assert result["duplicates"][0]["kept_id"] == "a1"
        assert result["duplicates"][0]["duplicate_id"] == "a2"

    def test_no_duplicates_different_hosts(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "Disk space low",
                "host_name": "SRV01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": [],
            },
            {
                "id": "a2",
                "source": "zabbix",
                "message": "Disk space low",
                "host_name": "SRV02",
                "severity": "critical",
                "timestamp": "2026-01-15T10:01:00Z",
                "tags": [],
            },
        ]
        result = correlator.correlate(alerts)
        assert len(result["duplicates"]) == 0

    def test_group_by_same_host(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "CPU high",
                "host_name": "SRV01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": [],
            },
            {
                "id": "a2",
                "source": "hyperv",
                "message": "VM stopped",
                "host_name": "SRV01",
                "severity": "warning",
                "timestamp": "2026-01-15T10:05:00Z",
                "tags": [],
            },
        ]
        result = correlator.correlate(alerts)
        same_host_groups = [
            g for g in result["groups"] if g.get("correlation_type") == "same_host"
        ]
        assert len(same_host_groups) >= 1
        assert same_host_groups[0]["host_name"] == "SRV01"
        assert same_host_groups[0]["alert_count"] == 2

    def test_group_by_shared_tag(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "Alert 1",
                "host_name": "SRV01",
                "severity": "warning",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": ["network"],
            },
            {
                "id": "a2",
                "source": "remote",
                "message": "Alert 2",
                "host_name": "SRV02",
                "severity": "critical",
                "timestamp": "2026-01-15T10:05:00Z",
                "tags": ["network"],
            },
        ]
        result = correlator.correlate(alerts)
        tag_groups = [
            g for g in result["groups"] if g.get("correlation_type") == "shared_tag"
        ]
        assert len(tag_groups) >= 1

    def test_root_events_detected(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "Alert 1",
                "host_name": "SRV01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": ["disk"],
            },
            {
                "id": "a2",
                "source": "zabbix",
                "message": "Alert 2",
                "host_name": "SRV01",
                "severity": "warning",
                "timestamp": "2026-01-15T10:05:00Z",
                "tags": ["disk"],
            },
        ]
        result = correlator.correlate(alerts)
        assert len(result["root_events"]) >= 1
        assert result["root_events"][0]["root_alert_id"] == "a1"

    def test_cascading_failures(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "Database slow",
                "host_name": "DB01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": ["database"],
            },
            {
                "id": "a2",
                "source": "hyperv",
                "message": "VM unresponsive",
                "host_name": "DB01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:01:00Z",
                "tags": ["database"],
            },
            {
                "id": "a3",
                "source": "remote",
                "message": "Connection timeout",
                "host_name": "WEB01",
                "severity": "high",
                "timestamp": "2026-01-15T10:02:00Z",
                "tags": ["database"],
            },
        ]
        result = correlator.correlate(alerts)
        assert len(result["cascading_failures"]) >= 1

    def test_severity_distribution(self, correlator, multiple_alerts):
        result = correlator.correlate(multiple_alerts)
        dist = result["summary"]["severity_distribution"]
        assert "critical" in dist
        assert "medium" in dist
        assert "low" in dist

    def test_summary_sources(self, correlator, multiple_alerts):
        result = correlator.correlate(multiple_alerts)
        sources = result["summary"]["sources"]
        assert "zabbix" in sources
        assert "hyperv" in sources
        assert "remote" in sources

    def test_max_severity(self, correlator):
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "message": "Low alert",
                "host_name": "SRV01",
                "severity": "low",
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": ["low_tag"],
            },
            {
                "id": "a2",
                "source": "zabbix",
                "message": "Critical alert",
                "host_name": "SRV01",
                "severity": "critical",
                "timestamp": "2026-01-15T10:01:00Z",
                "tags": ["low_tag"],
            },
        ]
        result = correlator.correlate(alerts)
        assert result["summary"]["severity_distribution"]["critical"] == 1
        assert result["summary"]["severity_distribution"]["low"] == 1


# ------------------------------------------------------------------ #
# RecommendationEngine Tests                                          #
# ------------------------------------------------------------------ #


class TestRecommendationEngine:

    def test_generate_disk_incident(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "Disk space critically low",
            "criticality": "critical",
            "priority": "P1",
            "business_impact": "major",
            "confidence": {"score": 0.8, "level": "high"},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("disk" in r.get("action", "").lower() or "disk" in r.get("reason", "").lower() for r in recs)
        for rec in recs:
            assert rec["requires_approval"] is True
            assert "id" in rec
            assert "action" in rec
            assert "category" in rec
            assert "confidence" in rec
            assert "risk" in rec
            assert "reason" in rec
            assert "estimated_impact" in rec
            assert "explanation" in rec

    def test_generate_dns_incident(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "DC01",
            "message": "DNS resolution failing on domain controller",
            "criticality": "high",
            "priority": "P2",
            "confidence": {"score": 0.7},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("dns" in r.get("action", "").lower() or "dns" in r.get("reason", "").lower() for r in recs)

    def test_generate_memory_incident(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "Memory usage above 95% OOM kills detected",
            "criticality": "high",
            "priority": "P2",
            "confidence": {"score": 0.7},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("memory" in r.get("action", "").lower() or "memory" in r.get("reason", "").lower() or "scale" in r.get("action", "").lower() for r in recs)

    def test_generate_network_incident(self, recommender):
        classified = {
            "source": "remote",
            "host_name": "SRV01",
            "message": "Network connectivity lost to remote host",
            "criticality": "critical",
            "priority": "P1",
            "confidence": {"score": 0.8},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("network" in r.get("action", "").lower() or "network" in r.get("reason", "").lower() for r in recs)

    def test_generate_login_incident(self, recommender):
        classified = {
            "source": "ad",
            "host_name": "DC01",
            "message": "Multiple failed login attempts from unknown source",
            "criticality": "high",
            "priority": "P2",
            "confidence": {"score": 0.7},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("login" in r.get("action", "").lower() or "login" in r.get("reason", "").lower() for r in recs)

    def test_generate_replication_incident(self, recommender):
        classified = {
            "source": "ad",
            "host_name": "DC01",
            "message": "AD replication latency between domain controllers",
            "criticality": "medium",
            "priority": "P3",
            "confidence": {"score": 0.6},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("replication" in r.get("action", "").lower() or "replication" in r.get("reason", "").lower() for r in recs)

    def test_generate_backup_incident(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "Backup restoration test failed",
            "criticality": "medium",
            "priority": "P3",
            "confidence": {"score": 0.6},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("backup" in r.get("action", "").lower() or "backup" in r.get("reason", "").lower() for r in recs)

    def test_generate_cpu_incident(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "CPU load average critically high",
            "criticality": "high",
            "priority": "P2",
            "confidence": {"score": 0.7},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("cpu" in r.get("action", "").lower() or "cpu" in r.get("reason", "").lower() for r in recs)

    def test_generate_hyperv_vm_incident(self, recommender):
        classified = {
            "source": "hyperv",
            "host_name": "HV01",
            "message": "VM not responding to heartbeat",
            "criticality": "critical",
            "priority": "P1",
            "confidence": {"score": 0.8},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        template_keys = [r.get("template_key", "") for r in recs]
        assert "restart_vm" in template_keys or "check_hyper_v_storage" in template_keys

    def test_generate_m365_incident(self, recommender):
        classified = {
            "source": "m365",
            "host_name": "cloud",
            "message": "Teams service degraded",
            "criticality": "medium",
            "priority": "P3",
            "confidence": {"score": 0.6},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert any("m365" in r.get("reason", "").lower() or "microsoft 365" in r.get("action", "").lower() for r in recs)

    def test_generate_unknown_source_fallback(self, recommender):
        classified = {
            "source": "unknown",
            "host_name": "SRV01",
            "message": "Something weird happened",
            "criticality": "medium",
            "priority": "P3",
            "confidence": {"score": 0.5},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1
        assert recs[0]["requires_approval"] is True

    def test_generate_empty_message(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "",
            "criticality": "low",
            "priority": "P5",
            "confidence": {"score": 0.3},
        }
        recs = recommender.generate(classified)
        assert len(recs) >= 1

    def test_generate_batch(self, recommender):
        incidents = [
            {
                "source": "zabbix",
                "host_name": "SRV01",
                "message": "Disk space low",
                "criticality": "critical",
                "confidence": {"score": 0.8},
            },
            {
                "source": "hyperv",
                "host_name": "HV01",
                "message": "VM stopped",
                "criticality": "medium",
                "confidence": {"score": 0.6},
            },
        ]
        result = recommender.generate_batch(incidents)
        assert result["total"] >= 2
        assert "by_risk" in result
        assert "timestamp" in result
        assert len(result["recommendations"]) >= 2

    def test_generate_batch_empty(self, recommender):
        result = recommender.generate_batch([])
        assert result["total"] == 0
        assert result["recommendations"] == []

    def test_requires_approval_always_true(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "Any incident",
            "criticality": "critical",
            "confidence": {"score": 0.8},
        }
        recs = recommender.generate(classified)
        assert all(rec["requires_approval"] is True for rec in recs)

    def test_critical_high_inserts_restart_first(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "Service failure detected",
            "criticality": "critical",
            "confidence": {"score": 0.8},
        }
        recs = recommender.generate(classified)
        assert recs[0]["action"] == "Restart service"

    def test_recommendation_confidence_in_range(self, recommender):
        classified = {
            "source": "zabbix",
            "host_name": "SRV01",
            "message": "Disk space low",
            "criticality": "high",
            "confidence": {"score": 0.7},
        }
        recs = recommender.generate(classified)
        for rec in recs:
            assert 0.0 <= rec["confidence"]["score"] <= 1.0
            assert rec["confidence"]["level"] in ("very_high", "high", "medium", "low", "very_low")


# ------------------------------------------------------------------ #
# AIEngine (Orchestrator) Tests                                       #
# ------------------------------------------------------------------ #


class TestAIEngine:

    @pytest.mark.asyncio
    async def test_analyze_incidents_empty(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        result = await engine.analyze_incidents([])
        assert "classified" in result
        assert "correlation" in result
        assert "recommendations" in result
        assert "health_score" in result
        assert "top_risks" in result
        assert "summary" in result
        assert result["summary"]["total_alerts"] == 0
        assert result["health_score"]["score"] == 100.0

    @pytest.mark.asyncio
    async def test_analyze_incidents_with_alerts(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        alerts = [
            {
                "id": "a1",
                "source": "zabbix",
                "severity": "critical",
                "message": "Disk space low",
                "host_name": "SRV01",
                "affected_systems": ["file_server"],
                "host_importance": "file_server",
                "alert_frequency": 12,
                "historical_failures": 5,
                "timestamp": "2026-01-15T10:00:00Z",
                "tags": ["disk"],
            },
            {
                "id": "a2",
                "source": "zabbix",
                "severity": "warning",
                "message": "Memory high",
                "host_name": "SRV01",
                "affected_systems": [],
                "host_importance": "unknown",
                "alert_frequency": 3,
                "historical_failures": 0,
                "timestamp": "2026-01-15T10:01:00Z",
                "tags": ["memory"],
            },
        ]
        result = await engine.analyze_incidents(alerts)
        assert len(result["classified"]) == 2
        assert result["summary"]["total_alerts"] == 2
        assert result["summary"]["critical_count"] >= 1
        assert result["recommendations"]["total"] >= 1
        assert len(result["top_risks"]) >= 1
        assert result["health_score"]["score"] < 100.0

    @pytest.mark.asyncio
    async def test_get_health_score_empty(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        result = await engine.get_health_score({})
        assert result["score"] == 50.0
        assert result["grade"] == "F"
        assert result["breakdown"] == []

    @pytest.mark.asyncio
    async def test_get_health_score_healthy_sources(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {
            "docker": {"status": "healthy"},
            "git": {"available": True},
            "hyperv": {"connected": True},
        }
        result = await engine.get_health_score(context)
        assert result["score"] > 80.0
        assert result["grade"] in ("A", "B")
        assert len(result["breakdown"]) == 3

    @pytest.mark.asyncio
    async def test_get_health_score_degraded_source(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {
            "docker": {"status": "degraded"},
            "git": {"available": True},
        }
        result = await engine.get_health_score(context)
        assert len(result["breakdown"]) == 2
        degraded = [b for b in result["breakdown"] if b["status"] == "degraded"]
        assert len(degraded) == 1
        assert degraded[0]["score"] == 60.0

    @pytest.mark.asyncio
    async def test_get_health_score_unhealthy_source(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {
            "docker": {"status": "unhealthy"},
        }
        result = await engine.get_health_score(context)
        assert result["score"] == 20.0
        assert result["grade"] == "F"

    @pytest.mark.asyncio
    async def test_evaluate_source_health_connected(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        assert engine._evaluate_source_health("test", {"connected": True})["score"] == 90.0
        assert engine._evaluate_source_health("test", {"connected": False})["score"] == 30.0

    @pytest.mark.asyncio
    async def test_evaluate_source_health_available(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        assert engine._evaluate_source_health("test", {"available": True})["score"] == 90.0
        assert engine._evaluate_source_health("test", {"available": False})["score"] == 30.0

    @pytest.mark.asyncio
    async def test_evaluate_source_health_unknown(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        result = engine._evaluate_source_health("test", {"random_key": "value"})
        assert result["score"] == 70.0
        assert result["status"] == "unknown"

    def test_score_to_grade(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        assert engine._score_to_grade(95) == "A"
        assert engine._score_to_grade(85) == "B"
        assert engine._score_to_grade(75) == "C"
        assert engine._score_to_grade(65) == "D"
        assert engine._score_to_grade(45) == "F"

    def test_extract_top_risks(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        classified = [
            {"criticality": "critical", "source": "zabbix", "host_name": "DC01", "message": "Outage", "priority": "P1", "business_impact": "catastrophic"},
            {"criticality": "high", "source": "hyperv", "host_name": "HV01", "message": "VM down", "priority": "P2", "business_impact": "major"},
            {"criticality": "low", "source": "remote", "host_name": "SRV01", "message": "Info", "priority": "P5", "business_impact": "none"},
        ]
        recs = {"total": 2}
        risks = engine._extract_top_risks(classified, recs)
        assert len(risks) == 2
        assert risks[0]["criticality"] == "critical"
        assert risks[1]["criticality"] == "high"

    def test_extract_top_risks_limit_10(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        classified = [
            {"criticality": "critical", "host_name": f"H{i}", "message": f"Alert {i}"}
            for i in range(15)
        ]
        risks = engine._extract_top_risks(classified, {})
        assert len(risks) == 10

    def test_rule_based_search_disk(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"system": {"disk_percent": 92}}
        answer = engine._rule_based_search("disk space low", context)
        assert "92" in answer

    def test_rule_based_search_disk_ok(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"system": {"disk_percent": 45}}
        answer = engine._rule_based_search("disk space", context)
        assert "45" in answer
        assert "No immediate concern" in answer

    def test_rule_based_search_disk_warning(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"system": {"disk_percent": 80}}
        answer = engine._rule_based_search("disk space", context)
        assert "80" in answer
        assert "Monitor" in answer

    def test_rule_based_search_health(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"health": {"docker": {"status": "unhealthy"}, "redis": {"status": "healthy"}}}
        answer = engine._rule_based_search("server health", context)
        assert "docker" in answer.lower()

    def test_rule_based_search_health_all_healthy(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"health": {"docker": {"status": "healthy"}, "redis": {"status": "healthy"}}}
        answer = engine._rule_based_search("unhealthy servers", context)
        assert "healthy" in answer.lower()

    def test_rule_based_search_failures(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"zabbix": {"problem_count": 5}}
        answer = engine._rule_based_search("overnight failures", context)
        assert "5" in answer

    def test_rule_based_search_failures_none(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"zabbix": {"problem_count": 0}}
        answer = engine._rule_based_search("failures", context)
        assert "No active" in answer

    def test_rule_based_search_hyperv(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"hyperv": {"connected": True, "running": 5, "stopped": 1, "used_memory_gb": 16.0, "total_memory_gb": 32.0}}
        answer = engine._rule_based_search("hyper-v status", context)
        assert "5 running" in answer
        assert "1 stopped" in answer

    def test_rule_based_search_hyperv_disconnected(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"hyperv": {"connected": False}}
        answer = engine._rule_based_search("hyper-v", context)
        assert "not connected" in answer

    def test_rule_based_search_exchange(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        answer = engine._rule_based_search("exchange slow", {})
        assert "Exchange" in answer

    def test_rule_based_search_ad(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        answer = engine._rule_based_search("active directory health", {})
        assert "Active Directory" in answer

    def test_rule_based_search_generic(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        answer = engine._rule_based_search("hello world", {})
        assert "infrastructure" in answer.lower()

    @pytest.mark.asyncio
    async def test_search_returns_confidence(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        result = await engine.natural_language_search("disk space", {"system": {"disk_percent": 50}})
        assert "confidence" in result
        assert "score" in result["confidence"]
        assert 0.0 <= result["confidence"]["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_search_returns_related_data(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"system": {"disk_info": "85% used on /dev/sda1"}}
        result = await engine.natural_language_search("disk", context)
        assert "related_data" in result

    @pytest.mark.asyncio
    async def test_get_ai_overview(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {
            "alerts": [
                {
                    "id": "a1",
                    "source": "zabbix",
                    "severity": "critical",
                    "message": "Critical outage",
                    "host_name": "DC01",
                    "affected_systems": ["ad"],
                    "host_importance": "domain_controller",
                    "alert_frequency": 20,
                    "historical_failures": 10,
                    "timestamp": "2026-01-15T10:00:00Z",
                    "tags": [],
                },
            ],
            "docker": {"status": "healthy"},
        }
        result = await engine.get_ai_overview(context)
        assert "health_score" in result
        assert "critical_incidents" in result
        assert "high_incidents" in result
        assert "correlated_alerts" in result
        assert "recommendations" in result
        assert "top_risks" in result
        assert "summary" in result
        assert "timestamp" in result

    def test_build_search_prompt(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"system": {"disk_percent": 80, "hostname": "SRV01"}}
        prompt = engine._build_search_prompt("what is the disk usage?", context)
        assert "disk usage" in prompt.lower()
        assert "system" in prompt
        assert "disk_percent" in prompt

    def test_extract_related(self):
        from app.ai.ai_engine import AIEngine

        engine = AIEngine()
        context = {"system": {"disk_info": "Disk is at 90% usage"}}
        related = engine._extract_related("disk", context)
        assert "system" in related
        assert "disk_info" in related["system"]


# ------------------------------------------------------------------ #
# AI Provider Tests                                                   #
# ------------------------------------------------------------------ #


class TestAIProvider:

    def test_rule_based_provider_always_available(self):
        from app.ai.ai_provider import RuleBasedProvider

        provider = RuleBasedProvider()
        assert provider is not None

    @pytest.mark.asyncio
    async def test_rule_based_test_connection(self):
        from app.ai.ai_provider import RuleBasedProvider

        provider = RuleBasedProvider()
        result = await provider.test_connection()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rule_based_complete(self):
        from app.ai.ai_provider import RuleBasedProvider

        provider = RuleBasedProvider()
        result = await provider.complete("test prompt", "system prompt")
        assert result["success"] is True
        assert len(result["text"]) > 0
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_rule_based_get_models(self):
        from app.ai.ai_provider import RuleBasedProvider

        provider = RuleBasedProvider()
        result = await provider.get_models()
        assert result["success"] is True
        assert "rule-based-v1" in result["models"]

    @pytest.mark.asyncio
    async def test_rule_based_get_provider_info(self):
        from app.ai.ai_provider import RuleBasedProvider

        provider = RuleBasedProvider()
        info = await provider.get_provider_info()
        assert info["name"] == "Rule-Based Engine"
        assert info["type"] == "rule_based"
        assert info["offline_capable"] is True

    def test_get_ai_provider_returns_rule_based(self):
        from app.ai.ai_provider import get_ai_provider, reset_ai_provider

        reset_ai_provider()
        provider = get_ai_provider()
        from app.ai.ai_provider import RuleBasedProvider

        assert isinstance(provider, RuleBasedProvider)
        reset_ai_provider()

    def test_reset_ai_provider(self):
        from app.ai.ai_provider import get_ai_provider, reset_ai_provider

        reset_ai_provider()
        p1 = get_ai_provider()
        p2 = get_ai_provider()
        assert p1 is p2
        reset_ai_provider()
        p3 = get_ai_provider()
        assert p3 is not p1

    def test_ai_provider_types_dict(self):
        from app.ai.ai_provider import AI_PROVIDER_TYPES

        assert "ollama" in AI_PROVIDER_TYPES
        assert "openai" in AI_PROVIDER_TYPES
        assert "azure_openai" in AI_PROVIDER_TYPES
        assert "anthropic" in AI_PROVIDER_TYPES
        assert "local" in AI_PROVIDER_TYPES
        assert "rule_based" in AI_PROVIDER_TYPES

    @pytest.mark.asyncio
    async def test_ollama_provider_init(self):
        from app.ai.ai_provider import OllamaProvider

        provider = OllamaProvider(base_url="http://test:11434", model="test-model")
        info = await provider.get_provider_info()
        assert info["type"] == "ollama"
        assert info["model"] == "test-model"
        assert info["offline_capable"] is True

    @pytest.mark.asyncio
    async def test_openai_provider_init(self):
        from app.ai.ai_provider import OpenAIProvider

        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        info = await provider.get_provider_info()
        assert info["type"] == "openai"
        assert info["model"] == "gpt-4o"
        assert info["offline_capable"] is False

    @pytest.mark.asyncio
    async def test_anthropic_provider_init(self):
        from app.ai.ai_provider import AnthropicProvider

        provider = AnthropicProvider(api_key="test-key", model="claude-3")
        info = await provider.get_provider_info()
        assert info["type"] == "anthropic"
        assert info["model"] == "claude-3"
        assert info["offline_capable"] is False

    @pytest.mark.asyncio
    async def test_azure_openai_provider_init(self):
        from app.ai.ai_provider import AzureOpenAIProvider

        provider = AzureOpenAIProvider(
            endpoint="https://test.openai.azure.com",
            api_key="test-key",
            deployment="gpt-4o",
        )
        info = await provider.get_provider_info()
        assert info["type"] == "azure_openai"
        assert info["model"] == "gpt-4o"
        assert info["offline_capable"] is False

    @pytest.mark.asyncio
    async def test_local_llm_provider_init(self):
        from app.ai.ai_provider import LocalLLMProvider

        provider = LocalLLMProvider(base_url="http://localhost:11434", model="llama3")
        info = await provider.get_provider_info()
        assert info["type"] == "local"
        assert info["model"] == "llama3"
        assert info["offline_capable"] is True


# ------------------------------------------------------------------ #
# AI Schemas Tests                                                    #
# ------------------------------------------------------------------ #


class TestAISchemas:

    def test_ai_search_request(self):
        from app.schemas.ai import AISearchRequest

        req = AISearchRequest(query="disk usage")
        assert req.query == "disk usage"

    def test_ai_search_response(self):
        from app.schemas.ai import AISearchResponse

        resp = AISearchResponse(
            query="test",
            answer="The disk is at 80%",
            sources=["system"],
            confidence={"score": 0.8},
            related_data={},
        )
        assert resp.query == "test"
        assert resp.answer == "The disk is at 80%"
        assert resp.sources == ["system"]

    def test_ai_health_score_response(self):
        from app.schemas.ai import AIHealthScoreResponse

        resp = AIHealthScoreResponse(
            score=85.5,
            grade="B",
            factors={"docker": 90.0},
            breakdown=[{"source": "docker", "score": 90.0, "status": "healthy"}],
            timestamp="2026-01-15T10:00:00Z",
        )
        assert resp.score == 85.5
        assert resp.grade == "B"

    def test_ai_correlation_response(self):
        from app.schemas.ai import AICorrelationResponse

        resp = AICorrelationResponse(
            groups=[],
            duplicates=[],
            root_events=[],
            cascading_failures=[],
            summary={"total_alerts": 0},
        )
        assert resp.summary["total_alerts"] == 0


# ------------------------------------------------------------------ #
# AI Service Tests (Unit)                                             #
# ------------------------------------------------------------------ #


class TestAIService:

    @pytest.mark.asyncio
    async def test_get_history(self):
        from app.ai.ai_service import AIService

        service = AIService()
        result = await service.get_history(None)
        assert result["analyses"] == []
        assert result["total"] == 0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_test_provider(self):
        from app.ai.ai_provider import reset_ai_provider
        from app.ai.ai_service import AIService

        reset_ai_provider()
        service = AIService()
        result = await service.test_provider()
        assert result["success"] is True
        assert "provider" in result
        reset_ai_provider()

    @pytest.mark.asyncio
    async def test_get_provider_status(self):
        from app.ai.ai_provider import reset_ai_provider
        from app.ai.ai_service import AIService

        reset_ai_provider()
        service = AIService()
        result = await service.get_provider_status()
        assert "provider" in result
        assert "connected" in result
        assert result["connected"] is True
        reset_ai_provider()
