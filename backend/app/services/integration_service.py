"""
Mission Control Integration Service

Business logic for integration management: CRUD, connection testing,
encryption/decryption of secrets, and provider injection.

Sprint 2.3.1 - Integration Management (Production Configuration UI).
"""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CredentialCipher
from app.models.db.integration_profile import IntegrationProfile
from app.plugins.installed.official_unifi.bridge import (
    delete_profile_controllers as _unifi_delete_controllers,
)
from app.plugins.installed.official_unifi.bridge import (
    sync_profile_to_controllers as _unifi_sync_controllers,
)
from app.providers.hyperv.provider_factory import reset_hyperv_provider
from app.providers.proxmox.provider_factory import reset_proxmox_provider
from app.repositories.agent_repository import AgentCommandRepository
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
        valid_types = ("zabbix", "active_directory", "microsoft_365", "hyperv", "proxmox", "veeam", "unifi")
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
            "agent_id": data.agent_id,
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
            "ssh_host": data.ssh_host,
            "ssh_port": data.ssh_port,
            "ssh_username": data.ssh_username,
            "ssh_password_encrypted": _encrypt(data.ssh_password),
            "data_source": data.data_source,
            "verify_ssl": data.verify_ssl,
            "timeout": data.timeout,
            "poll_interval": data.poll_interval,
        }

        profile = IntegrationProfileRepository.create(
            db, data.name, data.integration_type, **kwargs
        )
        if data.integration_type == "zabbix":
            self._reset_zabbix_singleton()
        if data.integration_type == "hyperv":
            reset_hyperv_provider(profile.id)
        if data.integration_type == "proxmox":
            reset_proxmox_provider()
        if data.integration_type == "veeam":
            self._reset_veeam_singleton()
        if data.integration_type == "unifi":
            _unifi_sync_controllers(db, profile)
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

        if "ssh_password" in updates:
            sp = updates.pop("ssh_password")
            if sp == "" or sp is None:
                updates["ssh_password_encrypted"] = (
                    existing.ssh_password_encrypted
                )
            else:
                updates["ssh_password_encrypted"] = _encrypt(sp)

        profile = IntegrationProfileRepository.update(
            db, profile_id, **updates
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )

        # If connection-identifying settings changed, clear the previously
        # cached test result so the UI stops reporting a stale "Connected"
        # status from the old target/host (e.g. after fixing an IP).
        connection_fields = (
            "base_url", "ssh_host", "ssh_port", "ssh_username",
            "domain", "username", "verify_ssl", "timeout", "use_ssl",
        )
        if any(f in updates for f in connection_fields):
            IntegrationProfileRepository.update(
                db, profile_id, last_success=None, last_error=None,
            )
            profile.last_success = None
            profile.last_error = None

        if profile.integration_type == "zabbix":
            self._reset_zabbix_singleton()
        if profile.integration_type == "hyperv":
            reset_hyperv_provider(profile.id)
        if profile.integration_type == "proxmox":
            reset_proxmox_provider()
        if profile.integration_type == "veeam":
            self._reset_veeam_singleton()
        if profile.integration_type == "unifi":
            _unifi_sync_controllers(db, profile)
        return self._to_response(profile)

    async def delete_profile(
        self, db: Session, profile_id: int
    ) -> None:
        """Delete an integration profile."""
        existing = IntegrationProfileRepository.get_by_id(db, profile_id)
        deleted = IntegrationProfileRepository.delete(db, profile_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration profile not found",
            )
        if existing and existing.integration_type == "zabbix":
            self._reset_zabbix_singleton()
        if existing and existing.integration_type == "hyperv":
            reset_hyperv_provider(profile_id)
        if existing and existing.integration_type == "proxmox":
            reset_proxmox_provider()
        if existing and existing.integration_type == "veeam":
            self._reset_veeam_singleton()
        if existing and existing.integration_type == "unifi":
            _unifi_delete_controllers(db, profile_id)

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
        if profile.integration_type == "zabbix":
            self._reset_zabbix_singleton()
        if profile.integration_type == "hyperv":
            reset_hyperv_provider(profile.id)
        if profile.integration_type == "proxmox":
            reset_proxmox_provider()
        if profile.integration_type == "veeam":
            self._reset_veeam_singleton()
        if profile.integration_type == "unifi":
            _unifi_sync_controllers(db, profile)
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
        if profile.integration_type == "zabbix":
            self._reset_zabbix_singleton()
        if profile.integration_type == "hyperv":
            reset_hyperv_provider(profile.id)
        if profile.integration_type == "proxmox":
            reset_proxmox_provider()
        if profile.integration_type == "veeam":
            self._reset_veeam_singleton()
        if profile.integration_type == "unifi":
            _unifi_sync_controllers(db, profile)
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
            result = await self._test_profile(db, profile)
        except Exception as e:
            logger.error("Connection test failed: %s", e)
            IntegrationProfileRepository.update(
                db,
                profile_id,
                last_test=datetime.now(UTC),
                last_error=str(e),
            )
            return IntegrationTestResponse(success=False, error=str(e))

        now = datetime.now(UTC)
        update_kwargs: dict = {"last_test": now}
        if result.get("connected"):
            update_kwargs["last_success"] = now
            update_kwargs["last_error"] = None
        else:
            update_kwargs["last_error"] = result.get("error", "Unknown error")

        IntegrationProfileRepository.update(db, profile_id, **update_kwargs)

        return IntegrationTestResponse(
            success=result.get("connected", False),
            latency_ms=result.get("latency_ms"),
            message=str(result.get("message")) if result.get("message") else None,
            version=str(result.get("version")) if result.get("version") else None,
            error=str(result.get("error")) if result.get("error") else None,
            details=result,
        )

    # ------------------------------------------------------------------ #
    # Provider Injection                                                  #
    # ------------------------------------------------------------------ #

    async def _test_profile(self, db: Session, profile: IntegrationProfile) -> dict:
        if profile.agent_id:
            return await self._test_via_agent(db, profile)
        return await self._test_provider(profile)

    async def _test_via_agent(
        self, db: Session, profile: IntegrationProfile
    ) -> dict:
        from app.schemas.agent import AgentCommandDispatchRequest
        from app.services.agent_service import AgentService

        agent_service = AgentService()
        cmd = AgentCommandDispatchRequest(
            agent_id=profile.agent_id,
            command_type="integration_test",
            command=str(profile.integration_type or "").lower(),
            integration_profile={
                "base_url": profile.base_url,
                "username": profile.username,
                "password": _decrypt(profile.encrypted_secret),
                "verify_ssl": profile.verify_ssl,
                "timeout": profile.timeout,
                "tenant_id": profile.tenant_id,
                "client_id": profile.client_id,
                "domain": profile.domain,
                "base_dn": profile.base_dn,
                "use_ssl": profile.use_ssl,
                "data_source": profile.data_source,
                "ssh_host": profile.ssh_host,
                "ssh_port": profile.ssh_port,
                "ssh_username": profile.ssh_username,
            },
            timeout=max((profile.timeout or 30) + 5, 90),
            requested_by="integration_test",
        )
        dispatch = await agent_service.dispatch_command(db, cmd)
        pending = AgentCommandRepository.get_pending_for_agent(db, profile.agent_id)
        [c for c in pending if c.command_type == "integration_test" and c.command == profile.integration_type and c.status == "dispatched"]
        timeout = max(profile.timeout or 30, 60)
        datetime.now(UTC)
        target = dispatch.id
        poll = 0.2
        waited = 0.0
        cmd = None

        while waited < timeout:
            cand = AgentCommandRepository.get_by_id(db, target)
            if not cand or cand.status in {"completed", "failed"}:
                cmd = cand
                break
            cmd = cand
            if cmd.status in {"completed", "failed"}:
                break
            await asyncio.sleep(min(poll, 1.0))
            waited += min(poll, 1.0)

        if cmd is None or cmd.status not in {"completed", "failed"}:
            return {"connected": False, "error": f"Timed out waiting for agent result after {timeout}s"}

        success = bool(cmd.success)
        stderr = (cmd.stdout or "") + ("\n" + cmd.stderr if cmd.stderr else "")
        error = cmd.error_message or (stderr.strip() if not success else None)
        details: dict[str, object] = {
            "agent_id": profile.agent_id,
            "command_id": target,
            "status": cmd.status,
            "agent_result": cmd.stdout or cmd.stderr,
            "duration_ms": cmd.duration_ms,
        }
        if success:
            return {"connected": True, "message": "Agent test succeeded", "details": details}
        return {"connected": False, "error": error or "Agent test failed", "details": details}

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
        elif profile.integration_type == "hyperv":
            return await self._test_hyperv(profile)
        elif profile.integration_type == "proxmox":
            return await self._test_proxmox(profile)
        elif profile.integration_type == "veeam":
            return await self._test_veeam(profile)
        elif profile.integration_type == "unifi":
            return await self._test_unifi(profile)
        else:
            return {
                "connected": False,
                "error": f"Unknown type: {profile.integration_type}",
            }

    async def _test_zabbix(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Zabbix connection using profile credentials."""
        if not profile.base_url:
            return {
                "connected": False,
                "error": "Zabbix URL (base_url) is required",
            }
        if not profile.username:
            return {
                "connected": False,
                "error": "Zabbix username is required",
            }

        from app.providers.zabbix.zabbix_provider import (
            ApiZabbixProvider,
        )

        password = _decrypt(profile.encrypted_secret)
        provider = ApiZabbixProvider(
            url=profile.base_url,
            username=profile.username,
            password=password,
            verify_ssl=profile.verify_ssl,
            timeout=profile.timeout,
        )
        return await provider.test_connection()

    async def _test_ad(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Active Directory connection using profile config."""
        from app.providers.identity.ldap_ad_provider import (
            LDAPActiveDirectoryProvider,
        )

        password = _decrypt(profile.encrypted_secret) or ""
        config = {
            "server": profile.domain or "",
            "port": 636 if profile.use_ssl else 389,
            "use_ssl": profile.use_ssl,
            "username": profile.username or "",
            "password": password,
            "base_dn": profile.base_dn or "",
        }
        provider = LDAPActiveDirectoryProvider(config=config)
        return await provider.test_connection()

    async def _test_m365(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Microsoft 365 connection using profile config."""
        from app.providers.identity.graph_m365_provider import (
            GraphMicrosoft365Provider,
        )

        if not profile.tenant_id:
            return {"connected": False, "error": "Tenant ID is required"}
        if not profile.client_id:
            return {"connected": False, "error": "Client ID is required"}

        client_secret = _decrypt(profile.client_secret_encrypted) or ""
        config = {
            "tenant_id": profile.tenant_id,
            "client_id": profile.client_id,
            "client_secret": client_secret,
        }
        provider = GraphMicrosoft365Provider(config=config)
        return await provider.test_connection()

    async def _test_hyperv(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Hyper-V connection using profile config."""
        from app.providers.hyperv.hyperv_provider import HyperVPowerShellProvider

        password = _decrypt(profile.encrypted_secret) or ""
        transport = profile.domain or "winrm"
        port = 22 if transport == "ssh" else 5985
        provider = HyperVPowerShellProvider(
            host=profile.base_url or "localhost",
            port=port,
            username=profile.username or "",
            password=password,
            timeout=profile.timeout or 30,
            transport=transport,
        )
        return await provider.test_connection()

    async def _test_proxmox(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Proxmox connection using profile config."""
        from app.providers.proxmox.proxmox_provider import ProxmoxRESTProvider

        token_secret = _decrypt(profile.encrypted_secret) or ""
        token_id = profile.username or ""
        base_url = profile.base_url or ""

        if not base_url:
            return {"connected": False, "error": "Proxmox server URL is required"}
        if not token_id:
            return {"connected": False, "error": "Proxmox API token ID is required"}

        full_token = f"{token_id}={token_secret}" if token_secret else token_id

        provider = ProxmoxRESTProvider(
            base_url=base_url,
            token=full_token,
            timeout=profile.timeout or 30,
            verify_ssl=profile.verify_ssl if profile.verify_ssl is not None else True,
        )
        return await provider.test_connection()

    async def _test_veeam(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test Veeam B&R connection using profile config.

        Supports both REST API (Enterprise) and PowerShell (Community Edition).
        Delegates to provider_factory which handles db_type detection.
        """
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.providers.veeam.provider_factory import _build_provider

        settings = get_settings()
        CredentialCipher(settings.missioncontrol_secret_key)
        try:
            provider = _build_provider(profile)
        except ValueError as e:
            msg = str(e)
            if "Decryption failed" in msg:
                return {
                    "connected": False,
                    "error": "Stored Veeam credentials could not be decrypted with the current key. "
                    "Re-save the SSH password for this integration to re-encrypt it.",
                }
            return {"connected": False, "error": "Veeam server URL or SSH connection is required"}
        if provider is None:
            return {"connected": False, "error": "Veeam server URL or SSH connection is required"}
        return await provider.test_connection()

    async def _test_unifi(
        self, profile: IntegrationProfile
    ) -> dict:
        """Test UniFi Site Manager connection using the saved API key."""
        from app.plugins.installed.official_unifi.api import UniFiApiClient

        api_key = _decrypt(profile.encrypted_secret) or ""
        if not api_key:
            return {
                "connected": False,
                "error": "UniFi Site Manager API key is required",
            }

        is_cloud = profile.base_url in ("https://api.ui.com", "https://api.ui.com/", "https://unifi.ui.com", "https://unifi.ui.com/", "", None)
        controller_url = "https://api.ui.com" if is_cloud else (profile.base_url or "")
        controller_type = "cloud" if is_cloud else "local"

        client = UniFiApiClient(
            url=controller_url,
            api_key=api_key,
            verify_ssl=profile.verify_ssl,
            timeout=profile.timeout or 30,
            controller_type=controller_type,
        )
        try:
            result = await client.test_connection()
        finally:
            await client.close()
        if result.get("connected"):
            return {
                "connected": True,
                "message": f"Connected to UniFi{' Site Manager' if is_cloud else ' controller'}",
            }
        return {
            "connected": False,
            "error": result.get("error", "UniFi connection test failed"),
        }

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _reset_zabbix_singleton() -> None:
        """Reset the cached Zabbix provider so profile changes take effect."""
        from app.providers.zabbix.provider_factory import (
            reset_zabbix_provider,
        )

        reset_zabbix_provider()
        logger.info("Zabbix provider singleton reset after profile change")

    @staticmethod
    def _reset_veeam_singleton() -> None:
        """Reset the cached Veeam provider so profile changes take effect."""
        from app.providers.veeam.provider_factory import (
            reset_veeam_provider,
        )

        reset_veeam_provider()
        logger.info("Veeam provider singleton reset after profile change")

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
            ssh_host=profile.ssh_host,
            ssh_port=profile.ssh_port,
            ssh_username=profile.ssh_username,
            has_ssh_password=bool(profile.ssh_password_encrypted),
            data_source=profile.data_source or "both",
            verify_ssl=profile.verify_ssl,
            timeout=profile.timeout,
            poll_interval=profile.poll_interval,
            last_test=profile.last_test,
            last_success=profile.last_success,
            last_error=profile.last_error,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def get_dashboard_summary(self, db: Session) -> dict:
        """Dashboard-friendly integration summary. Never raises."""
        try:
            profiles = IntegrationProfileRepository.get_all(db)
            items = []
            for p in profiles:
                items.append({
                    "id": p.id,
                    "name": p.name,
                    "type": p.integration_type,
                    "enabled": p.enabled,
                    "connected": (
                        p.last_success is not None
                        and p.last_error is None
                    ),
                    "last_test": (
                        p.last_test.isoformat()
                        if p.last_test
                        else None
                    ),
                })
            return {
                "count": len(items),
                "items": items,
            }
        except Exception as e:
            logger.warning(
                "Dashboard: integrations summary failed: %s", e
            )
            return {"count": 0, "items": []}


integration_service = IntegrationService()
