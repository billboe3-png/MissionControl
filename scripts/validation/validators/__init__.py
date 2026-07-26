"""
Mission Control Validation Framework

Base classes and utilities for all validation modules.
"""

import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    status: Status
    message: str
    details: str = ""
    duration_ms: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": round(self.duration_ms, 2),
        }
        if self.details:
            d["details"] = self.details
        if self.metrics:
            d["metrics"] = self.metrics
        return d


@dataclass
class ValidatorResult:
    """Aggregated result from a single validator module."""

    module: str
    checks: list[CheckResult] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.FAIL)

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.WARN)

    @property
    def skipped(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.SKIP)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def ok(self) -> bool:
        return self.failed == 0

    def add(self, check: CheckResult) -> None:
        self.checks.append(check)

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "total": self.total,
            "ok": self.ok,
            "duration_ms": round(self.duration_ms, 2),
            "checks": [c.to_dict() for c in self.checks],
        }


class BaseValidator:
    """Base class for all validation modules."""

    name: str = "base"
    description: str = ""

    def run(self, config: dict[str, Any]) -> ValidatorResult:
        """Run all checks in this validator. Override in subclasses."""
        raise NotImplementedError

    def _check(
        self,
        name: str,
        fn: Callable[[], Any],
        critical: bool = True,
    ) -> CheckResult:
        """Execute a check function and return a CheckResult."""
        start = time.perf_counter()
        try:
            result = fn()
            duration = (time.perf_counter() - start) * 1000

            if isinstance(result, CheckResult):
                result.duration_ms = duration
                return result

            if isinstance(result, bool):
                return CheckResult(
                    name=name,
                    status=Status.PASS if result else Status.FAIL,
                    message="ok" if result else "check failed",
                    duration_ms=duration,
                )

            if isinstance(result, str):
                return CheckResult(
                    name=name,
                    status=Status.PASS,
                    message=result,
                    duration_ms=duration,
                )

            return CheckResult(
                name=name,
                status=Status.PASS,
                message="ok",
                duration_ms=duration,
            )

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            return CheckResult(
                name=name,
                status=Status.FAIL if critical else Status.WARN,
                message=f"{type(e).__name__}: {e}",
                details=traceback.format_exc(),
                duration_ms=duration,
            )

    def _skip(self, name: str, reason: str) -> CheckResult:
        return CheckResult(
            name=name,
            status=Status.SKIP,
            message=reason,
        )

    def _warn(self, name: str, message: str) -> CheckResult:
        return CheckResult(
            name=name,
            status=Status.WARN,
            message=message,
        )
