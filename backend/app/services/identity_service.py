import json
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


def _get_ad_provider_from_db(db: Session, profile_id: int | None = None):
    """Get AD provider from an IntegrationProfile, preferring agent relay
    when the profile is bound to an agent, otherwise falling back to
    direct LDAP or env/mock."""
    try:
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.models.db.agent import Agent
        from app.models.db.integration_profile import IntegrationProfile
        from app.providers.identity.agent_ad_provider import (
            AgentActiveDirectoryProvider,
        )
        from app.providers.identity.ldap_ad_provider import (
            LDAPActiveDirectoryProvider,
        )

        settings = get_settings()

        if profile_id is not None:
            profile = (
                db.query(IntegrationProfile)
                .filter(IntegrationProfile.id == profile_id)
                .first()
            )
        else:
            profile = (
                db.query(IntegrationProfile)
                .filter(
                    IntegrationProfile.integration_type == "active_directory",
                    IntegrationProfile.enabled,
                )
                .order_by(IntegrationProfile.id.desc())
                .first()
            )

        if not profile:
            raise ValueError("No AD integration profile available")

        if profile.agent_id is not None:
            agent = (
                db.query(Agent)
                .filter(Agent.id == profile.agent_id)
                .first()
            )
            if agent and agent.inventory_json:
                try:
                    full_inv = json.loads(agent.inventory_json)
                    ad_inv = full_inv.get("plugins", {}).get("active_directory")
                    if ad_inv:
                        hostname = agent.name or full_inv.get("system", {}).get("hostname", "")
                        return AgentActiveDirectoryProvider(
                            inventory=ad_inv,
                            hostname=hostname or f"agent-{agent.id}",
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

        if profile.domain and profile.username:
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


def _get_m365_provider_from_db(db: Session, profile_id: int | None = None):
    """Get M365 provider from an IntegrationProfile, falling back to env/mock."""
    try:
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.models.db.integration_profile import IntegrationProfile
        from app.providers.identity.graph_m365_provider import (
            GraphMicrosoft365Provider,
        )

        settings = get_settings()

        if profile_id is not None:
            profile = (
                db.query(IntegrationProfile)
                .filter(IntegrationProfile.id == profile_id)
                .first()
            )
        else:
            profile = (
                db.query(IntegrationProfile)
                .filter(
                    IntegrationProfile.integration_type == "microsoft_365",
                    IntegrationProfile.enabled,
                )
                .order_by(IntegrationProfile.id.desc())
                .first()
            )

        if profile and profile.tenant_id and profile.client_id:
            client_secret = ""
            if profile.client_secret_encrypted:
                try:
                    cipher = CredentialCipher(settings.missioncontrol_secret_key)
                    client_secret = cipher.decrypt(profile.client_secret_encrypted)
                except Exception:
                    pass

            config = {
                "tenant_id": profile.tenant_id,
                "client_id": profile.client_id,
                "client_secret": client_secret,
            }
            return GraphMicrosoft365Provider(config=config)
    except Exception as e:
        logger.debug("Could not load M365 profile from DB: %s", e)

    return get_microsoft365_provider()


class IdentityService:
    """
    Service layer for identity operations.

    Orchestrates AD and M365 provider calls and formats
    responses for the API layer.
    """

    def __init__(self) -> None:
        pass

    def _get_ad(self, db: Session, profile_id: int | None = None):
        return _get_ad_provider_from_db(db, profile_id)

    def _get_m365(self, db: Session, profile_id: int | None = None):
        return _get_m365_provider_from_db(db, profile_id)

    # ------------------------------------------------------------------ #
    # Active Directory                                                    #
    # ------------------------------------------------------------------ #

    async def ad_test_connection(self, db: Session, profile_id: int | None = None) -> dict:
        """Test AD connectivity."""
        return await self._get_ad(db, profile_id).test_connection()

    async def ad_get_summary(self, db: Session, profile_id: int | None = None) -> dict:
        """Get AD domain and forest summary."""
        return await self._get_ad(db, profile_id).get_summary()

    async def ad_get_users(self, db: Session, profile_id: int | None = None) -> dict:
        """Get AD users."""
        return await self._get_ad(db, profile_id).get_users()

    async def ad_get_groups(self, db: Session, profile_id: int | None = None) -> dict:
        """Get AD groups."""
        return await self._get_ad(db, profile_id).get_groups()

    async def ad_get_devices(self, db: Session, profile_id: int | None = None) -> dict:
        """Get AD computers/devices."""
        return await self._get_ad(db, profile_id).get_devices()

    async def ad_get_health(self, db: Session, profile_id: int | None = None) -> dict:
        """Get AD health and replication status."""
        return await self._get_ad(db, profile_id).get_health()

    async def ad_reset_password(self, db: Session, sam_account_name: str, new_password: str, profile_id: int | None = None) -> dict:
        """Reset a user's AD password."""
        return await self._get_ad(db, profile_id).reset_password(sam_account_name, new_password)

    async def ad_unlock_account(self, db: Session, sam_account_name: str, profile_id: int | None = None) -> dict:
        """Unlock a locked AD account."""
        return await self._get_ad(db, profile_id).unlock_account(sam_account_name)

    async def ad_enable_account(self, db: Session, sam_account_name: str, profile_id: int | None = None) -> dict:
        """Enable a disabled AD account."""
        return await self._get_ad(db, profile_id).enable_account(sam_account_name)

    async def ad_disable_account(self, db: Session, sam_account_name: str, profile_id: int | None = None) -> dict:
        """Disable an AD account."""
        return await self._get_ad(db, profile_id).disable_account(sam_account_name)

    async def ad_rename_user(self, db: Session, sam_account_name: str, display_name: str, first_name: str | None = None, last_name: str | None = None, profile_id: int | None = None) -> dict:
        """Rename an AD user."""
        return await self._get_ad(db, profile_id).rename_user(sam_account_name, display_name, first_name, last_name)

    async def ad_get_user_groups(self, db: Session, sam_account_name: str, profile_id: int | None = None) -> dict:
        """Get groups a user belongs to."""
        return await self._get_ad(db, profile_id).get_user_groups(sam_account_name)

    async def ad_add_to_group(self, db: Session, sam_account_name: str, group_name: str, profile_id: int | None = None) -> dict:
        """Add a user to a group."""
        return await self._get_ad(db, profile_id).add_to_group(sam_account_name, group_name)

    async def ad_remove_from_group(self, db: Session, sam_account_name: str, group_name: str, profile_id: int | None = None) -> dict:
        """Remove a user from a group."""
        return await self._get_ad(db, profile_id).remove_from_group(sam_account_name, group_name)

    # ------------------------------------------------------------------ #
    # Microsoft 365                                                       #
    # ------------------------------------------------------------------ #

    async def m365_test_connection(self, db: Session, profile_id: int | None = None) -> dict:
        """Test M365 connectivity."""
        return await self._get_m365(db, profile_id).test_connection()

    async def m365_get_summary(self, db: Session, profile_id: int | None = None) -> dict:
        """Get tenant summary."""
        return await self._get_m365(db, profile_id).get_summary()

    async def m365_get_users(self, db: Session, profile_id: int | None = None) -> dict:
        """Get M365 users."""
        return await self._get_m365(db, profile_id).get_users()

    async def m365_get_groups(self, db: Session, profile_id: int | None = None) -> dict:
        """Get M365 groups."""
        return await self._get_m365(db, profile_id).get_groups()

    async def m365_get_devices(self, db: Session, profile_id: int | None = None) -> dict:
        """Get M365 managed devices."""
        return await self._get_m365(db, profile_id).get_devices()

    async def m365_get_health(self, db: Session, profile_id: int | None = None) -> dict:
        """Get M365 service health."""
        return await self._get_m365(db, profile_id).get_health()

    # ------------------------------------------------------------------ #
    # Combined Overview                                                   #
    # ------------------------------------------------------------------ #

    async def get_overview(self, db: Session) -> dict:
        """
        Get combined identity overview for the dashboard.

        Aggregates key metrics from all enabled AD profiles and M365.
        """
        from app.repositories.integration_profile_repository import (
            IntegrationProfileRepository,
        )

        ad_profiles = IntegrationProfileRepository.get_all_enabled_by_type(
            db, "active_directory"
        )

        ad_entries = []
        for profile in ad_profiles:
            try:
                provider = self._get_ad(db, profile.id)
                summary = await provider.get_summary()
                health = await provider.get_health()
                ad_entries.append({
                    "profile_id": profile.id,
                    "profile_name": profile.name,
                    "connected": summary.get("connected", False),
                    "domain": summary.get("domain", {}).get("name") or profile.domain or profile.name,
                    "user_count": summary.get("user_count", 0),
                    "group_count": summary.get("group_count", 0),
                    "computer_count": summary.get("computer_count", 0),
                    "health": health.get("status", "unknown"),
                    "replication": health.get("replication", {}),
                })
            except Exception as e:
                logger.debug("AD overview for profile %s failed: %s", profile.id, e)
                ad_entries.append({
                    "profile_id": profile.id,
                    "profile_name": profile.name,
                    "connected": False,
                    "domain": profile.domain or profile.name,
                    "user_count": 0,
                    "group_count": 0,
                    "computer_count": 0,
                    "health": "unavailable",
                    "replication": {},
                })

        m365_summary = await self._get_m365(db).get_summary()
        m365_health = await self._get_m365(db).get_health()

        return {
            "success": True,
            "overview": {
                "ad": ad_entries,
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
