"""
Mission Control AI Operations Engine (AIOps)

Provides AI-assisted operations: incident classification, alert correlation,
recommendation generation, and confidence scoring.

AI observes, analyzes, prioritizes, and recommends.
AI NEVER executes infrastructure changes.

Sprint 2.6.0 - AI Operations Engine.
"""

from app.ai.ai_engine import AIEngine
from app.ai.ai_service import ai_service

__all__ = ["AIEngine", "ai_service"]
