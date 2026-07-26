"""
Mission Control Plugin Repository

Data access layer for Plugin entities.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.plugin import Plugin


class PluginRepository:
    """Data access layer for plugins stored in PostgreSQL."""

    @staticmethod
    def get_all(
        db: Session,
        execution_target: str | None = None,
        category: str | None = None,
        enabled_only: bool = False,
    ) -> list[Plugin]:
        """Return all plugins with optional filtering."""
        stmt = select(Plugin).order_by(Plugin.name.asc())
        if execution_target is not None:
            stmt = stmt.where(Plugin.execution_target == execution_target)
        if category is not None:
            stmt = stmt.where(Plugin.category == category)
        if enabled_only:
            stmt = stmt.where(Plugin.enabled.is_(True))
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, plugin_id: int) -> Plugin | None:
        """Return a single plugin by identifier."""
        return db.scalar(select(Plugin).where(Plugin.id == plugin_id))

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Plugin | None:
        """Return a single plugin by slug."""
        return db.scalar(select(Plugin).where(Plugin.slug == slug))

    @staticmethod
    def create(
        db: Session,
        slug: str,
        name: str,
        version: str,
        execution_target: str,
        **kwargs,
    ) -> Plugin:
        """Persist a new plugin."""
        entity = Plugin(
            slug=slug.strip(),
            name=name.strip(),
            version=version,
            execution_target=execution_target,
            **kwargs,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, plugin_id: int, **kwargs) -> Plugin | None:
        """Update an existing plugin."""
        entity = PluginRepository.get_by_id(db, plugin_id)
        if entity is None:
            return None
        for field, value in kwargs.items():
            if value is not None:
                setattr(entity, field, value)
            elif hasattr(entity, field):
                setattr(entity, field, None)
        entity.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, plugin_id: int) -> bool:
        """Delete a plugin by identifier."""
        entity = PluginRepository.get_by_id(db, plugin_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def count_by_target(db: Session) -> dict[str, int]:
        """Return counts of plugins grouped by execution target."""
        stmt = select(Plugin.execution_target, func.count()).group_by(
            Plugin.execution_target
        )
        return {row[0]: row[1] for row in db.execute(stmt).all()}

    @staticmethod
    def count_enabled(db: Session) -> int:
        """Return the number of enabled plugins."""
        stmt = (
            select(func.count())
            .select_from(Plugin)
            .where(Plugin.enabled.is_(True))
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def get_by_status(db: Session, status: str) -> list[Plugin]:
        """Return all plugins with a given status."""
        stmt = select(Plugin).where(Plugin.status == status).order_by(
            Plugin.name.asc()
        )
        return list(db.scalars(stmt).all())
