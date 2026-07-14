"""
Mission Control Integration Service

Business logic for integration management: CRUD, connection testing,
encryption/decryption of secrets, and provider injection.

Sprint 2.3.1 - Integration Management (Production Configuration UI).
"""

import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CredentialCipher
from app.models.db.integration_profile import IntegrationProfile
from app.repositories.integration_profile_repository import (
    IntegrationProfileRepository,
)
from app.schemas.integration import (
    IntegrationProfileCreate,
    IntegrationProfileListResponse,
    IntegrationProfileResponse,
    IntegrationProfileUpdate,
    IntegrationTestResponse,
)

logger = logging.getLogger(__name__)


def _get_cipher() -> CredentialCipher:
    from app.core.config import get_settings

    settings = get_settings()
    return CredentialCipher(settings.missioncontrol_secret_key)


def _encrypt(value: str | None) -> str | None:
    if not value:
        return None
    return _get_cipher().encrypt(value)


def _decrypt(value: str | None) -> str | None:
    if not value:
        return None
    return _get_cipher().decrypt(value)


class IntegrationService:
    """Service layer for integration management."""

    # ------------------------------------------------------------------ #
    # CRUD                                                                #
    # ------------------------------------------------------------------ #

    async def list_profiles(
        self, db: Session
    ) -> IntegrationProfileListResponse:
        """List all integration profiles with secrets masked."""
        profiles = IntegrationProfileRepository.get_all(db)
        items = [
            self._to_response(p) for p in profiles
        ]
        return IntegrationProfileListResponse(
            count=len(items), items=items
        )

    async def get_profile(
        self, db: Session, profile_id: int
    ) -> IntegrationProfileResponse:
        """Get a single integration profile with secrets masked."""
        profile = IntegrationProfileRepository.get_by_id(db, profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )
        return self._to_response(profile)

    async def create_profile(
        self, db: Session, data: IntegrationProfileCreate
    ) -> IntegrationProfileResponse:
        """Create a new integration profile with encrypted secrets."""
        valid_types = ("zabbix", "active_directory", "microsoft_365")
        if data.integration_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"integration_type must be one of: "
                    f"{', '.join(valid_types)}"
                ),
            )

        kwargs = {
            "description": data.description,
            "enabled": data.enabled,
            "base_url": data.base_url,
            "username": data.username,
            "encrypted_secret": _encrypt(data.password),
            "tenant_id": data.tenant_id,
            "client_id": data.client_id,
            "client_secret_encrypted": _encrypt(data.client_secret),
            "authority_url": data.authority_url,
            "domain": data.domain,
            "base_dn": data.base_dn,
            "use_ssl": data.use_ssl,
            "verify_ssl": data.verify_ssl,
            "timeout": data.timeout,
            "poll_interval": data.poll_interval,
        }

        profile = IntegrationProfileRepository.create(
            db, data.name, data.integration_type, **kwargs
        )
        return self._to_response(profile)

    async def update_profile(
        self,
        db: Session,
        profile_id: int,
        data: IntegrationProfileUpdate,
    ) -> IntegrationProfileResponse:
        """Update an integration profile with encrypted secrets."""
        existing = IntegrationProfileRepository.get_by_id(
            db, profile_id
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )

        updates = data.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()

        if "password" in updates:
            pwd = updates.pop("password")
            if pwd == "" or pwd is None:
                updates["encrypted_secret"] = existing.encrypted_secret
            else:
                updates["encrypted_secret"] = _encrypt(pwd)

        if "client_secret" in updates:
            cs = updates.pop("client_secret")
            if cs == "" or cs is None:
                updates["client_secret_encrypted"] = (
                    existing.client_secret_encrypted
                )
            else:
                updates["client_secret_encrypted"] = _encrypt(cs)

        profile = IntegrationProfileRepository.update(
            db, profile_id, **updates
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )
        return self._to_response(profile)

    async def delete_profile(
        self, db: Session, profile_id: int
    ) -> None:
        """Delete an integration profile."""
        deleted = IntegrationProfileRepository.delete(db, profile_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )

    # ------------------------------------------------------------------ #
    # Actions                                                             #
    # ------------------------------------------------------------------ #

    async def enable_profile(
        self, db: Session, profile_id: int
    ) -> IntegrationProfileResponse:
        """Enable an integration profile."""
        profile = IntegrationProfileRepository.update(
            db, profile_id, enabled=True
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )
        return self._to_response(profile)

    async def disable_profile(
        self, db: Session, profile_id: int
    ) -> IntegrationProfileResponse:
        """Disable an integration profile."""
        profile = IntegrationProfileRepository.update(
            db, profile_id, enabled=False
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )
        return self._to_response(profile)

    async def test_connection(
        self, db: Session, profile_id: int
    ) -> IntegrationTestResponse:
        """Test connection for an integration profile without saving."""
        profile = IntegrationProfileRepository.get_by_id(db, profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )

        try:
            result = await self._test_provider(profile)
        except Exception as e:
            logger.error("Connection test failed: %s", e)
            IntegrationProfileRepository.update(
                db,
                profile_id,
                last_test=datetime.now(UTC),
                last_error=str(e),
            )
            return IntegrationTestResponse(
                success=False, error=str(e)
            )

        now = datetime.now(UTC)
        update_kwargs: dict = {"last_test": now}

        if result.get("connected"):
            update_kwargs["last_success"] = now
            update_kwargs["last_error"] = None
        else:
            update_kwargs["last_error"] = result.get(
                "error", "Unknown error"
            )

        IntegrationProfileRepository.update(
            db, profile_id, **update_kwargs
        )

        return IntegrationTestResponse(
            success=result.get("connected", False),
            latency_ms=result.get("latency_ms"),
            message=result.get("message"),
            version=result.get("version"),
            error=result.get("error"),
            details=result,
        )

    # ------------------------------------------------------------------ #
    # Provider Injection                                                  #
    # ------------------------------------------------------------------ #

    async def _test_provider(
        self, profile: IntegrationProfile
    ) -> dict:
        """Dispatch connection test to the appropriate provider."""
        if profile.integration_type == "zabbix":
            return await self._test_zabbix(profile)
        elif profile.integration_type == "active_directory":
            return await self._test_ad(profile)
        elif profile.integration_type == "microsoft_365":
            return await self._test_m365(profile)
        else:
            return {
                "connected": False,
                "error": f"Unknown type: {profile.integration_type}",
            }

    async def _test_zabbix(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Zabbix connection using profile config."""
        from app.providers.zabbix.mock_provider import MockZabbixProvider

        provider = MockZabbixProvider()
        return await provider.test_connection()

    async def _test_ad(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Active Directory connection using profile config."""
        from app.providers.identity.ad_provider import (
            MockActiveDirectoryProvider,
        )

        provider = MockActiveDirectoryProvider()
        return await provider.test_connection()

    async def _test_m365(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Microsoft 365 connection using profile config."""
        from app.providers.identity.m365_provider import (
            MockMicrosoft365Provider,
        )

        provider = MockMicrosoft365Provider()
        return await provider.test_connection()

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _to_response(
        self, profile: IntegrationProfile
    ) -> IntegrationProfileResponse:
        """Convert an ORM profile to a response with masked secrets."""
        return IntegrationProfileResponse(
            id=profile.id,
            name=profile.name,
            integration_type=profile.integration_type,
            description=profile.description,
            enabled=profile.enabled,
            base_url=profile.base_url,
            username=profile.username,
            tenant_id=profile.tenant_id,
            client_id=profile.client_id,
            authority_url=profile.authority_url,
            domain=profile.domain,
            base_dn=profile.base_dn,
            use_ssl=profile.use_ssl,
            verify_ssl=profile.verify_ssl,
            timeout=profile.timeout,
            poll_interval=profile.poll_interval,
            last_test=profile.last_test,
            last_success=profile.last_success,
            last_error=profile.last_error,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


integration_service = IntegrationService()
