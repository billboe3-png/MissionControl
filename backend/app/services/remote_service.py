"""
Mission Control Remote Service

Business logic for remote operations: host management,
connection testing, command execution, and history.

Sprint 2.1.0 - Remote Operations Framework.
"""

import logging
from datetime import UTC
from datetime import datetime

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.repositories.command_history_repository import CommandHistoryRepository
from app.repositories.credential_profile_repository import CredentialProfileRepository
from app.repositories.remote_host_repository import RemoteHostRepository
from app.schemas.credential_profile import CredentialProfileCreate
from app.schemas.credential_profile import CredentialProfileListResponse
from app.schemas.credential_profile import CredentialProfileResponse
from app.schemas.credential_profile import CredentialProfileUpdate
from app.schemas.remote_command import CommandHistoryItem
from app.schemas.remote_command import RemoteExecuteRequest
from app.schemas.remote_command import RemoteExecuteResponse
from app.schemas.remote_command import RemoteHistoryResponse
from app.schemas.remote_command import RemoteTestConnectionRequest
from app.schemas.remote_command import RemoteTestConnectionResponse
from app.schemas.remote_host import RemoteHostCreate
from app.schemas.remote_host import RemoteHostListResponse
from app.schemas.remote_host import RemoteHostResponse
from app.schemas.remote_host import RemoteHostUpdate
from app.providers.remote.provider_factory import get_remote_provider

logger = logging.getLogger(__name__)


class RemoteService:
    """Remote operations business logic layer."""

    # ------------------------------------------------------------------ #
    # Host CRUD                                                           #
    # ------------------------------------------------------------------ #

    async def get_hosts(
        self,
        db: Session,
        search: str | None = None,
    ) -> RemoteHostListResponse:
        """Return all remote hosts with optional search filter."""
        logger.info("Fetching remote hosts (search=%s)", search)
        hosts = RemoteHostRepository.search(db, search)
        enriched = RemoteHostRepository.attach_credential_names(db, hosts)
        items = [RemoteHostResponse(**h) for h in enriched]
        return RemoteHostListResponse(count=len(items), items=items)

    async def get_host_by_id(
        self, db: Session, host_id: int
    ) -> RemoteHostResponse:
        """Return a single remote host by identifier."""
        logger.info("Fetching remote host id=%s", host_id)
        host = RemoteHostRepository.get_by_id(db, host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        enriched = RemoteHostRepository.attach_credential_names(db, [host])
        return RemoteHostResponse(**enriched[0])

    async def create_host(
        self, db: Session, data: RemoteHostCreate
    ) -> RemoteHostResponse:
        """Create a new remote host."""
        logger.info("Creating remote host: %s", data.name)

        if data.credential_profile_id is not None:
            profile = CredentialProfileRepository.get_by_id(
                db, data.credential_profile_id
            )
            if profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Credential profile not found",
                )

        if data.connection_type not in ("ssh", "winrm"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="connection_type must be 'ssh' or 'winrm'",
            )

        host = RemoteHostRepository.create(db, data)
        enriched = RemoteHostRepository.attach_credential_names(db, [host])
        return RemoteHostResponse(**enriched[0])

    async def update_host(
        self,
        db: Session,
        host_id: int,
        data: RemoteHostUpdate,
    ) -> RemoteHostResponse:
        """Update an existing remote host."""
        logger.info("Updating remote host id=%s", host_id)

        existing = RemoteHostRepository.get_by_id(db, host_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )

        if data.credential_profile_id is not None:
            profile = CredentialProfileRepository.get_by_id(
                db, data.credential_profile_id
            )
            if profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Credential profile not found",
                )

        if data.connection_type is not None:
            if data.connection_type not in ("ssh", "winrm"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="connection_type must be 'ssh' or 'winrm'",
                )

        updated = RemoteHostRepository.update(db, host_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        enriched = RemoteHostRepository.attach_credential_names(db, [updated])
        return RemoteHostResponse(**enriched[0])

    async def delete_host(self, db: Session, host_id: int) -> None:
        """Delete a remote host by identifier."""
        logger.info("Deleting remote host id=%s", host_id)
        deleted = RemoteHostRepository.delete(db, host_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )

    # ------------------------------------------------------------------ #
    # Credential Profile CRUD                                             #
    # ------------------------------------------------------------------ #

    async def get_credentials(
        self, db: Session
    ) -> CredentialProfileListResponse:
        """Return all credential profiles."""
        logger.info("Fetching credential profiles")
        profiles = CredentialProfileRepository.get_all(db)
        items = [
            CredentialProfileResponse.model_validate(p) for p in profiles
        ]
        return CredentialProfileListResponse(count=len(items), items=items)

    async def get_credential_by_id(
        self, db: Session, profile_id: int
    ) -> CredentialProfileResponse:
        """Return a single credential profile by identifier."""
        logger.info("Fetching credential profile id=%s", profile_id)
        profile = CredentialProfileRepository.get_by_id(db, profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential profile not found",
            )
        return CredentialProfileResponse.model_validate(profile)

    async def create_credential(
        self, db: Session, data: CredentialProfileCreate
    ) -> CredentialProfileResponse:
        """Create a new credential profile."""
        logger.info("Creating credential profile: %s", data.name)

        existing = CredentialProfileRepository.get_by_name(db, data.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Credential profile already exists",
            )

        if data.authentication_type not in (
            "password",
            "ssh_key",
            "ntlm",
            "basic",
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="authentication_type must be password, ssh_key, ntlm, or basic",
            )

        profile = CredentialProfileRepository.create(db, data)
        return CredentialProfileResponse.model_validate(profile)

    async def update_credential(
        self,
        db: Session,
        profile_id: int,
        data: CredentialProfileUpdate,
    ) -> CredentialProfileResponse:
        """Update an existing credential profile."""
        logger.info("Updating credential profile id=%s", profile_id)

        existing = CredentialProfileRepository.get_by_id(db, profile_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential profile not found",
            )

        if data.name is not None:
            normalized_new = data.name.strip().lower()
            normalized_existing = existing.name.strip().lower()
            if normalized_new != normalized_existing:
                duplicate = CredentialProfileRepository.get_by_name(
                    db, data.name
                )
                if duplicate is not None and duplicate.id != profile_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Credential profile name already exists",
                    )

        if data.authentication_type is not None:
            if data.authentication_type not in (
                "password",
                "ssh_key",
                "ntlm",
                "basic",
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="authentication_type must be password, ssh_key, ntlm, or basic",
                )

        updated = CredentialProfileRepository.update(db, profile_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential profile not found",
            )
        return CredentialProfileResponse.model_validate(updated)

    async def delete_credential(
        self, db: Session, profile_id: int
    ) -> None:
        """Delete a credential profile by identifier."""
        logger.info("Deleting credential profile id=%s", profile_id)
        deleted = CredentialProfileRepository.delete(db, profile_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential profile not found",
            )

    # ------------------------------------------------------------------ #
    # Connection Testing                                                  #
    # ------------------------------------------------------------------ #

    async def test_connection(
        self,
        db: Session,
        request: RemoteTestConnectionRequest,
    ) -> RemoteTestConnectionResponse:
        """
        Test connectivity to a remote host.

        Loads the host and credential profile, then delegates
        to the appropriate provider (SSH or WinRM).
        """
        logger.info(
            "Testing connection for host id=%s", request.host_id
        )

        host = RemoteHostRepository.get_by_id(db, request.host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )

        if not host.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Remote host is disabled",
            )

        username = None
        password = None
        ssh_key = None

        if host.credential_profile_id is not None:
            profile = CredentialProfileRepository.get_by_id(
                db, host.credential_profile_id
            )
            if profile is not None:
                username = profile.username
                password = profile.password
                ssh_key = profile.ssh_key

        provider = get_remote_provider(host.connection_type)
        result = await provider.test_connection(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            ip_address=host.ip_address,
        )

        return RemoteTestConnectionResponse(
            success=result["success"],
            latency_ms=result["latency_ms"],
            message=result["message"],
            host=host.name,
            connection_type=host.connection_type,
            timestamp=datetime.now(UTC).isoformat(),
        )

    # ------------------------------------------------------------------ #
    # Command Execution                                                   #
    # ------------------------------------------------------------------ #

    async def execute_command(
        self,
        db: Session,
        request: RemoteExecuteRequest,
    ) -> RemoteExecuteResponse:
        """
        Execute a command on a remote host.

        Validates the host, delegates to the provider, and records
        the result in command_history.
        """
        logger.info(
            "Executing command on host id=%s: %s",
            request.host_id,
            request.command,
        )

        host = RemoteHostRepository.get_by_id(db, request.host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )

        if not host.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Remote host is disabled",
            )

        valid_shells = ("bash", "powershell", "cmd")
        if request.shell not in valid_shells:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"shell must be one of: {', '.join(valid_shells)}",
            )

        username = None
        password = None
        ssh_key = None

        if host.credential_profile_id is not None:
            profile = CredentialProfileRepository.get_by_id(
                db, host.credential_profile_id
            )
            if profile is not None:
                username = profile.username
                password = profile.password
                ssh_key = profile.ssh_key

        provider = get_remote_provider(host.connection_type)
        result = await provider.execute_command(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            command=request.command,
            shell=request.shell,
            ip_address=host.ip_address,
        )

        CommandHistoryRepository.create(
            db=db,
            host_id=host.id,
            command=request.command,
            shell=request.shell,
            stdout=result["stdout"],
            stderr=result["stderr"],
            exit_code=result["exit_code"],
            success=result["exit_code"] == 0,
            duration_ms=result["duration_ms"],
            executed_by=username,
        )

        return RemoteExecuteResponse(
            host=host.name,
            connection_type=host.connection_type,
            command=request.command,
            stdout=result["stdout"],
            stderr=result["stderr"],
            exit_code=result["exit_code"],
            success=result["exit_code"] == 0,
            duration_ms=result["duration_ms"],
            timestamp=datetime.now(UTC).isoformat(),
        )

    # ------------------------------------------------------------------ #
    # Command History                                                     #
    # ------------------------------------------------------------------ #

    async def get_history(
        self,
        db: Session,
        search: str | None = None,
        host_id: int | None = None,
        success: bool | None = None,
        limit: int = 50,
    ) -> RemoteHistoryResponse:
        """Return command history with optional filters."""
        logger.info(
            "Fetching command history (search=%s, host=%s, success=%s)",
            search,
            host_id,
            success,
        )
        records = CommandHistoryRepository.get_filtered(
            db, search, host_id, success, limit
        )
        enriched = CommandHistoryRepository.attach_host_names(db, records)
        items = [CommandHistoryItem(**r) for r in enriched]
        return RemoteHistoryResponse(count=len(items), items=items)


remote_service = RemoteService()
