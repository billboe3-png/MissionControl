"""
Mission Control Hyper-V Router

API endpoints for Hyper-V virtualization operations.
Configuration comes from IntegrationProfile — never from config.py.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.hyperv import (
    HyperVCheckpointActionResponse,
    HyperVCheckpointCreateRequest,
    HyperVCheckpointListResponse,
    HyperVConnectionTestResponse,
    HyperVHealthResponse,
    HyperVHostListResponse,
    HyperVNetworkListResponse,
    HyperVReplicationResponse,
    HyperVStorageListResponse,
    HyperVSummaryResponse,
    HyperVVmActionResponse,
    HyperVVmDetailResponse,
    HyperVVmListResponse,
)
from app.services.hyperv_service import hyperv_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hyperv",
    tags=["hyperv"],
    dependencies=[Depends(get_current_user)],
)


# ------------------------------------------------------------------ #
# Hosts                                                               #
# ------------------------------------------------------------------ #


@router.get("/hosts", response_model=HyperVHostListResponse)
async def list_hyperv_hosts(
    db: Session = Depends(get_db),
) -> HyperVHostListResponse:
    """List all enabled Hyper-V hosts."""
    from app.providers.hyperv.provider_factory import list_hyperv_hosts

    hosts = list_hyperv_hosts(db)
    return HyperVHostListResponse(hosts=hosts)


# ------------------------------------------------------------------ #
# Overview & Connection                                               #
# ------------------------------------------------------------------ #


@router.get("/overview", response_model=HyperVSummaryResponse)
async def get_hyperv_overview(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVSummaryResponse:
    """Get Hyper-V virtualization overview."""
    data = await hyperv_service.get_summary(db, host_id)
    return HyperVSummaryResponse(**data)


@router.get("/test", response_model=HyperVConnectionTestResponse)
async def test_hyperv_connection(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVConnectionTestResponse:
    """Test connectivity to Hyper-V host."""
    data = await hyperv_service.test_connection(db, host_id)
    return HyperVConnectionTestResponse(**data)


@router.get("/health", response_model=HyperVHealthResponse)
async def get_hyperv_health(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVHealthResponse:
    """Get Hyper-V host health status."""
    data = await hyperv_service.get_health(db, host_id)
    return HyperVHealthResponse(**data)


@router.get("/replication", response_model=HyperVReplicationResponse)
async def get_hyperv_replication(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVReplicationResponse:
    """Get Hyper-V VM replication status."""
    data = await hyperv_service.get_replication(db, host_id)
    return HyperVReplicationResponse(**data)


# ------------------------------------------------------------------ #
# Virtual Machines                                                    #
# ------------------------------------------------------------------ #


@router.get("/vms", response_model=HyperVVmListResponse)
async def list_vms(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmListResponse:
    """List all virtual machines."""
    data = await hyperv_service.get_vms(db, host_id)
    return HyperVVmListResponse(**data)


@router.get("/vms/{vm_id}", response_model=HyperVVmDetailResponse)
async def get_vm(
    vm_id: str,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmDetailResponse:
    """Get detailed information for a single VM."""
    data = await hyperv_service.get_vm_detail(vm_id, db, host_id)
    return HyperVVmDetailResponse(**data)


@router.post("/vms/{vm_id}/start", response_model=HyperVVmActionResponse)
async def start_vm(
    vm_id: str,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Start a virtual machine."""
    data = await hyperv_service.start_vm(vm_id, db, host_id)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/stop", response_model=HyperVVmActionResponse)
async def stop_vm(
    vm_id: str,
    force: bool = Query(False),
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Stop a virtual machine."""
    data = await hyperv_service.stop_vm(vm_id, force, db, host_id)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/restart", response_model=HyperVVmActionResponse)
async def restart_vm(
    vm_id: str,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Restart a virtual machine."""
    data = await hyperv_service.restart_vm(vm_id, db, host_id)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/pause", response_model=HyperVVmActionResponse)
async def pause_vm(
    vm_id: str,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Pause a virtual machine."""
    data = await hyperv_service.pause_vm(vm_id, db, host_id)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/resume", response_model=HyperVVmActionResponse)
async def resume_vm(
    vm_id: str,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Resume a paused virtual machine."""
    data = await hyperv_service.resume_vm(vm_id, db, host_id)
    return HyperVVmActionResponse(**data)


# ------------------------------------------------------------------ #
# Networks                                                            #
# ------------------------------------------------------------------ #


@router.get("/networks", response_model=HyperVNetworkListResponse)
async def list_networks(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVNetworkListResponse:
    """List virtual switches."""
    data = await hyperv_service.get_networks(db, host_id)
    return HyperVNetworkListResponse(**data)


# ------------------------------------------------------------------ #
# Storage                                                             #
# ------------------------------------------------------------------ #


@router.get("/storage", response_model=HyperVStorageListResponse)
async def list_storage(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVStorageListResponse:
    """List virtual hard disks."""
    data = await hyperv_service.get_storage(db, host_id)
    return HyperVStorageListResponse(**data)


# ------------------------------------------------------------------ #
# Checkpoints                                                         #
# ------------------------------------------------------------------ #


@router.get("/checkpoints", response_model=HyperVCheckpointListResponse)
async def list_checkpoints(
    vm_id: str | None = Query(None),
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVCheckpointListResponse:
    """List checkpoints, optionally filtered by VM."""
    data = await hyperv_service.get_checkpoints(vm_id, db, host_id)
    return HyperVCheckpointListResponse(**data)


@router.post("/checkpoints", response_model=HyperVCheckpointActionResponse)
async def create_checkpoint(
    payload: HyperVCheckpointCreateRequest,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVCheckpointActionResponse:
    """Create a checkpoint for a VM."""
    data = await hyperv_service.create_checkpoint(payload.vm_id, payload.name, db, host_id)
    return HyperVCheckpointActionResponse(**data)


@router.delete(
    "/vms/{vm_id}/checkpoints/{checkpoint_id}",
    response_model=HyperVCheckpointActionResponse,
)
async def delete_checkpoint(
    vm_id: str,
    checkpoint_id: str,
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVCheckpointActionResponse:
    """Delete a checkpoint."""
    data = await hyperv_service.delete_checkpoint(vm_id, checkpoint_id, db, host_id)
    return HyperVCheckpointActionResponse(**data)
