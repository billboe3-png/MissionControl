"""
Mission Control Agent Registration Token Router

API endpoints for managing registration tokens.
Sprint 2.9 - Agent Registration with Company/Site scoping.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.models.db.user import User
from app.schemas.agent_token import TokenCreateRequest, TokenResponse
from app.services.agent_token_service import AgentTokenService
from app.services.auth_service import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-tokens", tags=["Agent Tokens"])


@router.get("", response_model=list[TokenResponse])
def list_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List registration tokens visible to the current user."""
    require_role(current_user, "company_admin")
    tokens = AgentTokenService.list_tokens(db)
    if current_user.role == "global_admin":
        return [TokenResponse.model_validate(t) for t in tokens]
    return [
        TokenResponse.model_validate(t)
        for t in tokens
        if t.company_id == current_user.company_id
    ]


@router.post("", response_model=TokenResponse, status_code=201)
def create_token(
    request: TokenCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new registration token (company admins within their company)."""
    require_role(current_user, "company_admin")
    if current_user.role != "global_admin":
        if (
            request.company_id is not None
            and request.company_id != current_user.company_id
        ):
            raise HTTPException(status_code=403, detail="Company not allowed")
        request.company_id = current_user.company_id
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
    require_role(current_user, "company_admin")
    token = AgentTokenService.get_token(db, token_id)
    if token is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if (
        current_user.role != "global_admin"
        and token.company_id != current_user.company_id
    ):
        raise HTTPException(status_code=404, detail="Token not found")
    token = AgentTokenService.disable_token(db, token_id)
    return TokenResponse.model_validate(token)


@router.delete("/{token_id}")
def delete_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a registration token."""
    require_role(current_user, "company_admin")
    token = AgentTokenService.get_token(db, token_id)
    if token is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if (
        current_user.role != "global_admin"
        and token.company_id != current_user.company_id
    ):
        raise HTTPException(status_code=404, detail="Token not found")
    AgentTokenService.delete_token(db, token_id)
    return {"status": "ok"}
