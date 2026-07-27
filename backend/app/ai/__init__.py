"""
Mission Control AI Operations Engine (AIOps)

Provides AI-assisted operations: incident classification, alert correlation,
recommendation generation, confidence scoring, context building, and
natural language queries.

AI observes, analyzes, prioritizes, and recommends.
AI NEVER executes infrastructure changes.

Sprint 2.6.0 - AI Operations Engine.
Sprint 3.11.0 - AI Operations Assistant.
"""

from app.ai.ai_engine import AIEngine
from app.ai.ai_service import ai_service
from app.ai.assistant import ai_assistant

__all__ = ["AIEngine", "ai_service", "ai_assistant"]
