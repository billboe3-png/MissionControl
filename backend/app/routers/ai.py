"""
Mission Control AI Router

API endpoints for the AI Operations Engine.

All endpoints are read-only analysis.
No endpoint executes infrastructure changes.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.ai_service import ai_service
from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.ai import AISearchRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Operations"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/overview", summary="AI Operations Overview")
async def get_ai_overview(db: Session = Depends(get_db)):
    """Get AI operations overview for the dashboard."""
    return await ai_service.get_overview(db)


@router.get("/analyze", summary="Full Incident Analysis")
async def analyze_incidents(db: Session = Depends(get_db)):
    """Run full incident analysis pipeline."""
    return await ai_service.analyze(db)


@router.get("/incidents", summary="Classified Incidents")
async def get_incidents(db: Session = Depends(get_db)):
    """Get classified incidents with priority and reasoning."""
    return await ai_service.get_incidents(db)


@router.get("/recommendations", summary="AI Recommendations")
async def get_recommendations(db: Session = Depends(get_db)):
    """Get current AI recommendations."""
    return await ai_service.get_recommendations(db)


@router.get("/correlations", summary="Alert Correlations")
async def get_correlations(db: Session = Depends(get_db)):
    """Get correlated alerts across all sources."""
    return await ai_service.get_correlations(db)


@router.get("/health-score", summary="System Health Score")
async def get_health_score(db: Session = Depends(get_db)):
    """Get AI-calculated system health score."""
    return await ai_service.get_health_score(db)


@router.post("/search", summary="Natural Language Search")
async def search(request: AISearchRequest, db: Session = Depends(get_db)):
    """Search infrastructure using natural language."""
    return await ai_service.search(request.query, db)


@router.get("/history", summary="Analysis History")
async def get_history(db: Session = Depends(get_db)):
    """Get AI analysis history."""
    return await ai_service.get_history(db)


@router.get("/provider/status", summary="AI Provider Status")
async def get_provider_status():
    """Get current AI provider status."""
    return await ai_service.get_provider_status()


@router.post("/provider/test", summary="Test AI Provider")
async def test_provider():
    """Test AI provider connection."""
    return await ai_service.test_provider()
