"""
Mission Control Proxmox Router

API endpoints for Proxmox virtualization operations.
Configuration comes from IntegrationProfile — never from config.py.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.proxmox import (
    ProxmoxConnectionTestResponse,
    ProxmoxHealthResponse,
    ProxmoxLxcActionResponse,
    ProxmoxLxcCloneRequest,
    ProxmoxLxcCreateRequest,
    ProxmoxLxcCreateResponse,
    ProxmoxLxcDeleteResponse,
    ProxmoxLxcDetailResponse,
    ProxmoxLxcListResponse,
    ProxmoxLxcTemplateListResponse,
    ProxmoxNetworkListResponse,
    ProxmoxNodeListResponse,
    ProxmoxSnapshotActionResponse,
    ProxmoxSnapshotCreateRequest,
    ProxmoxSnapshotListResponse,
    ProxmoxStorageListResponse,
    ProxmoxSummaryResponse,
    ProxmoxTaskListResponse,
    ProxmoxVmActionResponse,
    ProxmoxVmDetailResponse,
    ProxmoxVmListResponse,
)
from app.services.proxmox_service import proxmox_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/proxmox",
    tags=["proxmox"],
    dependencies=[Depends(get_current_user)],
)


# ------------------------------------------------------------------ #
# Overview & Connection                                               #
# ------------------------------------------------------------------ #


@router.get("/overview", response_model=ProxmoxSummaryResponse)
async def get_proxmox_overview(
    db: Session = Depends(get_db),
) -> ProxmoxSummaryResponse:
    """Get Proxmox cluster overview."""
    data = await proxmox_service.get_summary(db)
    return ProxmoxSummaryResponse(**data)


@router.get("/test", response_model=ProxmoxConnectionTestResponse)
async def test_proxmox_connection(
    db: Session = Depends(get_db),
) -> ProxmoxConnectionTestResponse:
    """Test connectivity to Proxmox cluster."""
    data = await proxmox_service.test_connection(db)
    return ProxmoxConnectionTestResponse(**data)


@router.get("/health", response_model=ProxmoxHealthResponse)
async def get_proxmox_health(
    db: Session = Depends(get_db),
) -> ProxmoxHealthResponse:
    """Get Proxmox cluster health status."""
    data = await proxmox_service.get_health(db)
    return ProxmoxHealthResponse(**data)


# ------------------------------------------------------------------ #
# Nodes                                                               #
# ------------------------------------------------------------------ #


@router.get("/nodes", response_model=ProxmoxNodeListResponse)
async def list_nodes(
    db: Session = Depends(get_db),
) -> ProxmoxNodeListResponse:
    """List cluster nodes."""
    data = await proxmox_service.get_nodes(db)
    return ProxmoxNodeListResponse(**data)


# ------------------------------------------------------------------ #
# Virtual Machines                                                    #
# ------------------------------------------------------------------ #


@router.get("/vms", response_model=ProxmoxVmListResponse)
async def list_vms(
    db: Session = Depends(get_db),
) -> ProxmoxVmListResponse:
    """List all QEMU virtual machines."""
    data = await proxmox_service.get_vms(db)
    return ProxmoxVmListResponse(**data)


@router.get("/vms/{vm_id}", response_model=ProxmoxVmDetailResponse)
async def get_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxVmDetailResponse:
    """Get detailed information for a single VM."""
    data = await proxmox_service.get_vm_detail(vm_id, db)
    return ProxmoxVmDetailResponse(**data)


@router.post("/vms/{vm_id}/start", response_model=ProxmoxVmActionResponse)
async def start_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxVmActionResponse:
    """Start a virtual machine."""
    data = await proxmox_service.start_vm(vm_id, db)
    return ProxmoxVmActionResponse(**data)


@router.post("/vms/{vm_id}/stop", response_model=ProxmoxVmActionResponse)
async def stop_vm(
    vm_id: str,
    force: bool = Query(False),
    db: Session = Depends(get_db),
) -> ProxmoxVmActionResponse:
    """Stop a virtual machine (ACPI or force)."""
    data = await proxmox_service.stop_vm(vm_id, force, db)
    return ProxmoxVmActionResponse(**data)


@router.post("/vms/{vm_id}/restart", response_model=ProxmoxVmActionResponse)
async def restart_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxVmActionResponse:
    """Reboot a virtual machine."""
    data = await proxmox_service.restart_vm(vm_id, db)
    return ProxmoxVmActionResponse(**data)


@router.post("/vms/{vm_id}/pause", response_model=ProxmoxVmActionResponse)
async def pause_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxVmActionResponse:
    """Suspend a virtual machine."""
    data = await proxmox_service.pause_vm(vm_id, db)
    return ProxmoxVmActionResponse(**data)


@router.post("/vms/{vm_id}/resume", response_model=ProxmoxVmActionResponse)
async def resume_vm(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxVmActionResponse:
    """Resume a suspended virtual machine."""
    data = await proxmox_service.resume_vm(vm_id, db)
    return ProxmoxVmActionResponse(**data)


# ------------------------------------------------------------------ #
# LXC Containers                                                      #
# ------------------------------------------------------------------ #


@router.get("/lxc", response_model=ProxmoxLxcListResponse)
async def list_lxc(
    db: Session = Depends(get_db),
) -> ProxmoxLxcListResponse:
    """List all LXC containers."""
    data = await proxmox_service.get_lxc_containers(db)
    return ProxmoxLxcListResponse(**data)


@router.get("/lxc/templates", response_model=ProxmoxLxcTemplateListResponse)
async def list_lxc_templates(
    node: str | None = Query(None),
    db: Session = Depends(get_db),
) -> ProxmoxLxcTemplateListResponse:
    """List available LXC templates on storage."""
    data = await proxmox_service.get_lxc_templates(node, db)
    return ProxmoxLxcTemplateListResponse(**data)


@router.post("/lxc", response_model=ProxmoxLxcCreateResponse)
async def create_lxc(
    payload: ProxmoxLxcCreateRequest,
    db: Session = Depends(get_db),
) -> ProxmoxLxcCreateResponse:
    """Create a new LXC container from a template."""
    config = payload.model_dump(exclude_none=True)
    data = await proxmox_service.create_lxc(config, db)
    return ProxmoxLxcCreateResponse(**data)


@router.get("/lxc/{vm_id}", response_model=ProxmoxLxcDetailResponse)
async def get_lxc(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxLxcDetailResponse:
    """Get detailed information for a single LXC container."""
    data = await proxmox_service.get_lxc_detail(vm_id, db)
    return ProxmoxLxcDetailResponse(**data)


@router.post("/lxc/{vm_id}/start", response_model=ProxmoxLxcActionResponse)
async def start_lxc(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxLxcActionResponse:
    """Start an LXC container."""
    data = await proxmox_service.start_lxc(vm_id, db)
    return ProxmoxLxcActionResponse(**data)


@router.post("/lxc/{vm_id}/stop", response_model=ProxmoxLxcActionResponse)
async def stop_lxc(
    vm_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxLxcActionResponse:
    """Stop an LXC container."""
    data = await proxmox_service.stop_lxc(vm_id, db)
    return ProxmoxLxcActionResponse(**data)


@router.post("/lxc/{vm_id}/clone", response_model=ProxmoxLxcCreateResponse)
async def clone_lxc(
    vm_id: str,
    payload: ProxmoxLxcCloneRequest | None = None,
    db: Session = Depends(get_db),
) -> ProxmoxLxcCreateResponse:
    """Clone an existing LXC container."""
    new_vmid = payload.new_vmid if payload else None
    hostname = payload.hostname if payload else None
    data = await proxmox_service.clone_lxc(vm_id, new_vmid, hostname, db)
    return ProxmoxLxcCreateResponse(**data)


@router.delete("/lxc/{vm_id}", response_model=ProxmoxLxcDeleteResponse)
async def delete_lxc(
    vm_id: str,
    purge: bool = Query(False),
    db: Session = Depends(get_db),
) -> ProxmoxLxcDeleteResponse:
    """Delete an LXC container (must be stopped)."""
    data = await proxmox_service.delete_lxc(vm_id, purge, db)
    return ProxmoxLxcDeleteResponse(**data)


# ------------------------------------------------------------------ #
# Networks                                                            #
# ------------------------------------------------------------------ #


@router.get("/networks", response_model=ProxmoxNetworkListResponse)
async def list_networks(
    db: Session = Depends(get_db),
) -> ProxmoxNetworkListResponse:
    """List virtual networks."""
    data = await proxmox_service.get_networks(db)
    return ProxmoxNetworkListResponse(**data)


# ------------------------------------------------------------------ #
# Storage                                                             #
# ------------------------------------------------------------------ #


@router.get("/storage", response_model=ProxmoxStorageListResponse)
async def list_storage(
    db: Session = Depends(get_db),
) -> ProxmoxStorageListResponse:
    """List storage pools."""
    data = await proxmox_service.get_storage(db)
    return ProxmoxStorageListResponse(**data)


# ------------------------------------------------------------------ #
# Tasks                                                               #
# ------------------------------------------------------------------ #


@router.get("/tasks", response_model=ProxmoxTaskListResponse)
async def list_tasks(
    node: str | None = Query(None),
    db: Session = Depends(get_db),
) -> ProxmoxTaskListResponse:
    """List recent tasks, optionally filtered by node."""
    data = await proxmox_service.get_tasks(node, db)
    return ProxmoxTaskListResponse(**data)


# ------------------------------------------------------------------ #
# Snapshots                                                           #
# ------------------------------------------------------------------ #


@router.get("/snapshots", response_model=ProxmoxSnapshotListResponse)
async def list_snapshots(
    vm_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> ProxmoxSnapshotListResponse:
    """List snapshots, optionally filtered by VM."""
    data = await proxmox_service.get_snapshots(vm_id, db)
    return ProxmoxSnapshotListResponse(**data)


@router.post("/snapshots", response_model=ProxmoxSnapshotActionResponse)
async def create_snapshot(
    payload: ProxmoxSnapshotCreateRequest,
    db: Session = Depends(get_db),
) -> ProxmoxSnapshotActionResponse:
    """Create a snapshot for a VM."""
    data = await proxmox_service.create_snapshot(payload.vm_id, payload.name, db)
    return ProxmoxSnapshotActionResponse(**data)


@router.delete(
    "/vms/{vm_id}/snapshots/{snapshot_id}",
    response_model=ProxmoxSnapshotActionResponse,
)
async def delete_snapshot(
    vm_id: str,
    snapshot_id: str,
    db: Session = Depends(get_db),
) -> ProxmoxSnapshotActionResponse:
    """Delete a snapshot."""
    data = await proxmox_service.delete_snapshot(vm_id, snapshot_id, db)
    return ProxmoxSnapshotActionResponse(**data)
