"""
Mission Control Agent Registration Token Service

Generate, validate, and consume registration tokens.
Sprint 2.9 - Agent Registration with Company/Site scoping.
"""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.agent_registration_token import AgentRegistrationToken


class AgentTokenService:
    """Business logic for registration tokens."""

    @staticmethod
    def generate_token(
        db: Session,
        company_id: int | None = None,
        site_id: int | None = None,
        max_agents: int = 10,
        label: str | None = None,
        expires_hours: int | None = None,
    ) -> AgentRegistrationToken:
        """Generate a new registration token."""
        token_value = secrets.token_urlsafe(32)
        expires_at = None
        if expires_hours:
            expires_at = datetime.now(UTC) + timedelta(hours=expires_hours)

        entity = AgentRegistrationToken(
            token=token_value,
            company_id=company_id,
            site_id=site_id,
            max_agents=max_agents,
            label=label,
            expires_at=expires_at,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def validate_token(
        db: Session, token_value: str
    ) -> AgentRegistrationToken:
        """
        Validate a registration token.

        Returns the token entity if valid, raises HTTPException otherwise.
        """
        stmt = select(AgentRegistrationToken).where(
            AgentRegistrationToken.token == token_value
        )
        entity = db.scalar(stmt)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration token",
            )
        if not entity.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration token is disabled",
            )
        if (
            entity.expires_at is not None
            and entity.expires_at < datetime.now(UTC)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration token has expired",
            )
        if entity.used_count >= entity.max_agents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration token has reached its agent limit",
            )
        return entity

    @staticmethod
    def consume_token(db: Session, token: AgentRegistrationToken) -> None:
        """Mark a token as used (increment counter)."""
        token.used_count += 1
        token.last_used_at = datetime.now(UTC)
        db.commit()

    @staticmethod
    def list_tokens(db: Session) -> list[AgentRegistrationToken]:
        """List all registration tokens."""
        stmt = select(AgentRegistrationToken).order_by(
            AgentRegistrationToken.created_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_token(
        db: Session, token_id: int
    ) -> AgentRegistrationToken | None:
        """Get a token by ID."""
        return db.scalar(
            select(AgentRegistrationToken).where(
                AgentRegistrationToken.id == token_id
            )
        )

    @staticmethod
    def disable_token(db: Session, token_id: int) -> AgentRegistrationToken:
        """Disable a registration token."""
        token = AgentTokenService.get_token(db, token_id)
        if token is None:
            raise HTTPException(status_code=404, detail="Token not found")
        token.enabled = False
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def delete_token(db: Session, token_id: int) -> None:
        """Delete a registration token."""
        token = AgentTokenService.get_token(db, token_id)
        if token is None:
            raise HTTPException(status_code=404, detail="Token not found")
        db.delete(token)
        db.commit()
