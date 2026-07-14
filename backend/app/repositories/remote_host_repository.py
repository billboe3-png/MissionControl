"""
Mission Control Remote Host Repository

All database access for RemoteHost entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.credential_profile import CredentialProfile
from app.models.db.remote_host import RemoteHost
from app.schemas.remote_host import RemoteHostCreate
from app.schemas.remote_host import RemoteHostUpdate


class RemoteHostRepository:
    """Data access layer for remote hosts stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[RemoteHost]:
        """Return all remote hosts ordered by creation date descending."""
        stmt = select(RemoteHost).order_by(RemoteHost.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_count(db: Session) -> int:
        """Return the total number of remote hosts."""
        stmt = select(func.count()).select_from(RemoteHost)
        return db.scalar(stmt) or 0

    @staticmethod
    def get_by_id(db: Session, host_id: int) -> RemoteHost | None:
        """Return a single remote host by identifier."""
        stmt = select(RemoteHost).where(RemoteHost.id == host_id)
        return db.scalar(stmt)

    @staticmethod
    def search(db: Session, search: str | None = None) -> list[RemoteHost]:
        """
        Search remote hosts by name, hostname, or IP address.
        """
        stmt = select(RemoteHost)
        if search:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                func.lower(RemoteHost.name).like(term)
                | func.lower(RemoteHost.hostname).like(term)
                | func.lower(RemoteHost.ip_address).like(term)
            )
        stmt = stmt.order_by(RemoteHost.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_status(db: Session) -> dict:
        """Return counts of enabled and disabled hosts."""
        enabled = db.scalar(
            select(func.count())
            .select_from(RemoteHost)
            .where(RemoteHost.enabled.is_(True))
        ) or 0
        disabled = db.scalar(
            select(func.count())
            .select_from(RemoteHost)
            .where(RemoteHost.enabled.is_(False))
        ) or 0
        return {"enabled": enabled, "disabled": disabled}

    @staticmethod
    def get_by_site(db: Session, site_id: int) -> list[RemoteHost]:
        """Return all remote hosts for a given site."""
        stmt = select(RemoteHost).where(
            RemoteHost.site_id == site_id
        ).order_by(RemoteHost.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_site(db: Session, site_id: int) -> int:
        """Return the number of remote hosts for a given site."""
        stmt = (
            select(func.count())
            .select_from(RemoteHost)
            .where(RemoteHost.site_id == site_id)
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def create(db: Session, data: RemoteHostCreate) -> RemoteHost:
        """Persist a new remote host."""
        entity = RemoteHost(
            name=data.name.strip(),
            hostname=data.hostname.strip(),
            ip_address=data.ip_address,
            operating_system=data.operating_system,
            connection_type=data.connection_type,
            port=data.port,
            enabled=data.enabled,
            credential_profile_id=data.credential_profile_id,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        host_id: int,
        data: RemoteHostUpdate,
    ) -> RemoteHost | None:
        """Update an existing remote host with only the supplied fields."""
        entity = RemoteHostRepository.get_by_id(db, host_id)
        if entity is None:
            return None

        updates = data.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, host_id: int) -> bool:
        """Delete a remote host by identifier."""
        entity = RemoteHostRepository.get_by_id(db, host_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def attach_credential_names(
        db: Session,
        hosts: list[RemoteHost],
    ) -> list[dict]:
        """
        Enrich host ORM instances with credential profile names.

        Returns list of dicts ready for API response serialization.
        """
        profile_ids = {
            h.credential_profile_id
            for h in hosts
            if h.credential_profile_id is not None
        }
        profiles: dict[int, str] = {}
        if profile_ids:
            result = db.execute(
                select(CredentialProfile.id, CredentialProfile.name).where(
                    CredentialProfile.id.in_(profile_ids)
                )
            )
            profiles = {row[0]: row[1] for row in result.all()}

        return [
            {
                "id": h.id,
                "name": h.name,
                "hostname": h.hostname,
                "ip_address": h.ip_address,
                "operating_system": h.operating_system,
                "connection_type": h.connection_type,
                "port": h.port,
                "enabled": h.enabled,
                "credential_profile_id": h.credential_profile_id,
                "credential_profile_name": profiles.get(h.credential_profile_id),
                "created_at": h.created_at,
                "updated_at": h.updated_at,
            }
            for h in hosts
        ]
