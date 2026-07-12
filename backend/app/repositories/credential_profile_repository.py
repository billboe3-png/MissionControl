"""
Mission Control Credential Profile Repository

All database access for CredentialProfile entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.credential_profile import CredentialProfile
from app.schemas.credential_profile import CredentialProfileCreate
from app.schemas.credential_profile import CredentialProfileUpdate


class CredentialProfileRepository:
    """Data access layer for credential profiles stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[CredentialProfile]:
        """Return all credential profiles ordered by creation date descending."""
        stmt = select(CredentialProfile).order_by(
            CredentialProfile.created_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_count(db: Session) -> int:
        """Return the total number of credential profiles."""
        stmt = select(func.count()).select_from(CredentialProfile)
        return db.scalar(stmt) or 0

    @staticmethod
    def get_by_id(
        db: Session, profile_id: int
    ) -> CredentialProfile | None:
        """Return a single credential profile by identifier."""
        stmt = select(CredentialProfile).where(
            CredentialProfile.id == profile_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(
        db: Session, name: str
    ) -> CredentialProfile | None:
        """Return a credential profile by name using case-insensitive lookup."""
        normalized = name.strip().lower()
        stmt = select(CredentialProfile).where(
            func.lower(func.trim(CredentialProfile.name)) == normalized
        )
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session, data: CredentialProfileCreate
    ) -> CredentialProfile:
        """Persist a new credential profile."""
        entity = CredentialProfile(
            name=data.name.strip(),
            authentication_type=data.authentication_type,
            username=data.username.strip(),
            password=data.password,
            ssh_key=data.ssh_key,
            description=data.description,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        profile_id: int,
        data: CredentialProfileUpdate,
    ) -> CredentialProfile | None:
        """Update an existing credential profile with only the supplied fields."""
        entity = CredentialProfileRepository.get_by_id(db, profile_id)
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
    def delete(db: Session, profile_id: int) -> bool:
        """Delete a credential profile by identifier."""
        entity = CredentialProfileRepository.get_by_id(db, profile_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True
