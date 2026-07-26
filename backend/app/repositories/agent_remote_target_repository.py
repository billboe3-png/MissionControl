"""
Mission Control Agent Remote Target Repository
"""

from sqlalchemy.orm import Session

from app.models.db.agent_remote_target import AgentRemoteTarget


class AgentRemoteTargetRepository:
    """CRUD operations for agent remote targets."""

    @staticmethod
    def get_by_agent_id(db: Session, agent_id: int) -> list[AgentRemoteTarget]:
        return (
            db.query(AgentRemoteTarget)
            .filter(AgentRemoteTarget.agent_id == agent_id)
            .order_by(AgentRemoteTarget.name)
            .all()
        )

    @staticmethod
    def get_enabled_by_agent_id(db: Session, agent_id: int) -> list[AgentRemoteTarget]:
        return (
            db.query(AgentRemoteTarget)
            .filter(
                AgentRemoteTarget.agent_id == agent_id,
                AgentRemoteTarget.enabled,
            )
            .order_by(AgentRemoteTarget.name)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, target_id: int) -> AgentRemoteTarget | None:
        return db.query(AgentRemoteTarget).filter(AgentRemoteTarget.id == target_id).first()

    @staticmethod
    def create(db: Session, agent_id: int, **kwargs) -> AgentRemoteTarget:
        target = AgentRemoteTarget(agent_id=agent_id, **kwargs)
        db.add(target)
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def update(db: Session, target_id: int, **kwargs) -> AgentRemoteTarget | None:
        target = db.query(AgentRemoteTarget).filter(AgentRemoteTarget.id == target_id).first()
        if target is None:
            return None
        for field, value in kwargs.items():
            if value is not None:
                setattr(target, field, value)
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def delete(db: Session, target_id: int) -> bool:
        target = db.query(AgentRemoteTarget).filter(AgentRemoteTarget.id == target_id).first()
        if target is None:
            return False
        db.delete(target)
        db.commit()
        return True
