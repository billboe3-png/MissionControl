"""
Mission Control Confidence Engine

Calculates confidence scores for AI analyses based on:
- Data completeness
- Historical accuracy
- Source reliability
- Pattern match strength

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class ConfidenceLevel(StrEnum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class ConfidenceEngine:
    """Calculates and normalizes confidence scores."""

    def calculate(
        self,
        data_completeness: float = 0.0,
        pattern_match: float = 0.0,
        source_reliability: float = 0.0,
        historical_accuracy: float = 0.0,
    ) -> dict:
        """
        Calculate weighted confidence score.

        Args:
            data_completeness: 0.0-1.0, how complete the input data is
            pattern_match: 0.0-1.0, how well patterns match known issues
            source_reliability: 0.0-1.0, reliability of the data source
            historical_accuracy: 0.0-1.0, past accuracy of similar analyses

        Returns:
            {"score": float, "level": str, "factors": dict}
        """
        weights = {
            "data_completeness": 0.30,
            "pattern_match": 0.30,
            "source_reliability": 0.20,
            "historical_accuracy": 0.20,
        }

        factors = {
            "data_completeness": max(0.0, min(1.0, data_completeness)),
            "pattern_match": max(0.0, min(1.0, pattern_match)),
            "source_reliability": max(0.0, min(1.0, source_reliability)),
            "historical_accuracy": max(0.0, min(1.0, historical_accuracy)),
        }

        score = sum(factors[k] * weights[k] for k in weights)
        score = round(max(0.0, min(1.0, score)), 3)
        level = self._score_to_level(score)

        return {
            "score": score,
            "level": level,
            "factors": factors,
        }

    def _score_to_level(self, score: float) -> str:
        if score >= 0.85:
            return ConfidenceLevel.VERY_HIGH
        if score >= 0.70:
            return ConfidenceLevel.HIGH
        if score >= 0.50:
            return ConfidenceLevel.MEDIUM
        if score >= 0.30:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.VERY_LOW

    def from_data_fields(self, fields: list[bool]) -> dict:
        """Calculate confidence from boolean data field availability."""
        if not fields:
            return self.calculate(data_completeness=0.0)
        available = sum(1 for f in fields if f)
        completeness = available / len(fields)
        return self.calculate(data_completeness=completeness)

    def from_alert_count(self, critical: int, warning: int, info: int) -> dict:
        """Calculate confidence from alert distribution."""
        total = critical + warning + info
        if total == 0:
            return self.calculate(data_completeness=0.5, pattern_match=0.5)

        critical_ratio = critical / total
        pattern = min(1.0, critical_ratio * 2 + 0.3)
        completeness = min(1.0, total / 10)

        return self.calculate(
            data_completeness=completeness,
            pattern_match=pattern,
            source_reliability=0.8,
        )


confidence_engine = ConfidenceEngine()
