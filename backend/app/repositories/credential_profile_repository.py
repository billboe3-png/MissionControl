"""
Mission Control Credential Profile Repository

All database access for CredentialProfile entities.

Sprint 2.1.4 - Secure Credential Vault.

Repositories remain persistence-only. Encryption/decryption
is handled exclusively by the service layer.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.credential_profile import CredentialProfile
from app.schemas.credential_profile import (
    CredentialProfileCreate,
    CredentialProfileUpdate,
)


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
    def get_by_site(db: Session, site_id: int) -> list[CredentialProfile]:
        """Return all credential profiles for a given site."""
        stmt = select(CredentialProfile).where(
            CredentialProfile.site_id == site_id
        ).order_by(CredentialProfile.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session, data: CredentialProfileCreate
    ) -> CredentialProfile:
        """Persist a new credential profile (plaintext - legacy)."""
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
    def create_encrypted(
        db: Session,
        data: CredentialProfileCreate,
        password_encrypted: str | None = None,
        private_key_encrypted: str | None = None,
        passphrase_encrypted: str | None = None,
    ) -> CredentialProfile:
        """Persist a new credential profile with encrypted sensitive fields."""
        entity = CredentialProfile(
            name=data.name.strip(),
            authentication_type=data.authentication_type,
            username=data.username.strip(),
            password_encrypted=password_encrypted,
            private_key_encrypted=private_key_encrypted,
            passphrase_encrypted=passphrase_encrypted,
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
    def update_encrypted(
        db: Session,
        profile_id: int,
        data: CredentialProfileUpdate,
        password_encrypted: str | None = None,
        private_key_encrypted: str | None = None,
        passphrase_encrypted: str | None = None,
    ) -> CredentialProfile | None:
        """Update an existing credential profile with encrypted sensitive fields."""
        entity = CredentialProfileRepository.get_by_id(db, profile_id)
        if entity is None:
            return None

        # Apply non-sensitive field updates
        updates = data.model_dump(exclude_unset=True)
        # Remove sensitive fields from the standard update
        sensitive_fields = {"password", "ssh_key", "passphrase"}
        for field in sensitive_fields:
            updates.pop(field, None)

        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        for field, value in updates.items():
            setattr(entity, field, value)

        # Apply encrypted sensitive fields
        if password_encrypted is not None:
            entity.password_encrypted = password_encrypted
        if private_key_encrypted is not None:
            entity.private_key_encrypted = private_key_encrypted
        if passphrase_encrypted is not None:
            entity.passphrase_encrypted = passphrase_encrypted

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
