"""
Mission Control Remote Operations Router

Sprint 2.1.8 - Remote Operations Finalization.
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.bulk_command import (
    BulkExecuteRequest,
    BulkExecuteResponse,
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
    FileTransferResponse,
    FileUploadRequest,
)
from app.schemas.remote_command import (
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
from app.services.remote_service import RemoteService, remote_service

router = APIRouter(
    prefix="/remote",
    tags=["Remote Operations"],
    dependencies=[Depends(get_current_user)],
)


def get_remote_service() -> RemoteService:
    return remote_service


# ------------------------------------------------------------------ #
# Host Endpoints                                                      #
# ------------------------------------------------------------------ #

@router.get("/hosts", response_model=RemoteHostListResponse)
async def list_hosts(
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostListResponse:
    return await service.get_hosts(db, search)


@router.get("/hosts/{host_id}", response_model=RemoteHostResponse)
async def get_host(
    host_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostResponse:
    return await service.get_host_by_id(db, host_id)


@router.post(
    "/hosts",
    status_code=status.HTTP_201_CREATED,
    response_model=RemoteHostResponse,
)
async def create_host(
    payload: RemoteHostCreate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostResponse:
    return await service.create_host(db, payload)


@router.put("/hosts/{host_id}", response_model=RemoteHostResponse)
async def update_host(
    host_id: int,
    payload: RemoteHostUpdate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostResponse:
    return await service.update_host(db, host_id, payload)


@router.delete(
    "/hosts/{host_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_host(
    host_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> None:
    await service.delete_host(db, host_id)


# ------------------------------------------------------------------ #
# Credential Profile Endpoints                                        #
# ------------------------------------------------------------------ #

@router.get("/credentials", response_model=CredentialProfileListResponse)
async def list_credentials(
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileListResponse:
    return await service.get_credentials(db)


@router.get("/credentials/{profile_id}", response_model=CredentialProfileResponse)
async def get_credential(
    profile_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileResponse:
    return await service.get_credential_by_id(db, profile_id)


@router.post(
    "/credentials",
    status_code=status.HTTP_201_CREATED,
    response_model=CredentialProfileResponse,
)
async def create_credential(
    payload: CredentialProfileCreate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileResponse:
    return await service.create_credential(db, payload)


@router.put("/credentials/{profile_id}", response_model=CredentialProfileResponse)
async def update_credential(
    profile_id: int,
    payload: CredentialProfileUpdate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileResponse:
    return await service.update_credential(db, profile_id, payload)


@router.delete(
    "/credentials/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_credential(
    profile_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> None:
    await service.delete_credential(db, profile_id)


# ------------------------------------------------------------------ #
# Command Execution                                                   #
# ------------------------------------------------------------------ #

@router.post("/test", response_model=RemoteTestConnectionResponse)
async def test_connection(
    payload: RemoteTestConnectionRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteTestConnectionResponse:
    return await service.test_connection(db, payload)


@router.post("/execute", response_model=RemoteExecuteResponse)
async def execute_command(
    payload: RemoteExecuteRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteExecuteResponse:
    return await service.execute_command(db, payload)


@router.post("/execute/stream")
async def execute_command_stream(
    payload: RemoteExecuteRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> StreamingResponse:
    async def event_generator():
        import json
        import logging

        logger = logging.getLogger("missioncontrol")
        try:
            async for chunk in service.execute_command_stream(db, payload):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception:
            logger.info("Stream client disconnected, command may still be running on remote host")
            yield f'data: {json.dumps({"type": "error", "message": "Connection lost"})}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/bulk-execute", response_model=BulkExecuteResponse)
async def bulk_execute(
    payload: BulkExecuteRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> BulkExecuteResponse:
    return await service.bulk_execute(db, payload)


@router.get("/history", response_model=RemoteHistoryResponse)
async def get_history(
    search: str | None = Query(None),
    host_id: int | None = Query(None),
    success: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHistoryResponse:
    return await service.get_history(db, search, host_id, success, limit)


# ------------------------------------------------------------------ #
# Command Templates                                                   #
# ------------------------------------------------------------------ #

@router.get("/templates", response_model=CommandTemplateListResponse)
async def list_templates(
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CommandTemplateListResponse:
    return await service.get_templates(db)


@router.get("/templates/{template_id}", response_model=CommandTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CommandTemplateResponse:
    return await service.get_template_by_id(db, template_id)


@router.post(
    "/templates",
    status_code=status.HTTP_201_CREATED,
    response_model=CommandTemplateResponse,
)
async def create_template(
    payload: CommandTemplateCreate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CommandTemplateResponse:
    return await service.create_template(db, payload)


@router.put("/templates/{template_id}", response_model=CommandTemplateResponse)
async def update_template(
    template_id: int,
    payload: CommandTemplateUpdate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CommandTemplateResponse:
    return await service.update_template(db, template_id, payload)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> None:
    await service.delete_template(db, template_id)


@router.post("/templates/{template_id}/execute", response_model=RemoteExecuteResponse)
async def execute_template(
    template_id: int,
    host_id: int = Query(..., description="Host ID to execute against"),
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteExecuteResponse:
    return await service.execute_template(db, template_id, host_id)


# ------------------------------------------------------------------ #
# Scheduled Commands                                                  #
# ------------------------------------------------------------------ #

@router.get("/schedules", response_model=ScheduledCommandListResponse)
async def list_schedules(
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> ScheduledCommandListResponse:
    return await service.get_schedules(db)


@router.get("/schedules/{schedule_id}", response_model=ScheduledCommandResponse)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> ScheduledCommandResponse:
    return await service.get_schedule_by_id(db, schedule_id)


@router.post(
    "/schedules",
    status_code=status.HTTP_201_CREATED,
    response_model=ScheduledCommandResponse,
)
async def create_schedule(
    payload: ScheduledCommandCreate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> ScheduledCommandResponse:
    return await service.create_schedule(db, payload)


@router.put("/schedules/{schedule_id}", response_model=ScheduledCommandResponse)
async def update_schedule(
    schedule_id: int,
    payload: ScheduledCommandUpdate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> ScheduledCommandResponse:
    return await service.update_schedule(db, schedule_id, payload)


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> None:
    await service.delete_schedule(db, schedule_id)


@router.post("/schedules/{schedule_id}/run-now", response_model=RemoteExecuteResponse)
async def run_schedule_now(
    schedule_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteExecuteResponse:
    return await service.run_schedule_now(db, schedule_id)


# ------------------------------------------------------------------ #
# File Transfer                                                       #
# ------------------------------------------------------------------ #

@router.post("/files/upload", response_model=FileTransferResponse)
async def upload_file(
    payload: FileUploadRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> FileTransferResponse:
    return await service.upload_file(db, payload)


@router.post("/files/download", response_model=FileDownloadResponse)
async def download_file(
    payload: FileDownloadRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> FileDownloadResponse:
    return await service.download_file(db, payload)


@router.get("/files/list", response_model=FileListResponse)
async def list_directory(
    host_id: int = Query(...),
    path: str = Query("/", description="Remote directory path"),
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> FileListResponse:
    return await service.list_directory(db, host_id, path)


@router.post("/files/mkdir", response_model=FileTransferResponse)
async def create_directory(
    payload: FileMkdirRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> FileTransferResponse:
    return await service.create_directory(db, payload)


@router.post("/files/delete", response_model=FileTransferResponse)
async def delete_file(
    payload: FileDeleteRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> FileTransferResponse:
    return await service.delete_file(db, payload)


# ------------------------------------------------------------------ #
# Session Metrics                                                     #
# ------------------------------------------------------------------ #

@router.get("/metrics", response_model=SessionMetricsResponse)
async def get_metrics(
    service: RemoteService = Depends(get_remote_service),
) -> SessionMetricsResponse:
    return await service.get_session_metrics()


# ------------------------------------------------------------------ #
# Interactive Console (WebSocket)                                     #
# ------------------------------------------------------------------ #

import asyncio  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402

from fastapi import WebSocket, WebSocketDisconnect  # noqa: E402

from app.providers.remote.ssh_provider import SSHProvider  # noqa: E402
from app.repositories.credential_profile_repository import (  # noqa: E402
    CredentialProfileRepository,
)
from app.repositories.remote_host_repository import RemoteHostRepository  # noqa: E402
from app.services.remote_service import _decrypt_credential  # noqa: E402

logger = logging.getLogger(__name__)


@router.websocket("/console")
async def console_ws(
    websocket: WebSocket,
    host_id: int = Query(...),
    db: Session = Depends(get_db),
):
    await websocket.accept()

    host = RemoteHostRepository.get_by_id(db, host_id)
    if host is None or not host.enabled:
        await websocket.send_json({"type": "error", "message": "Host not found or disabled"})
        await websocket.close()
        return

    username, password, ssh_key = None, None, None
    if host.credential_profile_id is not None:
        profile = CredentialProfileRepository.get_by_id(db, host.credential_profile_id)
        if profile is not None:
            username = profile.username
            password = _decrypt_credential(profile.password_encrypted)
            ssh_key = _decrypt_credential(profile.private_key_encrypted)

    ssh = SSHProvider()
    client = None
    chan = None

    try:
        target = host.ip_address if host.ip_address else host.hostname
        client = ssh._build_client(target, host.port, username or "", password, ssh_key)
        chan = client.invoke_shell(term="xterm-256color", width=120, height=40)
        chan.settimeout(0.0)

        await websocket.send_json({"type": "connected", "host": host.name})

        asyncio.get_event_loop()

        async def read_ssh():
            while True:
                if chan.closed:
                    break
                if chan.recv_ready():
                    data = chan.recv(4096).decode("utf-8", errors="replace")
                    await websocket.send_json({"type": "output", "data": data})
                elif chan.exit_status_ready():
                    while chan.recv_ready():
                        data = chan.recv(4096).decode("utf-8", errors="replace")
                        await websocket.send_json({"type": "output", "data": data})
                    await websocket.send_json({"type": "exit", "exit_code": chan.recv_exit_status()})
                    break
                else:
                    try:
                        # Drain any pending bytes; non-blocking recv raises on
                        # no data, which is expected and must be ignored.
                        if chan.recv_ready():
                            data = chan.recv(4096).decode("utf-8", errors="replace")
                            await websocket.send_json({"type": "output", "data": data})
                    except (OSError, paramiko.SSHException):
                        pass
                    await asyncio.sleep(0.05)

        async def read_ws():
            while True:
                msg = await websocket.receive_text()
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    data = {"type": "input", "data": msg}

                if data.get("type") == "input":
                    chan.send(data["data"])
                elif data.get("type") == "resize":
                    chan.resize_height(data.get("height", 40))
                    chan.resize_width(data.get("width", 120))

        read_task = asyncio.create_task(read_ssh())
        write_task = asyncio.create_task(read_ws())

        done, pending = await asyncio.wait(
            [read_task, write_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("WebSocket console error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if chan is not None:
            try:
                chan.close()
            except Exception:
                pass
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
