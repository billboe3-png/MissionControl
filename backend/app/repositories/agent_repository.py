"""
Mission Control Agent Repository

Data access layer for Agent and AgentCommand entities.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.agent import Agent
from app.models.db.agent_command import AgentCommand


class AgentRepository:
    """Data access layer for agents stored in PostgreSQL."""

    # ------------------------------------------------------------------ #
    # Agent CRUD                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_all(
        db: Session,
        company_id: int | None = None,
        site_id: int | None = None,
    ) -> list[Agent]:
        """Return all agents ordered by creation date."""
        stmt = select(Agent).order_by(Agent.created_at.desc())
        if company_id is not None:
            stmt = stmt.where(Agent.company_id == company_id)
        if site_id is not None:
            stmt = stmt.where(Agent.site_id == site_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, agent_id: int) -> Agent | None:
        """Return a single agent by identifier."""
        stmt = select(Agent).where(Agent.id == agent_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_api_key(db: Session, api_key: str) -> Agent | None:
        """Return an agent by its API key."""
        stmt = select(Agent).where(Agent.api_key == api_key)
        return db.scalar(stmt)

    @staticmethod
    def get_by_hostname(db: Session, hostname: str) -> Agent | None:
        """Return an agent by its hostname."""
        stmt = select(Agent).where(Agent.hostname == hostname)
        return db.scalar(stmt)

    @staticmethod
    def count_all(db: Session) -> int:
        """Return total agent count."""
        stmt = select(func.count()).select_from(Agent)
        return db.scalar(stmt) or 0

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        """Return agent count by status."""
        stmt = (
            select(func.count())
            .select_from(Agent)
            .where(Agent.status == status)
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def get_online_agents(db: Session) -> list[Agent]:
        """Return all agents with online status."""
        stmt = (
            select(Agent)
            .where(Agent.status == "online")
            .order_by(Agent.last_heartbeat.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_stale_agents(
        db: Session, threshold_seconds: int = 120
    ) -> list[Agent]:
        """Return agents that haven't sent a heartbeat recently."""
        cutoff = datetime.now(UTC) - timedelta(seconds=threshold_seconds)
        stmt = (
            select(Agent)
            .where(
                Agent.status == "online",
                Agent.last_heartbeat < cutoff,
            )
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        name: str,
        hostname: str,
        api_key: str,
        **kwargs,
    ) -> Agent:
        """Persist a new agent."""
        entity = Agent(
            name=name.strip(),
            hostname=hostname.strip(),
            api_key=api_key,
            **kwargs,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, agent_id: int, **kwargs) -> Agent | None:
        """Update an existing agent."""
        entity = AgentRepository.get_by_id(db, agent_id)
        if entity is None:
            return None

        for field, value in kwargs.items():
            if value is not None:
                setattr(entity, field, value)

        entity.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, agent_id: int) -> bool:
        """Delete an agent by identifier."""
        entity = AgentRepository.get_by_id(db, agent_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True


class AgentCommandRepository:
    """Data access layer for agent commands stored in PostgreSQL."""

    @staticmethod
    def get_by_id(
        db: Session, command_id: int
    ) -> AgentCommand | None:
        """Return a single command by identifier."""
        stmt = select(AgentCommand).where(
            AgentCommand.id == command_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_pending_for_agent(
        db: Session, agent_id: int, limit: int = 10
    ) -> list[AgentCommand]:
        """Return pending/dispatched commands for an agent."""
        stmt = (
            select(AgentCommand)
            .where(
                AgentCommand.agent_id == agent_id,
                AgentCommand.status.in_({"pending", "dispatched"}),
            )
            .order_by(AgentCommand.created_at.asc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_agent(
        db: Session, agent_id: int, limit: int = 50
    ) -> list[AgentCommand]:
        """Return command history for an agent."""
        stmt = (
            select(AgentCommand)
            .where(AgentCommand.agent_id == agent_id)
            .order_by(AgentCommand.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_all(
        db: Session,
        limit: int = 100,
        status: str | None = None,
        command_type: str | None = None,
        company_id: int | None = None,
        site_id: int | None = None,
    ) -> list[AgentCommand]:
        """Return all commands with optional filters."""
        stmt = select(AgentCommand)
        if status:
            stmt = stmt.where(AgentCommand.status == status)
        if command_type:
            stmt = stmt.where(
                AgentCommand.command_type == command_type
            )
        if company_id is not None:
            stmt = stmt.where(AgentCommand.company_id == company_id)
        if site_id is not None:
            stmt = stmt.where(AgentCommand.site_id == site_id)
        stmt = stmt.order_by(
            AgentCommand.created_at.desc()
        ).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        agent_id: int,
        command_type: str,
        command: str,
        **kwargs,
    ) -> AgentCommand:
        """Persist a new command."""
        entity = AgentCommand(
            agent_id=agent_id,
            command_type=command_type,
            command=command,
            **kwargs,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session, command_id: int, **kwargs
    ) -> AgentCommand | None:
        """Update an existing command."""
        entity = AgentCommandRepository.get_by_id(db, command_id)
        if entity is None:
            return None

        for field, value in kwargs.items():
            if value is not None:
                setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def count_by_status(
        db: Session, agent_id: int, status: str
    ) -> int:
        """Count commands by status for an agent."""
        stmt = (
            select(func.count())
            .select_from(AgentCommand)
            .where(
                AgentCommand.agent_id == agent_id,
                AgentCommand.status == status,
            )
        )
        return db.scalar(stmt) or 0
