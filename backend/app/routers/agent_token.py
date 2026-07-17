"""
Mission Control Agent Registration Token Router

API endpoints for managing registration tokens.
Sprint 2.9 - Agent Registration with Company/Site scoping.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.models.db.user import User
from app.schemas.agent_token import TokenCreateRequest, TokenResponse
from app.services.agent_token_service import AgentTokenService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-tokens", tags=["Agent Tokens"])


@router.get("", response_model=list[TokenResponse])
def list_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all registration tokens."""
    tokens = AgentTokenService.list_tokens(db)
    return [TokenResponse.model_validate(t) for t in tokens]


@router.post("", response_model=TokenResponse, status_code=201)
def create_token(
    request: TokenCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new registration token."""
    token = AgentTokenService.generate_token(
        db,
        company_id=request.company_id,
        site_id=request.site_id,
        max_agents=request.max_agents,
        label=request.label,
        expires_hours=request.expires_hours,
    )
    return TokenResponse.model_validate(token)


@router.post("/{token_id}/disable", response_model=TokenResponse)
def disable_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable a registration token."""
    token = AgentTokenService.disable_token(db, token_id)
    return TokenResponse.model_validate(token)


@router.delete("/{token_id}")
def delete_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a registration token."""
    AgentTokenService.delete_token(db, token_id)
    return {"status": "ok"}
