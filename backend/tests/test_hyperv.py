"""
Mission Control Hyper-V Tests

Tests the Hyper-V provider, service, router, schemas, mock provider,
VirtualizationProvider abstraction, and domain models.
"""


import pytest

from app.providers.hyperv.mock_provider import MockHyperVProvider, set_mock_mode
from app.providers.hyperv.provider_factory import (
    get_hyperv_provider,
    reset_hyperv_provider,
)

# ------------------------------------------------------------------ #
# Mock Provider Tests                                                 #
# ------------------------------------------------------------------ #


class TestMockHyperVProvider:
    """Tests for the mock Hyper-V provider."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    @pytest.mark.asyncio
    async def test_test_connection_healthy(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.test_connection()
        assert result["connected"] is True
        assert "latency_ms" in result
        assert result["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_test_connection_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockHyperVProvider()
        result = await provider.test_connection()
        assert result["connected"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_test_connection_auth_failure(self) -> None:
        set_mock_mode("auth_failure")
        provider = MockHyperVProvider()
        result = await provider.test_connection()
        assert result["connected"] is False
        assert "Access denied" in result["error"]

    @pytest.mark.asyncio
    async def test_get_summary_healthy(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_summary()
        assert result["connected"] is True
        assert result["total_vms"] == 6
        assert result["running"] == 4
        assert result["stopped"] == 1
        assert result["paused"] == 1
        assert result["total_cpu"] > 0
        assert result["total_memory_gb"] > 0

    @pytest.mark.asyncio
    async def test_get_summary_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockHyperVProvider()
        result = await provider.get_summary()
        assert result["connected"] is False
        assert result["total_vms"] == 0

    @pytest.mark.asyncio
    async def test_get_vms(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_vms()
        assert result["connected"] is True
        assert result["count"] == 6
        assert len(result["items"]) == 6

    @pytest.mark.asyncio
    async def test_get_vms_empty(self) -> None:
        set_mock_mode("empty")
        provider = MockHyperVProvider()
        result = await provider.get_vms()
        assert result["connected"] is True
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_vm_detail_found(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.get_vm_detail(vm_id)
        assert result["connected"] is True
        assert result["item"]["name"] == "DC01"

    @pytest.mark.asyncio
    async def test_get_vm_detail_not_found(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_vm_detail("nonexistent-id")
        assert result["connected"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_start_vm(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "d4e5f6a7-b8c9-0123-defa-234567890123"  # APP01 (stopped)
        result = await provider.start_vm(vm_id)
        assert result["success"] is True
        assert result["vm_name"] == "APP01"

    @pytest.mark.asyncio
    async def test_start_vm_already_running(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # DC01 (running)
        result = await provider.start_vm(vm_id)
        assert result["success"] is False
        assert "already running" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_vm(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # DC01 (running)
        result = await provider.stop_vm(vm_id)
        assert result["success"] is True
        assert result["vm_name"] == "DC01"

    @pytest.mark.asyncio
    async def test_stop_vm_force(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.stop_vm(vm_id, force=True)
        assert result["success"] is True
        assert "force stopped" in result["message"]

    @pytest.mark.asyncio
    async def test_stop_vm_already_stopped(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "d4e5f6a7-b8c9-0123-defa-234567890123"  # APP01 (stopped)
        result = await provider.stop_vm(vm_id)
        assert result["success"] is False
        assert "already stopped" in result["error"]

    @pytest.mark.asyncio
    async def test_restart_vm(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.restart_vm(vm_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_restart_vm_not_running(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "d4e5f6a7-b8c9-0123-defa-234567890123"  # stopped
        result = await provider.restart_vm(vm_id)
        assert result["success"] is False
        assert "must be running" in result["error"]

    @pytest.mark.asyncio
    async def test_pause_vm(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.pause_vm(vm_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pause_vm_not_running(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "d4e5f6a7-b8c9-0123-defa-234567890123"  # stopped
        result = await provider.pause_vm(vm_id)
        assert result["success"] is False
        assert "must be running" in result["error"]

    @pytest.mark.asyncio
    async def test_resume_vm(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "e5f6a7b8-c9d0-1234-efab-345678901234"  # TEST01 (paused)
        result = await provider.resume_vm(vm_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_resume_vm_not_paused(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # running
        result = await provider.resume_vm(vm_id)
        assert result["success"] is False
        assert "not paused" in result["error"]

    @pytest.mark.asyncio
    async def test_get_networks(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_networks()
        assert result["connected"] is True
        assert result["count"] == 4
        types = {n["switch_type"] for n in result["items"]}
        assert "external" in types
        assert "internal" in types
        assert "private" in types

    @pytest.mark.asyncio
    async def test_get_storage(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_storage()
        assert result["connected"] is True
        assert result["count"] == 9
        assert all(s["type"] == "vhdx" for s in result["items"])

    @pytest.mark.asyncio
    async def test_get_checkpoints_all(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_checkpoints()
        assert result["connected"] is True
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_get_checkpoints_by_vm(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # DC01
        result = await provider.get_checkpoints(vm_id)
        assert result["connected"] is True
        assert result["count"] == 2
        assert all(c["vm_id"] == vm_id for c in result["items"])

    @pytest.mark.asyncio
    async def test_create_checkpoint(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.create_checkpoint(vm_id, "Test CP")
        assert result["success"] is True
        assert result["checkpoint"]["name"] == "Test CP"

    @pytest.mark.asyncio
    async def test_create_checkpoint_auto_name(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.create_checkpoint(vm_id)
        assert result["success"] is True
        assert "DC01" in result["checkpoint"]["name"]

    @pytest.mark.asyncio
    async def test_delete_checkpoint(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = await provider.delete_checkpoint(vm_id, "cp-001")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_checkpoint_not_found(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.delete_checkpoint("vm-id", "cp-nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_health(self) -> None:
        provider = MockHyperVProvider()
        result = await provider.get_health()
        assert result["connected"] is True
        assert result["status"] == "healthy"
        assert len(result["hosts"]) == 2

    @pytest.mark.asyncio
    async def test_get_health_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockHyperVProvider()
        result = await provider.get_health()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_vm_not_found_operations(self) -> None:
        provider = MockHyperVProvider()
        fake_id = "nonexistent-id"
        assert (await provider.start_vm(fake_id))["success"] is False
        assert (await provider.stop_vm(fake_id))["success"] is False
        assert (await provider.restart_vm(fake_id))["success"] is False
        assert (await provider.pause_vm(fake_id))["success"] is False
        assert (await provider.resume_vm(fake_id))["success"] is False


# ------------------------------------------------------------------ #
# Provider Factory Tests                                              #
# ------------------------------------------------------------------ #


class TestHyperVProviderFactory:
    """Tests for the Hyper-V provider factory."""

    def teardown_method(self) -> None:
        reset_hyperv_provider()

    def test_factory_returns_mock_when_not_configured(self) -> None:
        reset_hyperv_provider()
        provider = get_hyperv_provider()
        assert isinstance(provider, MockHyperVProvider)

    def test_factory_is_singleton(self) -> None:
        reset_hyperv_provider()
        p1 = get_hyperv_provider()
        p2 = get_hyperv_provider()
        assert p1 is p2

    def test_reset_provider(self) -> None:
        p1 = get_hyperv_provider()
        reset_hyperv_provider()
        p2 = get_hyperv_provider()
        assert p1 is not p2


# ------------------------------------------------------------------ #
# Service Tests                                                       #
# ------------------------------------------------------------------ #


class TestHyperVService:
    """Tests for the Hyper-V service layer."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    @pytest.mark.asyncio
    async def test_service_get_summary(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.get_summary()
        assert result["connected"] is True
        assert result["total_vms"] == 6

    @pytest.mark.asyncio
    async def test_service_get_vms(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.get_vms()
        assert result["count"] == 6

    @pytest.mark.asyncio
    async def test_service_start_vm(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.start_vm("d4e5f6a7-b8c9-0123-defa-234567890123")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_service_get_networks(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.get_networks()
        assert result["count"] == 4

    @pytest.mark.asyncio
    async def test_service_get_storage(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.get_storage()
        assert result["count"] == 9

    @pytest.mark.asyncio
    async def test_service_get_checkpoints(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.get_checkpoints()
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_service_get_health(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.get_health()
        assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_service_test_connection(self) -> None:
        from app.services.hyperv_service import HyperVService

        service = HyperVService()
        result = await service.test_connection()
        assert result["connected"] is True


# ------------------------------------------------------------------ #
# Router Tests                                                        #
# ------------------------------------------------------------------ #


class TestHyperVRouter:
    """Tests for the Hyper-V API endpoints."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    def test_overview(self, client) -> None:
        response = client.get("/api/v1/hyperv/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["total_vms"] == 6
        assert data["running"] == 4

    def test_test_connection(self, client) -> None:
        response = client.get("/api/v1/hyperv/test")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["latency_ms"] > 0

    def test_health(self, client) -> None:
        response = client.get("/api/v1/hyperv/health")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert len(data["hosts"]) == 2

    def test_list_vms(self, client) -> None:
        response = client.get("/api/v1/hyperv/vms")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6
        assert len(data["items"]) == 6

    def test_get_vm(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.get(f"/api/v1/hyperv/vms/{vm_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["item"]["name"] == "DC01"

    def test_start_vm(self, client) -> None:
        vm_id = "d4e5f6a7-b8c9-0123-defa-234567890123"
        response = client.post(f"/api/v1/hyperv/vms/{vm_id}/start")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_stop_vm(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.post(f"/api/v1/hyperv/vms/{vm_id}/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_restart_vm(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.post(f"/api/v1/hyperv/vms/{vm_id}/restart")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_pause_vm(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.post(f"/api/v1/hyperv/vms/{vm_id}/pause")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_resume_vm(self, client) -> None:
        vm_id = "e5f6a7b8-c9d0-1234-efab-345678901234"
        response = client.post(f"/api/v1/hyperv/vms/{vm_id}/resume")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_networks(self, client) -> None:
        response = client.get("/api/v1/hyperv/networks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4

    def test_list_storage(self, client) -> None:
        response = client.get("/api/v1/hyperv/storage")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 9

    def test_list_checkpoints(self, client) -> None:
        response = client.get("/api/v1/hyperv/checkpoints")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    def test_list_checkpoints_filtered(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.get(f"/api/v1/hyperv/checkpoints?vm_id={vm_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_create_checkpoint(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.post(
            "/api/v1/hyperv/checkpoints",
            json={"vm_id": vm_id, "name": "Test Checkpoint"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_checkpoint(self, client) -> None:
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        response = client.delete(f"/api/v1/hyperv/vms/{vm_id}/checkpoints/cp-001")
        assert response.status_code == 200
        assert response.json()["success"] is True


# ------------------------------------------------------------------ #
# Dashboard Provider Tests                                            #
# ------------------------------------------------------------------ #


class TestHyperVDashboardProvider:
    """Tests for the Hyper-V dashboard provider."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_hyperv_provider()


# ------------------------------------------------------------------ #
# VirtualizationProvider Abstraction Tests                            #
# ------------------------------------------------------------------ #


class TestVirtualizationProvider:
    """Tests that HyperVProvider properly extends VirtualizationProvider."""

    def test_mock_provider_is_virtualization_provider(self) -> None:
        from app.providers.virtualization import VirtualizationProvider

        provider = MockHyperVProvider()
        assert isinstance(provider, VirtualizationProvider)

    @pytest.mark.asyncio
    async def test_virtualization_aliases_delegate(self) -> None:
        provider = MockHyperVProvider()
        vm_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        snapshots = await provider.get_snapshots(vm_id)
        checkpoints = await provider.get_checkpoints(vm_id)
        assert snapshots == checkpoints

        snap_result = await provider.create_snapshot(vm_id, "snap-test")
        cp_result = await provider.create_checkpoint(vm_id, "snap-test")
        assert snap_result["success"] == cp_result["success"]

        delete_result = await provider.delete_snapshot(vm_id, "cp-001")
        assert delete_result["success"] is True


# ------------------------------------------------------------------ #
# Domain Model Tests                                                  #
# ------------------------------------------------------------------ #


class TestDomainModels:
    """Tests for VirtualizationProvider domain models."""

    def test_virtual_machine_model(self) -> None:
        from app.providers.virtualization import VirtualMachine

        vm = VirtualMachine(
            id="vm-001",
            name="TEST-VM",
            state="running",
            cpu_count=4,
            memory_assigned_mb=8192,
            host_server="HV-HOST01",
        )
        assert vm.id == "vm-001"
        assert vm.name == "TEST-VM"
        assert vm.state == "running"
        assert vm.cpu_count == 4
        assert vm.memory_assigned_mb == 8192
        assert vm.host_server == "HV-HOST01"
        assert vm.guest_os == ""

    def test_virtual_host_model(self) -> None:
        from app.providers.virtualization import VirtualHost

        host = VirtualHost(
            name="HV-HOST01",
            status="healthy",
            cpu_percent=45.2,
            memory_percent=68.1,
            vm_count=3,
        )
        assert host.name == "HV-HOST01"
        assert host.status == "healthy"
        assert host.cpu_percent == 45.2
        assert host.vm_count == 3
        assert host.uptime_seconds == 0

    def test_virtual_network_model(self) -> None:
        from app.providers.virtualization import VirtualNetwork

        net = VirtualNetwork(
            id="net-001",
            name="Management",
            switch_type="external",
        )
        assert net.id == "net-001"
        assert net.name == "Management"
        assert net.switch_type == "external"
        assert net.vlan_id is None

    def test_virtual_storage_model(self) -> None:
        from app.providers.virtualization import VirtualStorage

        disk = VirtualStorage(
            id="disk-001",
            name="DC01-OS.vhdx",
            path="C:\\VMs\\DC01\\disk.vhdx",
            size_bytes=107374182400,
            used_bytes=53687091200,
        )
        assert disk.id == "disk-001"
        assert disk.name == "DC01-OS.vhdx"
        assert disk.size_bytes == 107374182400
        assert disk.used_bytes == 53687091200
        assert disk.vm_name is None

    def test_snapshot_model(self) -> None:
        from app.providers.virtualization import Snapshot

        snap = Snapshot(
            id="snap-001",
            name="Pre-patch",
            vm_name="DC01",
            creation_time="2026-07-01T12:00:00",
        )
        assert snap.id == "snap-001"
        assert snap.name == "Pre-patch"
        assert snap.vm_name == "DC01"
        assert snap.size_bytes == 0
        assert snap.parent_checkpoint_id is None
