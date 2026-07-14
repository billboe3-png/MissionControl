"""
Mission Control Remote Service

Business logic for remote operations: host management,
connection testing, command execution, history, templates,
bulk execution, scheduled commands, file transfer, and metrics.

Sprint 2.1.8 - Remote Operations Finalization.
"""

import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CredentialCipher
from app.providers.remote.provider_factory import (
    get_remote_provider,
    get_session_metrics,
    record_command_executed,
)
from app.repositories.command_history_repository import CommandHistoryRepository
from app.repositories.command_template_repository import (
    CommandTemplateRepository,
)
from app.repositories.credential_profile_repository import (
    CredentialProfileRepository,
)
from app.repositories.remote_host_repository import RemoteHostRepository
from app.repositories.scheduled_command_repository import (
    ScheduledCommandRepository,
)
from app.schemas.bulk_command import (
    BulkExecuteRequest,
    BulkExecuteResponse,
    BulkExecuteResult,
    SessionMetricsResponse,
)
from app.schemas.command_template import (
    CommandTemplateCreate,
    CommandTemplateListResponse,
    CommandTemplateResponse,
    CommandTemplateUpdate,
)
from app.schemas.credential_profile import (
    CredentialProfileCreate,
    CredentialProfileListResponse,
    CredentialProfileResponse,
    CredentialProfileUpdate,
)
from app.schemas.file_transfer import (
    FileDeleteRequest,
    FileDownloadRequest,
    FileDownloadResponse,
    FileListResponse,
    FileMkdirRequest,
    FileListItem,
    FileTransferResponse,
    FileUploadRequest,
)
from app.schemas.remote_command import (
    CommandHistoryItem,
    RemoteExecuteRequest,
    RemoteExecuteResponse,
    RemoteHistoryResponse,
    RemoteTestConnectionRequest,
    RemoteTestConnectionResponse,
)
from app.schemas.remote_host import (
    RemoteHostCreate,
    RemoteHostListResponse,
    RemoteHostResponse,
    RemoteHostUpdate,
)
from app.schemas.scheduled_command import (
    ScheduledCommandCreate,
    ScheduledCommandListResponse,
    ScheduledCommandResponse,
    ScheduledCommandUpdate,
)

logger = logging.getLogger(__name__)


def _get_cipher() -> CredentialCipher:
    from app.core.config import get_settings
    settings = get_settings()
    return CredentialCipher(settings.missioncontrol_secret_key)


def _encrypt_credential(value: str | None) -> str | None:
    if not value:
        return None
    return _get_cipher().encrypt(value)


def _decrypt_credential(value: str | None) -> str | None:
    if not value:
        return None
    return _get_cipher().decrypt(value)


class RemoteService:
    # ------------------------------------------------------------------ #
    # Host CRUD                                                           #
    # ------------------------------------------------------------------ #

    async def get_hosts(
        self, db: Session, search: str | None = None,
    ) -> RemoteHostListResponse:
        hosts = RemoteHostRepository.search(db, search)
        enriched = RemoteHostRepository.attach_credential_names(db, hosts)
        items = [RemoteHostResponse(**h) for h in enriched]
        return RemoteHostListResponse(count=len(items), items=items)

    async def get_host_by_id(
        self, db: Session, host_id: int,
    ) -> RemoteHostResponse:
        host = RemoteHostRepository.get_by_id(db, host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        enriched = RemoteHostRepository.attach_credential_names(db, [host])
        return RemoteHostResponse(**enriched[0])

    async def create_host(
        self, db: Session, data: RemoteHostCreate,
    ) -> RemoteHostResponse:
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
        self, db: Session, host_id: int, data: RemoteHostUpdate,
    ) -> RemoteHostResponse:
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
        self, db: Session,
    ) -> CredentialProfileListResponse:
        profiles = CredentialProfileRepository.get_all(db)
        items = [
            CredentialProfileResponse.model_validate(p) for p in profiles
        ]
        return CredentialProfileListResponse(count=len(items), items=items)

    async def get_credential_by_id(
        self, db: Session, profile_id: int,
    ) -> CredentialProfileResponse:
        profile = CredentialProfileRepository.get_by_id(db, profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential profile not found",
            )
        return CredentialProfileResponse.model_validate(profile)

    async def create_credential(
        self, db: Session, data: CredentialProfileCreate,
    ) -> CredentialProfileResponse:
        existing = CredentialProfileRepository.get_by_name(db, data.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Credential profile already exists",
            )
        if data.authentication_type not in (
            "password", "ssh_key", "ntlm", "basic",
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="authentication_type must be password, ssh_key, ntlm, or basic",
            )
        profile = CredentialProfileRepository.create_encrypted(
            db, data,
            password_encrypted=_encrypt_credential(data.password),
            private_key_encrypted=_encrypt_credential(data.ssh_key),
            passphrase_encrypted=_encrypt_credential(data.passphrase),
        )
        return CredentialProfileResponse.model_validate(profile)

    async def update_credential(
        self, db: Session, profile_id: int, data: CredentialProfileUpdate,
    ) -> CredentialProfileResponse:
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
                "password", "ssh_key", "ntlm", "basic",
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="authentication_type must be password, ssh_key, ntlm, or basic",
                )
        password_encrypted = None
        private_key_encrypted = None
        passphrase_encrypted = None
        if data.password is not None:
            password_encrypted = (
                existing.password_encrypted if data.password == ""
                else _encrypt_credential(data.password)
            )
        if data.ssh_key is not None:
            private_key_encrypted = (
                existing.private_key_encrypted if data.ssh_key == ""
                else _encrypt_credential(data.ssh_key)
            )
        if data.passphrase is not None:
            passphrase_encrypted = (
                existing.passphrase_encrypted if data.passphrase == ""
                else _encrypt_credential(data.passphrase)
            )
        updated = CredentialProfileRepository.update_encrypted(
            db, profile_id, data,
            password_encrypted=password_encrypted,
            private_key_encrypted=private_key_encrypted,
            passphrase_encrypted=passphrase_encrypted,
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential profile not found",
            )
        return CredentialProfileResponse.model_validate(updated)

    async def delete_credential(
        self, db: Session, profile_id: int,
    ) -> None:
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
        self, db: Session, request: RemoteTestConnectionRequest,
    ) -> RemoteTestConnectionResponse:
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
                password = _decrypt_credential(profile.password_encrypted)
                ssh_key = _decrypt_credential(profile.private_key_encrypted)
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

    async def _resolve_credentials(
        self, db: Session, host,
    ) -> tuple[str | None, str | None, str | None]:
        """Decrypt and return (username, password, ssh_key) for a host."""
        username = None
        password = None
        ssh_key = None
        if host.credential_profile_id is not None:
            profile = CredentialProfileRepository.get_by_id(
                db, host.credential_profile_id
            )
            if profile is not None:
                username = profile.username
                password = _decrypt_credential(profile.password_encrypted)
                ssh_key = _decrypt_credential(profile.private_key_encrypted)
        return username, password, ssh_key

    async def execute_command(
        self,
        db: Session,
        request: RemoteExecuteRequest,
        execution_source: str = "manual",
        username_override: str | None = None,
    ) -> RemoteExecuteResponse:
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
        username, password, ssh_key = await self._resolve_credentials(db, host)
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
        record_command_executed(result["success"], result.get("duration_ms", 0))
        CommandHistoryRepository.create(
            db=db,
            host_id=host.id,
            command=request.command,
            shell=request.shell,
            stdout=result["stdout"],
            stderr=result["stderr"],
            exit_code=result["exit_code"],
            success=result["success"],
            duration_ms=result["duration_ms"],
            executed_by=username_override or username,
            credential_id=host.credential_profile_id,
            username=username,
            execution_source=execution_source,
        )
        return RemoteExecuteResponse(
            host=host.name,
            connection_type=host.connection_type,
            command=request.command,
            stdout=result["stdout"],
            stderr=result["stderr"],
            exit_code=result["exit_code"],
            success=result["success"],
            duration_ms=result["duration_ms"],
            timestamp=datetime.now(UTC).isoformat(),
        )

    # ------------------------------------------------------------------ #
    # Bulk Command Execution                                              #
    # ------------------------------------------------------------------ #

    async def bulk_execute(
        self, db: Session, request: BulkExecuteRequest,
    ) -> BulkExecuteResponse:
        results = []
        for host_id in request.host_ids:
            host = RemoteHostRepository.get_by_id(db, host_id)
            if host is None:
                results.append(BulkExecuteResult(
                    host_id=host_id,
                    host_name=f"Host #{host_id} (not found)",
                    success=False,
                    stdout="",
                    stderr="Host not found",
                    exit_code=-1,
                    duration_ms=0,
                ))
                continue
            if not host.enabled:
                results.append(BulkExecuteResult(
                    host_id=host_id,
                    host_name=host.name,
                    success=False,
                    stdout="",
                    stderr="Host is disabled",
                    exit_code=-1,
                    duration_ms=0,
                ))
                continue
            username, password, ssh_key = await self._resolve_credentials(db, host)
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
            record_command_executed(result["success"], result.get("duration_ms", 0))
            CommandHistoryRepository.create(
                db=db,
                host_id=host.id,
                command=request.command,
                shell=request.shell,
                stdout=result["stdout"],
                stderr=result["stderr"],
                exit_code=result["exit_code"],
                success=result["success"],
                duration_ms=result["duration_ms"],
                executed_by=username,
                credential_id=host.credential_profile_id,
                username=username,
                execution_source="bulk",
            )
            results.append(BulkExecuteResult(
                host_id=host_id,
                host_name=host.name,
                success=result["success"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                exit_code=result["exit_code"],
                duration_ms=result["duration_ms"],
            ))
        succeeded = sum(1 for r in results if r.success)
        return BulkExecuteResponse(
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )

    # ------------------------------------------------------------------ #
    # Command Templates                                                   #
    # ------------------------------------------------------------------ #

    async def get_templates(
        self, db: Session,
    ) -> CommandTemplateListResponse:
        templates = CommandTemplateRepository.get_all(db)
        items = [
            CommandTemplateResponse.model_validate(t) for t in templates
        ]
        return CommandTemplateListResponse(count=len(items), items=items)

    async def get_template_by_id(
        self, db: Session, template_id: int,
    ) -> CommandTemplateResponse:
        template = CommandTemplateRepository.get_by_id(db, template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command template not found",
            )
        return CommandTemplateResponse.model_validate(template)

    async def create_template(
        self, db: Session, data: CommandTemplateCreate,
    ) -> CommandTemplateResponse:
        existing = CommandTemplateRepository.get_by_name(db, data.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Template name already exists",
            )
        if data.protocol not in ("ssh", "winrm"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="protocol must be 'ssh' or 'winrm'",
            )
        template = CommandTemplateRepository.create(
            db, data.name, data.description, data.protocol,
            data.command, data.category,
        )
        return CommandTemplateResponse.model_validate(template)

    async def update_template(
        self, db: Session, template_id: int, data: CommandTemplateUpdate,
    ) -> CommandTemplateResponse:
        existing = CommandTemplateRepository.get_by_id(db, template_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command template not found",
            )
        if data.name is not None:
            normalized_new = data.name.strip().lower()
            normalized_existing = existing.name.strip().lower()
            if normalized_new != normalized_existing:
                dup = CommandTemplateRepository.get_by_name(db, data.name)
                if dup is not None and dup.id != template_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Template name already exists",
                    )
        update_data = data.model_dump(exclude_unset=True)
        template = CommandTemplateRepository.update(
            db, template_id, update_data
        )
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command template not found",
            )
        return CommandTemplateResponse.model_validate(template)

    async def delete_template(
        self, db: Session, template_id: int,
    ) -> None:
        deleted = CommandTemplateRepository.delete(db, template_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command template not found",
            )

    async def execute_template(
        self, db: Session, template_id: int, host_id: int,
    ) -> RemoteExecuteResponse:
        template = CommandTemplateRepository.get_by_id(db, template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command template not found",
            )
        request = RemoteExecuteRequest(
            host_id=host_id,
            command=template.command,
            shell="bash" if template.protocol == "ssh" else "powershell",
        )
        return await self.execute_command(
            db, request, execution_source="template"
        )

    # ------------------------------------------------------------------ #
    # Scheduled Commands                                                  #
    # ------------------------------------------------------------------ #

    async def get_schedules(
        self, db: Session,
    ) -> ScheduledCommandListResponse:
        schedules = ScheduledCommandRepository.get_all(db)
        enriched = ScheduledCommandRepository.attach_host_names(db, schedules)
        items = [ScheduledCommandResponse(**s) for s in enriched]
        return ScheduledCommandListResponse(count=len(items), items=items)

    async def get_schedule_by_id(
        self, db: Session, schedule_id: int,
    ) -> ScheduledCommandResponse:
        schedule = ScheduledCommandRepository.get_by_id(db, schedule_id)
        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled command not found",
            )
        enriched = ScheduledCommandRepository.attach_host_names(db, [schedule])
        return ScheduledCommandResponse(**enriched[0])

    async def create_schedule(
        self, db: Session, data: ScheduledCommandCreate,
    ) -> ScheduledCommandResponse:
        host = RemoteHostRepository.get_by_id(db, data.host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        schedule = ScheduledCommandRepository.create(
            db, data.host_id, data.credential_id,
            data.command, data.cron_expression, data.enabled,
        )
        enriched = ScheduledCommandRepository.attach_host_names(db, [schedule])
        return ScheduledCommandResponse(**enriched[0])

    async def update_schedule(
        self, db: Session, schedule_id: int, data: ScheduledCommandUpdate,
    ) -> ScheduledCommandResponse:
        existing = ScheduledCommandRepository.get_by_id(db, schedule_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled command not found",
            )
        update_data = data.model_dump(exclude_unset=True)
        schedule = ScheduledCommandRepository.update(
            db, schedule_id, update_data
        )
        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled command not found",
            )
        enriched = ScheduledCommandRepository.attach_host_names(db, [schedule])
        return ScheduledCommandResponse(**enriched[0])

    async def delete_schedule(
        self, db: Session, schedule_id: int,
    ) -> None:
        deleted = ScheduledCommandRepository.delete(db, schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled command not found",
            )

    async def run_schedule_now(
        self, db: Session, schedule_id: int,
    ) -> RemoteExecuteResponse:
        schedule = ScheduledCommandRepository.get_by_id(db, schedule_id)
        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled command not found",
            )
        request = RemoteExecuteRequest(
            host_id=schedule.host_id,
            command=schedule.command,
            shell="bash",
        )
        result = await self.execute_command(
            db, request, execution_source="scheduled"
        )
        ScheduledCommandRepository.update(
            db, schedule_id, {"last_run": datetime.now(UTC)}
        )
        return result

    # ------------------------------------------------------------------ #
    # File Transfer                                                       #
    # ------------------------------------------------------------------ #

    async def upload_file(
        self, db: Session, request: FileUploadRequest,
    ) -> FileTransferResponse:
        import base64
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
        username, password, ssh_key = await self._resolve_credentials(db, host)
        content = base64.b64decode(request.content_base64)
        provider = get_remote_provider(host.connection_type)
        result = await provider.upload_file(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            remote_path=request.remote_path,
            content=content,
            ip_address=host.ip_address,
        )
        return FileTransferResponse(
            success=result["success"],
            message=result.get("message", ""),
            remote_path=result["remote_path"],
            size_bytes=result.get("size_bytes"),
        )

    async def download_file(
        self, db: Session, request: FileDownloadRequest,
    ) -> FileDownloadResponse:
        import base64
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
        username, password, ssh_key = await self._resolve_credentials(db, host)
        provider = get_remote_provider(host.connection_type)
        result = await provider.download_file(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            remote_path=request.remote_path,
            ip_address=host.ip_address,
        )
        content_b64 = None
        if result.get("content"):
            content_b64 = base64.b64encode(result["content"]).decode("ascii")
        return FileDownloadResponse(
            success=result["success"],
            message=result.get("message", ""),
            remote_path=result["remote_path"],
            content_base64=content_b64,
            size_bytes=result.get("size_bytes"),
        )

    async def list_directory(
        self, db: Session, host_id: int, remote_path: str,
    ) -> FileListResponse:
        host = RemoteHostRepository.get_by_id(db, host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        username, password, ssh_key = await self._resolve_credentials(db, host)
        provider = get_remote_provider(host.connection_type)
        result = await provider.list_directory(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            remote_path=remote_path,
            ip_address=host.ip_address,
        )
        items = [
            FileListItem(**item) for item in result.get("items", [])
        ]
        return FileListResponse(
            path=result.get("path", remote_path),
            items=items,
        )

    async def create_directory(
        self, db: Session, request: FileMkdirRequest,
    ) -> FileTransferResponse:
        host = RemoteHostRepository.get_by_id(db, request.host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        username, password, ssh_key = await self._resolve_credentials(db, host)
        provider = get_remote_provider(host.connection_type)
        result = await provider.create_directory(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            remote_path=request.remote_path,
            ip_address=host.ip_address,
        )
        return FileTransferResponse(
            success=result["success"],
            message=result.get("message", ""),
            remote_path=result["remote_path"],
        )

    async def delete_file(
        self, db: Session, request: FileDeleteRequest,
    ) -> FileTransferResponse:
        host = RemoteHostRepository.get_by_id(db, request.host_id)
        if host is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remote host not found",
            )
        username, password, ssh_key = await self._resolve_credentials(db, host)
        provider = get_remote_provider(host.connection_type)
        result = await provider.delete_file(
            hostname=host.hostname,
            port=host.port,
            username=username or "unknown",
            password=password,
            ssh_key=ssh_key,
            remote_path=request.remote_path,
            ip_address=host.ip_address,
        )
        return FileTransferResponse(
            success=result["success"],
            message=result.get("message", ""),
            remote_path=result["remote_path"],
        )

    # ------------------------------------------------------------------ #
    # Session Metrics                                                     #
    # ------------------------------------------------------------------ #

    async def get_session_metrics(self) -> SessionMetricsResponse:
        metrics = get_session_metrics()
        return SessionMetricsResponse(**metrics)

    # ------------------------------------------------------------------ #
    # Command History                                                     #
    # ------------------------------------------------------------------ #

    async def get_history(
        self, db: Session, search: str | None = None,
        host_id: int | None = None, success: bool | None = None,
        limit: int = 50,
    ) -> RemoteHistoryResponse:
        records = CommandHistoryRepository.get_filtered(
            db, search, host_id, success, limit
        )
        enriched = CommandHistoryRepository.attach_host_names(db, records)
        items = [CommandHistoryItem(**r) for r in enriched]
        return RemoteHistoryResponse(count=len(items), items=items)


remote_service = RemoteService()
