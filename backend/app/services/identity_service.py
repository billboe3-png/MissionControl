"""
Mission Control Identity Service

Business logic for identity operations: Active Directory
and Microsoft 365 data retrieval through provider layer.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging

from sqlalchemy.orm import Session

from app.providers.identity.provider_factory import (
    get_microsoft365_provider,
)

logger = logging.getLogger(__name__)


def _get_ad_provider_from_db(db: Session):
    """Get AD provider from the active IntegrationProfile, falling back to env/mock."""
    try:
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.models.db.integration_profile import IntegrationProfile
        from app.providers.identity.ldap_ad_provider import (
            LDAPActiveDirectoryProvider,
        )

        settings = get_settings()
        profile = (
            db.query(IntegrationProfile)
            .filter(
                IntegrationProfile.integration_type == "active_directory",
                IntegrationProfile.enabled == True,
            )
            .order_by(IntegrationProfile.id.desc())
            .first()
        )

        if profile and profile.domain and profile.username:
            password = ""
            if profile.encrypted_secret:
                try:
                    cipher = CredentialCipher(settings.missioncontrol_secret_key)
                    password = cipher.decrypt(profile.encrypted_secret)
                except Exception:
                    pass

            config = {
                "server": profile.domain,
                "port": 636 if profile.use_ssl else 389,
                "use_ssl": profile.use_ssl,
                "username": profile.username,
                "password": password,
                "base_dn": profile.base_dn or "",
            }
            return LDAPActiveDirectoryProvider(config=config)
    except Exception as e:
        logger.debug("Could not load AD profile from DB: %s", e)

    from app.providers.identity.provider_factory import (
        get_active_directory_provider,
    )
    return get_active_directory_provider()


class IdentityService:
    """
    Service layer for identity operations.

    Orchestrates AD and M365 provider calls and formats
    responses for the API layer.
    """

    def __init__(self) -> None:
        self._m365 = get_microsoft365_provider()

    def _get_ad(self, db: Session):
        return _get_ad_provider_from_db(db)

    # ------------------------------------------------------------------ #
    # Active Directory                                                    #
    # ------------------------------------------------------------------ #

    async def ad_test_connection(self, db: Session) -> dict:
        """Test AD connectivity."""
        return await self._get_ad(db).test_connection()

    async def ad_get_summary(self, db: Session) -> dict:
        """Get AD domain and forest summary."""
        return await self._get_ad(db).get_summary()

    async def ad_get_users(self, db: Session) -> dict:
        """Get AD users."""
        return await self._get_ad(db).get_users()

    async def ad_get_groups(self, db: Session) -> dict:
        """Get AD groups."""
        return await self._get_ad(db).get_groups()

    async def ad_get_devices(self, db: Session) -> dict:
        """Get AD computers/devices."""
        return await self._get_ad(db).get_devices()

    async def ad_get_health(self, db: Session) -> dict:
        """Get AD health and replication status."""
        return await self._get_ad(db).get_health()

    async def ad_reset_password(self, db: Session, sam_account_name: str, new_password: str) -> dict:
        """Reset a user's AD password."""
        return await self._get_ad(db).reset_password(sam_account_name, new_password)

    async def ad_unlock_account(self, db: Session, sam_account_name: str) -> dict:
        """Unlock a locked AD account."""
        return await self._get_ad(db).unlock_account(sam_account_name)

    async def ad_enable_account(self, db: Session, sam_account_name: str) -> dict:
        """Enable a disabled AD account."""
        return await self._get_ad(db).enable_account(sam_account_name)

    async def ad_disable_account(self, db: Session, sam_account_name: str) -> dict:
        """Disable an AD account."""
        return await self._get_ad(db).disable_account(sam_account_name)

    async def ad_rename_user(self, db: Session, sam_account_name: str, display_name: str, first_name: str | None = None, last_name: str | None = None) -> dict:
        """Rename an AD user."""
        return await self._get_ad(db).rename_user(sam_account_name, display_name, first_name, last_name)

    async def ad_get_user_groups(self, db: Session, sam_account_name: str) -> dict:
        """Get groups a user belongs to."""
        return await self._get_ad(db).get_user_groups(sam_account_name)

    async def ad_add_to_group(self, db: Session, sam_account_name: str, group_name: str) -> dict:
        """Add a user to a group."""
        return await self._get_ad(db).add_to_group(sam_account_name, group_name)

    async def ad_remove_from_group(self, db: Session, sam_account_name: str, group_name: str) -> dict:
        """Remove a user from a group."""
        return await self._get_ad(db).remove_from_group(sam_account_name, group_name)

    # ------------------------------------------------------------------ #
    # Microsoft 365                                                       #
    # ------------------------------------------------------------------ #

    async def m365_test_connection(self) -> dict:
        """Test M365 connectivity."""
        return await self._m365.test_connection()

    async def m365_get_summary(self) -> dict:
        """Get tenant summary."""
        return await self._m365.get_summary()

    async def m365_get_users(self) -> dict:
        """Get M365 users."""
        return await self._m365.get_users()

    async def m365_get_groups(self) -> dict:
        """Get M365 groups."""
        return await self._m365.get_groups()

    async def m365_get_devices(self) -> dict:
        """Get M365 managed devices."""
        return await self._m365.get_devices()

    async def m365_get_health(self) -> dict:
        """Get M365 service health."""
        return await self._m365.get_health()

    # ------------------------------------------------------------------ #
    # Combined Overview                                                   #
    # ------------------------------------------------------------------ #

    async def get_overview(self, db: Session) -> dict:
        """
        Get combined identity overview for the dashboard.

        Aggregates key metrics from both AD and M365 providers.
        """
        ad_summary = await self._get_ad(db).get_summary()
        ad_health = await self._get_ad(db).get_health()
        m365_summary = await self._m365.get_summary()
        m365_health = await self._m365.get_health()

        return {
            "success": True,
            "overview": {
                "ad": {
                    "connected": ad_summary.get("connected", False),
                    "domain": ad_summary.get("domain", {}).get("name", "N/A"),
                    "user_count": ad_summary.get("user_count", 0),
                    "group_count": ad_summary.get("group_count", 0),
                    "computer_count": ad_summary.get("computer_count", 0),
                    "health": ad_health.get("status", "unknown"),
                    "replication": ad_health.get("replication", {}),
                },
                "m365": {
                    "connected": m365_summary.get("connected", False),
                    "tenant": m365_summary.get("tenant", {}).get("display_name", "N/A"),
                    "licensed_users": m365_summary.get("licensed_users", 0),
                    "license_count": len(m365_summary.get("licenses", [])),
                    "health": m365_health.get("status", "unknown"),
                    "active_incidents": m365_health.get("active_incidents", 0),
                },
            },
        }


identity_service = IdentityService()
