"""
Mission Control Hyper-V Router

API endpoints for Hyper-V virtualization operations.
Configuration comes from IntegrationProfile — never from config.py.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.hyperv import (
    HyperVCheckpointActionResponse,
    HyperVCheckpointCreateRequest,
    HyperVCheckpointListResponse,
    HyperVConnectionTestResponse,
    HyperVHealthResponse,
    HyperVNetworkListResponse,
    HyperVStorageListResponse,
    HyperVSummaryResponse,
    HyperVVmActionResponse,
    HyperVVmDetailResponse,
    HyperVVmListResponse,
)
from app.services.hyperv_service import hyperv_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hyperv", tags=["hyperv"])


# ------------------------------------------------------------------ #
# Overview & Connection                                               #
# ------------------------------------------------------------------ #


@router.get("/overview", response_model=HyperVSummaryResponse)
async def get_hyperv_overview(
    db: Session = Depends(get_db),
) -> HyperVSummaryResponse:
    """Get Hyper-V virtualization overview."""
    data = await hyperv_service.get_summary(db)
    return HyperVSummaryResponse(**data)


@router.get("/test", response_model=HyperVConnectionTestResponse)
async def test_hyperv_connection(
    db: Session = Depends(get_db),
) -> HyperVConnectionTestResponse:
    """Test connectivity to Hyper-V host."""
    data = await hyperv_service.test_connection(db)
    return HyperVConnectionTestResponse(**data)


@router.get("/health", response_model=HyperVHealthResponse)
async def get_hyperv_health(
    db: Session = Depends(get_db),
) -> HyperVHealthResponse:
    """Get Hyper-V host health status."""
    data = await hyperv_service.get_health(db)
    return HyperVHealthResponse(**data)


# ------------------------------------------------------------------ #
# Virtual Machines                                                    #
# ------------------------------------------------------------------ #


@router.get("/vms", response_model=HyperVVmListResponse)
async def list_vms(
    db: Session = Depends(get_db),
) -> HyperVVmListResponse:
    """List all virtual machines."""
    data = await hyperv_service.get_vms(db)
    return HyperVVmListResponse(**data)


@router.get("/vms/{vm_id}", response_model=HyperVVmDetailResponse)
async def get_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> HyperVVmDetailResponse:
    """Get detailed information for a single VM."""
    data = await hyperv_service.get_vm_detail(vm_id, db)
    return HyperVVmDetailResponse(**data)


@router.post("/vms/{vm_id}/start", response_model=HyperVVmActionResponse)
async def start_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Start a virtual machine."""
    data = await hyperv_service.start_vm(vm_id, db)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/stop", response_model=HyperVVmActionResponse)
async def stop_vm(
    vm_id: str,
    force: bool = Query(False),
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Stop a virtual machine."""
    data = await hyperv_service.stop_vm(vm_id, force, db)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/restart", response_model=HyperVVmActionResponse)
async def restart_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Restart a virtual machine."""
    data = await hyperv_service.restart_vm(vm_id, db)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/pause", response_model=HyperVVmActionResponse)
async def pause_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Pause a virtual machine."""
    data = await hyperv_service.pause_vm(vm_id, db)
    return HyperVVmActionResponse(**data)


@router.post("/vms/{vm_id}/resume", response_model=HyperVVmActionResponse)
async def resume_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> HyperVVmActionResponse:
    """Resume a paused virtual machine."""
    data = await hyperv_service.resume_vm(vm_id, db)
    return HyperVVmActionResponse(**data)


# ------------------------------------------------------------------ #
# Networks                                                            #
# ------------------------------------------------------------------ #


@router.get("/networks", response_model=HyperVNetworkListResponse)
async def list_networks(
    db: Session = Depends(get_db),
) -> HyperVNetworkListResponse:
    """List virtual switches."""
    data = await hyperv_service.get_networks(db)
    return HyperVNetworkListResponse(**data)


# ------------------------------------------------------------------ #
# Storage                                                             #
# ------------------------------------------------------------------ #


@router.get("/storage", response_model=HyperVStorageListResponse)
async def list_storage(
    db: Session = Depends(get_db),
) -> HyperVStorageListResponse:
    """List virtual hard disks."""
    data = await hyperv_service.get_storage(db)
    return HyperVStorageListResponse(**data)


# ------------------------------------------------------------------ #
# Checkpoints                                                         #
# ------------------------------------------------------------------ #


@router.get("/checkpoints", response_model=HyperVCheckpointListResponse)
async def list_checkpoints(
    vm_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HyperVCheckpointListResponse:
    """List checkpoints, optionally filtered by VM."""
    data = await hyperv_service.get_checkpoints(vm_id, db)
    return HyperVCheckpointListResponse(**data)


@router.post("/checkpoints", response_model=HyperVCheckpointActionResponse)
async def create_checkpoint(
    payload: HyperVCheckpointCreateRequest,
    db: Session = Depends(get_db),
) -> HyperVCheckpointActionResponse:
    """Create a checkpoint for a VM."""
    data = await hyperv_service.create_checkpoint(payload.vm_id, payload.name, db)
    return HyperVCheckpointActionResponse(**data)


@router.delete(
    "/vms/{vm_id}/checkpoints/{checkpoint_id}",
    response_model=HyperVCheckpointActionResponse,
)
async def delete_checkpoint(
    vm_id: str,
    checkpoint_id: str,
    db: Session = Depends(get_db),
) -> HyperVCheckpointActionResponse:
    """Delete a checkpoint."""
    data = await hyperv_service.delete_checkpoint(vm_id, checkpoint_id, db)
    return HyperVCheckpointActionResponse(**data)
