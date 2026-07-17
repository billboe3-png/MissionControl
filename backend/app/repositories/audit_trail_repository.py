"""
Mission Control Audit Trail Repository

All database access for AuditTrail entities.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.audit_trail import AuditTrail


class AuditTrailRepository:
    """Data access layer for audit trail records."""

    @staticmethod
    def get_all(db: Session, limit: int = 200) -> list[AuditTrail]:
        stmt = (
            select(AuditTrail)
            .order_by(AuditTrail.timestamp.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, audit_id: int
    ) -> AuditTrail | None:
        stmt = select(AuditTrail).where(AuditTrail.id == audit_id)
        return db.scalar(stmt)

    @staticmethod
    def get_filtered(
        db: Session,
        entity_type: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        limit: int = 100,
    ) -> list[AuditTrail]:
        stmt = select(AuditTrail)

        if entity_type:
            stmt = stmt.where(AuditTrail.entity_type == entity_type)
        if action:
            stmt = stmt.where(AuditTrail.action == action)
        if actor:
            term = f"%{actor.strip().lower()}%"
            stmt = stmt.where(func.lower(AuditTrail.actor).like(term))

        stmt = stmt.order_by(AuditTrail.timestamp.desc()).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        entity_type: str,
        action: str,
        entity_id: int | None = None,
        actor: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> AuditTrail:
        entity = AuditTrail(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            details=details,
            ip_address=ip_address,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def count(db: Session) -> int:
        return db.scalar(
            select(func.count()).select_from(AuditTrail)
        ) or 0
