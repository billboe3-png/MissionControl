"""
Mission Control Remote Operations Router

Sprint 2.1.0 - Remote Operations Framework.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.credential_profile import CredentialProfileCreate
from app.schemas.credential_profile import CredentialProfileListResponse
from app.schemas.credential_profile import CredentialProfileResponse
from app.schemas.credential_profile import CredentialProfileUpdate
from app.schemas.remote_command import RemoteExecuteRequest
from app.schemas.remote_command import RemoteExecuteResponse
from app.schemas.remote_command import RemoteHistoryResponse
from app.schemas.remote_command import RemoteTestConnectionRequest
from app.schemas.remote_command import RemoteTestConnectionResponse
from app.schemas.remote_host import RemoteHostCreate
from app.schemas.remote_host import RemoteHostListResponse
from app.schemas.remote_host import RemoteHostResponse
from app.schemas.remote_host import RemoteHostUpdate
from app.services.remote_service import RemoteService
from app.services.remote_service import remote_service

router = APIRouter(
    prefix="/remote",
    tags=["Remote Operations"],
)


def get_remote_service() -> RemoteService:
    """Provide the shared remote service instance."""
    return remote_service


# ------------------------------------------------------------------ #
# Host Endpoints                                                      #
# ------------------------------------------------------------------ #


@router.get(
    "/hosts",
    summary="List remote hosts",
    description="Return all remote hosts with optional search.",
    response_model=RemoteHostListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Remote hosts retrieved successfully.",
            "model": RemoteHostListResponse,
        },
    },
)
async def list_hosts(
    search: str | None = Query(None, description="Search by name, hostname, or IP."),
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostListResponse:
    return await service.get_hosts(db, search)


@router.get(
    "/hosts/{host_id}",
    summary="Get remote host",
    description="Return a single remote host by its identifier.",
    response_model=RemoteHostResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Remote host retrieved successfully.",
            "model": RemoteHostResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Remote host not found.",
        },
    },
)
async def get_host(
    host_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostResponse:
    return await service.get_host_by_id(db, host_id)


@router.post(
    "/hosts",
    summary="Create remote host",
    description="Create a new remote host record.",
    response_model=RemoteHostResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Remote host created successfully.",
            "model": RemoteHostResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid connection type.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Credential profile not found.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def create_host(
    payload: RemoteHostCreate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostResponse:
    return await service.create_host(db, payload)


@router.put(
    "/hosts/{host_id}",
    summary="Update remote host",
    description="Update fields on an existing remote host.",
    response_model=RemoteHostResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Remote host updated successfully.",
            "model": RemoteHostResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid connection type.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Remote host not found.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def update_host(
    host_id: int,
    payload: RemoteHostUpdate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHostResponse:
    return await service.update_host(db, host_id, payload)


@router.delete(
    "/hosts/{host_id}",
    summary="Delete remote host",
    description="Remove a remote host by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Remote host deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Remote host not found.",
        },
    },
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


@router.get(
    "/credentials",
    summary="List credential profiles",
    description="Return all credential profiles.",
    response_model=CredentialProfileListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Credential profiles retrieved successfully.",
            "model": CredentialProfileListResponse,
        },
    },
)
async def list_credentials(
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileListResponse:
    return await service.get_credentials(db)


@router.get(
    "/credentials/{profile_id}",
    summary="Get credential profile",
    description="Return a single credential profile by its identifier.",
    response_model=CredentialProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Credential profile retrieved successfully.",
            "model": CredentialProfileResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Credential profile not found.",
        },
    },
)
async def get_credential(
    profile_id: int,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileResponse:
    return await service.get_credential_by_id(db, profile_id)


@router.post(
    "/credentials",
    summary="Create credential profile",
    description="Create a new credential profile record.",
    response_model=CredentialProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Credential profile created successfully.",
            "model": CredentialProfileResponse,
        },
        status.HTTP_409_CONFLICT: {
            "description": "Credential profile name already exists.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def create_credential(
    payload: CredentialProfileCreate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileResponse:
    return await service.create_credential(db, payload)


@router.put(
    "/credentials/{profile_id}",
    summary="Update credential profile",
    description="Update fields on an existing credential profile.",
    response_model=CredentialProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Credential profile updated successfully.",
            "model": CredentialProfileResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Credential profile not found.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Credential profile name already exists.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def update_credential(
    profile_id: int,
    payload: CredentialProfileUpdate,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> CredentialProfileResponse:
    return await service.update_credential(db, profile_id, payload)


@router.delete(
    "/credentials/{profile_id}",
    summary="Delete credential profile",
    description="Remove a credential profile by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Credential profile deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Credential profile not found.",
        },
    },
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


@router.post(
    "/test",
    summary="Test connection",
    description="Test connectivity to a remote host.",
    response_model=RemoteTestConnectionResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Connection test completed.",
            "model": RemoteTestConnectionResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Remote host is disabled.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Remote host not found.",
        },
    },
)
async def test_connection(
    payload: RemoteTestConnectionRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteTestConnectionResponse:
    return await service.test_connection(db, payload)


@router.post(
    "/execute",
    summary="Execute command",
    description="Execute a command on a remote host.",
    response_model=RemoteExecuteResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Command execution completed.",
            "model": RemoteExecuteResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid shell or host disabled.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Remote host not found.",
        },
    },
)
async def execute_command(
    payload: RemoteExecuteRequest,
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteExecuteResponse:
    return await service.execute_command(db, payload)


@router.get(
    "/history",
    summary="Get command history",
    description="Return command execution history with optional filters.",
    response_model=RemoteHistoryResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Command history retrieved successfully.",
            "model": RemoteHistoryResponse,
        },
    },
)
async def get_history(
    search: str | None = Query(None, description="Filter by command text."),
    host_id: int | None = Query(None, description="Filter by host ID."),
    success: bool | None = Query(None, description="Filter by success status."),
    limit: int = Query(50, ge=1, le=500, description="Max records to return."),
    db: Session = Depends(get_db),
    service: RemoteService = Depends(get_remote_service),
) -> RemoteHistoryResponse:
    return await service.get_history(db, search, host_id, success, limit)
