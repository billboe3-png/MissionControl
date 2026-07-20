"""
Mission Control AI Schemas

Pydantic models for AI Operations Engine API.

Sprint 2.6.0 - AI Operations Engine.
"""

from pydantic import BaseModel


class AISearchRequest(BaseModel):
    query: str


class AISearchResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]
    confidence: dict
    related_data: dict


class AIProviderTestResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    provider: dict | None = None


class AIIncidentResponse(BaseModel):
    source: str
    host_name: str
    message: str
    criticality: str
    business_impact: str
    priority: str
    confidence: dict
    reasoning: str
    suggested_actions: list[str]


class AIRecommendationResponse(BaseModel):
    id: str
    action: str
    template_key: str
    host_name: str
    source: str
    category: str
    confidence: dict
    risk: str
    reason: str
    estimated_impact: str
    explanation: str
    requires_approval: bool
    status: str = "pending"


class AIHealthScoreResponse(BaseModel):
    score: float
    grade: str
    factors: dict
    breakdown: list[dict]
    timestamp: str


class AICorrelationResponse(BaseModel):
    groups: list[dict]
    duplicates: list[dict]
    root_events: list[dict]
    cascading_failures: list[dict]
    summary: dict
