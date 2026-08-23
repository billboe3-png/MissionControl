"""
RC1 Validation Orchestrator

Runs the full validation framework for Community Edition RC1.
All checks must pass to certify RC1.

Sprint 3.12.0 — RC1 Stabilization.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class CheckStatus(StrEnum):
    PASS = "pass"  # noqa: S105 - enum member name, not a password
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str = ""
    duration_ms: float = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditResult:
    phase: str
    checks: list[CheckResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    @property
    def passed(self) -> bool:
        return all(c.status != CheckStatus.FAIL for c in self.checks)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.WARN)

    @property
    def skip_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.SKIP)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "passed": self.passed,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "warn_count": self.warn_count,
            "skip_count": self.skip_count,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "duration_ms": round(c.duration_ms, 2),
                    "details": c.details,
                }
                for c in self.checks
            ],
        }


class RC1Validator:
    """Orchestrates all RC1 validation phases."""

    def __init__(self) -> None:
        self.results: dict[str, AuditResult] = {}

    def run_all(self) -> dict[str, Any]:
        """Run all validation phases and return combined results."""
        self.run_api_audit()
        self.run_plugin_audit()
        self.run_security_audit()
        self.run_performance_audit()

        total_pass = sum(r.pass_count for r in self.results.values())
        total_fail = sum(r.fail_count for r in self.results.values())
        total_warn = sum(r.warn_count for r in self.results.values())
        total_skip = sum(r.skip_count for r in self.results.values())

        overall_pass = all(r.passed for r in self.results.values())

        return {
            "certified": overall_pass,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "total_warn": total_warn,
            "total_skip": total_skip,
            "phases": {name: r.to_dict() for name, r in self.results.items()},
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def run_api_audit(self) -> AuditResult:
        """Phase 2 — API Consistency Audit."""
        from app.rc1.api_audit import run_api_audit

        result = run_api_audit()
        self.results["api_audit"] = result
        return result

    def run_plugin_audit(self) -> AuditResult:
        """Phase 3 — Plugin Integration Audit."""
        from app.rc1.plugin_audit import run_plugin_audit

        result = run_plugin_audit()
        self.results["plugin_audit"] = result
        return result

    def run_security_audit(self) -> AuditResult:
        """Phase 8 — Security Validation."""
        from app.rc1.security_audit import run_security_audit

        result = run_security_audit()
        self.results["security_audit"] = result
        return result

    def run_performance_audit(self) -> AuditResult:
        """Phase 7 — Performance Validation."""
        from app.rc1.performance import run_performance_audit

        result = run_performance_audit()
        self.results["performance_audit"] = result
        return result

    def to_dict(self) -> dict[str, Any]:
        return {name: r.to_dict() for name, r in self.results.items()}
