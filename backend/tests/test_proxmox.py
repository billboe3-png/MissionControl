"""
Mission Control Proxmox Tests

Tests the Proxmox provider, service, router, schemas, mock provider,
VirtualizationProvider abstraction, and domain models.
"""


import pytest

from app.providers.proxmox.mock_provider import MockProxmoxProvider, set_mock_mode
from app.providers.proxmox.provider_factory import (
    get_proxmox_provider,
    reset_proxmox_provider,
)

# ------------------------------------------------------------------ #
# Mock Provider Tests                                                 #
# ------------------------------------------------------------------ #


class TestMockProxmoxProvider:
    """Tests for the mock Proxmox provider."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    @pytest.mark.asyncio
    async def test_test_connection_healthy(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.test_connection()
        assert result["connected"] is True
        assert "latency_ms" in result
        assert result["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_test_connection_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockProxmoxProvider()
        result = await provider.test_connection()
        assert result["connected"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_test_connection_auth_failure(self) -> None:
        set_mock_mode("auth_failure")
        provider = MockProxmoxProvider()
        result = await provider.test_connection()
        assert result["connected"] is False
        assert "Authentication failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_summary_healthy(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_summary()
        assert result["connected"] is True
        assert result["total_vms"] == 6
        assert result["running"] == 4
        assert result["stopped"] == 1
        assert result["paused"] == 1
        assert result["total_lxc"] == 4
        assert result["running_lxc"] == 3
        assert result["nodes_online"] == 2
        assert result["total_cpu"] > 0
        assert result["total_memory_gb"] > 0

    @pytest.mark.asyncio
    async def test_get_summary_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockProxmoxProvider()
        result = await provider.get_summary()
        assert result["connected"] is False
        assert result["total_vms"] == 0

    @pytest.mark.asyncio
    async def test_get_nodes(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_nodes()
        assert result["connected"] is True
        assert result["count"] == 2
        assert result["items"][0]["name"] == "pve-node01"

    @pytest.mark.asyncio
    async def test_get_vms(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_vms()
        assert result["connected"] is True
        assert result["count"] == 6
        assert len(result["items"]) == 6

    @pytest.mark.asyncio
    async def test_get_vms_empty(self) -> None:
        set_mock_mode("empty")
        provider = MockProxmoxProvider()
        result = await provider.get_vms()
        assert result["connected"] is True
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_vm_detail_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_vm_detail("100")
        assert result["connected"] is True
        assert result["item"]["name"] == "web-prod-01"

    @pytest.mark.asyncio
    async def test_get_vm_detail_not_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_vm_detail("999")
        assert result["connected"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_start_vm(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.start_vm("103")
        assert result["success"] is True
        assert result["vm_name"] == "app-staging-01"

    @pytest.mark.asyncio
    async def test_start_vm_already_running(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.start_vm("100")
        assert result["success"] is False
        assert "already running" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_vm(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.stop_vm("100")
        assert result["success"] is True
        assert result["vm_name"] == "web-prod-01"

    @pytest.mark.asyncio
    async def test_stop_vm_force(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.stop_vm("100", force=True)
        assert result["success"] is True
        assert "force" in result["message"]

    @pytest.mark.asyncio
    async def test_stop_vm_already_stopped(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.stop_vm("103")
        assert result["success"] is False
        assert "already stopped" in result["error"]

    @pytest.mark.asyncio
    async def test_restart_vm(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.restart_vm("100")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_restart_vm_not_running(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.restart_vm("103")
        assert result["success"] is False
        assert "must be running" in result["error"]

    @pytest.mark.asyncio
    async def test_pause_vm(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.pause_vm("100")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pause_vm_not_running(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.pause_vm("103")
        assert result["success"] is False
        assert "must be running" in result["error"]

    @pytest.mark.asyncio
    async def test_resume_vm(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.resume_vm("105")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_resume_vm_not_paused(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.resume_vm("100")
        assert result["success"] is False
        assert "not suspended" in result["error"]

    @pytest.mark.asyncio
    async def test_get_networks(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_networks()
        assert result["connected"] is True
        assert result["count"] == 4
        types = {n["switch_type"] for n in result["items"]}
        assert "bridge" in types
        assert "bond" in types

    @pytest.mark.asyncio
    async def test_get_storage(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_storage()
        assert result["connected"] is True
        assert result["count"] == 6

    @pytest.mark.asyncio
    async def test_get_snapshots_all(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_snapshots()
        assert result["connected"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_get_snapshots_by_vm(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_snapshots("100")
        assert result["connected"] is True
        assert result["count"] == 2
        assert all(s["vm_id"] == "100" for s in result["items"])

    @pytest.mark.asyncio
    async def test_create_snapshot(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.create_snapshot("100", "Test Snap")
        assert result["success"] is True
        assert result["snapshot"]["name"] == "Test Snap"

    @pytest.mark.asyncio
    async def test_create_snapshot_auto_name(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.create_snapshot("100")
        assert result["success"] is True
        assert "web-prod-01" in result["snapshot"]["name"]

    @pytest.mark.asyncio
    async def test_delete_snapshot(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.delete_snapshot("100", "snap-1719000000")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_snapshot_not_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.delete_snapshot("100", "snap/nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_health(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_health()
        assert result["connected"] is True
        assert result["status"] == "healthy"
        assert len(result["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_get_health_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockProxmoxProvider()
        result = await provider.get_health()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_get_tasks(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_tasks()
        assert result["connected"] is True
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_get_tasks_by_node(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_tasks("pve-node01")
        assert result["connected"] is True
        assert result["count"] == 3
        assert all(t["node"] == "pve-node01" for t in result["items"])

    @pytest.mark.asyncio
    async def test_get_lxc_containers(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_lxc_containers()
        assert result["connected"] is True
        assert result["count"] == 4
        assert len(result["items"]) == 4

    @pytest.mark.asyncio
    async def test_get_lxc_detail_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_lxc_detail("200")
        assert result["connected"] is True
        assert result["item"]["name"] == "dns-resolver"

    @pytest.mark.asyncio
    async def test_get_lxc_detail_not_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_lxc_detail("999")
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_start_lxc(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.start_lxc("202")
        assert result["success"] is True
        assert result["vm_name"] == "ci-runner-01"

    @pytest.mark.asyncio
    async def test_start_lxc_already_running(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.start_lxc("200")
        assert result["success"] is False
        assert "already running" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_lxc(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.stop_lxc("200")
        assert result["success"] is True
        assert result["vm_name"] == "dns-resolver"

    @pytest.mark.asyncio
    async def test_stop_lxc_already_stopped(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.stop_lxc("202")
        assert result["success"] is False
        assert "already stopped" in result["error"]

    @pytest.mark.asyncio
    async def test_vm_not_found_operations(self) -> None:
        provider = MockProxmoxProvider()
        fake_id = "999"
        assert (await provider.start_vm(fake_id))["success"] is False
        assert (await provider.stop_vm(fake_id))["success"] is False
        assert (await provider.restart_vm(fake_id))["success"] is False
        assert (await provider.pause_vm(fake_id))["success"] is False
        assert (await provider.resume_vm(fake_id))["success"] is False

    @pytest.mark.asyncio
    async def test_lxc_not_found_operations(self) -> None:
        provider = MockProxmoxProvider()
        fake_id = "999"
        assert (await provider.start_lxc(fake_id))["success"] is False
        assert (await provider.stop_lxc(fake_id))["success"] is False

    @pytest.mark.asyncio
    async def test_get_lxc_templates(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.get_lxc_templates()
        assert result["connected"] is True
        assert result["count"] == 3
        names = [t["name"] for t in result["items"]]
        assert any("mission-control" in n for n in names)

    @pytest.mark.asyncio
    async def test_get_lxc_templates_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockProxmoxProvider()
        result = await provider.get_lxc_templates()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_create_lxc(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.create_lxc({
            "node": "pve-node01",
            "ostemplate": "local:vztmpl/mission-control-v3.0.0-amd64.tar.zst",
            "hostname": "mc-test",
            "cores": 4,
            "memory": 8192,
        })
        assert result["success"] is True
        assert "vmid" in result
        assert result["node"] == "pve-node01"

    @pytest.mark.asyncio
    async def test_create_lxc_offline(self) -> None:
        set_mock_mode("offline")
        provider = MockProxmoxProvider()
        result = await provider.create_lxc({
            "node": "pve-node01",
            "ostemplate": "local:vztmpl/debian-12.tar.zst",
            "hostname": "test",
        })
        assert result["success"] is False
        assert "Host unreachable" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_lxc(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.delete_lxc("202")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_lxc_not_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.delete_lxc("999")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_clone_lxc(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.clone_lxc("200", new_vmid="250", hostname="dns-clone")
        assert result["success"] is True
        assert result["vmid"] == "250"

    @pytest.mark.asyncio
    async def test_clone_lxc_not_found(self) -> None:
        provider = MockProxmoxProvider()
        result = await provider.clone_lxc("999")
        assert result["success"] is False
        assert "not found" in result["error"]


# ------------------------------------------------------------------ #
# Provider Factory Tests                                              #
# ------------------------------------------------------------------ #


class TestProxmoxProviderFactory:
    """Tests for the Proxmox provider factory."""

    def teardown_method(self) -> None:
        reset_proxmox_provider()

    def test_factory_returns_mock_when_not_configured(self) -> None:
        reset_proxmox_provider()
        provider = get_proxmox_provider()
        assert isinstance(provider, MockProxmoxProvider)

    def test_factory_is_singleton(self) -> None:
        reset_proxmox_provider()
        p1 = get_proxmox_provider()
        p2 = get_proxmox_provider()
        assert p1 is p2

    def test_reset_provider(self) -> None:
        p1 = get_proxmox_provider()
        reset_proxmox_provider()
        p2 = get_proxmox_provider()
        assert p1 is not p2


# ------------------------------------------------------------------ #
# Service Tests                                                       #
# ------------------------------------------------------------------ #


class TestProxmoxService:
    """Tests for the Proxmox service layer."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    @pytest.mark.asyncio
    async def test_service_get_summary(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_summary()
        assert result["connected"] is True
        assert result["total_vms"] == 6

    @pytest.mark.asyncio
    async def test_service_get_vms(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_vms()
        assert result["count"] == 6

    @pytest.mark.asyncio
    async def test_service_get_nodes(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_nodes()
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_service_start_vm(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.start_vm("103")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_service_get_networks(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_networks()
        assert result["count"] == 4

    @pytest.mark.asyncio
    async def test_service_get_storage(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_storage()
        assert result["count"] == 6

    @pytest.mark.asyncio
    async def test_service_get_snapshots(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_snapshots()
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_service_get_health(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_health()
        assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_service_test_connection(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.test_connection()
        assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_service_get_tasks(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_tasks()
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_service_get_lxc(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.get_lxc_containers()
        assert result["count"] == 4

    @pytest.mark.asyncio
    async def test_service_start_lxc(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.start_lxc("202")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_service_stop_lxc(self) -> None:
        from app.services.proxmox_service import ProxmoxService

        service = ProxmoxService()
        result = await service.stop_lxc("200")
        assert result["success"] is True


# ------------------------------------------------------------------ #
# Router Tests                                                        #
# ------------------------------------------------------------------ #


class TestProxmoxRouter:
    """Tests for the Proxmox API endpoints."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    def test_overview(self, client) -> None:
        response = client.get("/api/v1/proxmox/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["total_vms"] == 6
        assert data["running"] == 4

    def test_test_connection(self, client) -> None:
        response = client.get("/api/v1/proxmox/test")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["latency_ms"] > 0

    def test_health(self, client) -> None:
        response = client.get("/api/v1/proxmox/health")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert len(data["nodes"]) == 2

    def test_list_nodes(self, client) -> None:
        response = client.get("/api/v1/proxmox/nodes")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["items"][0]["name"] == "pve-node01"

    def test_list_vms(self, client) -> None:
        response = client.get("/api/v1/proxmox/vms")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6
        assert len(data["items"]) == 6

    def test_get_vm(self, client) -> None:
        response = client.get("/api/v1/proxmox/vms/100")
        assert response.status_code == 200
        data = response.json()
        assert data["item"]["name"] == "web-prod-01"

    def test_start_vm(self, client) -> None:
        response = client.post("/api/v1/proxmox/vms/103/start")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_stop_vm(self, client) -> None:
        response = client.post("/api/v1/proxmox/vms/100/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_restart_vm(self, client) -> None:
        response = client.post("/api/v1/proxmox/vms/100/restart")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_pause_vm(self, client) -> None:
        response = client.post("/api/v1/proxmox/vms/100/pause")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_resume_vm(self, client) -> None:
        response = client.post("/api/v1/proxmox/vms/105/resume")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_lxc(self, client) -> None:
        response = client.get("/api/v1/proxmox/lxc")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4

    def test_get_lxc(self, client) -> None:
        response = client.get("/api/v1/proxmox/lxc/200")
        assert response.status_code == 200
        data = response.json()
        assert data["item"]["name"] == "dns-resolver"

    def test_start_lxc(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc/202/start")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_stop_lxc(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc/200/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_networks(self, client) -> None:
        response = client.get("/api/v1/proxmox/networks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4

    def test_list_storage(self, client) -> None:
        response = client.get("/api/v1/proxmox/storage")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6

    def test_list_tasks(self, client) -> None:
        response = client.get("/api/v1/proxmox/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    def test_list_tasks_filtered(self, client) -> None:
        response = client.get("/api/v1/proxmox/tasks?node=pve-node01")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_list_snapshots(self, client) -> None:
        response = client.get("/api/v1/proxmox/snapshots")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_list_snapshots_filtered(self, client) -> None:
        response = client.get("/api/v1/proxmox/snapshots?vm_id=100")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_create_snapshot(self, client) -> None:
        response = client.post(
            "/api/v1/proxmox/snapshots",
            json={"vm_id": "100", "name": "Test Snapshot"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_snapshot(self, client) -> None:
        response = client.delete("/api/v1/proxmox/vms/100/snapshots/snap-1719000000")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_lxc_templates(self, client) -> None:
        response = client.get("/api/v1/proxmox/lxc/templates")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert any("mission-control" in t["name"] for t in data["items"])

    def test_list_lxc_templates_filtered(self, client) -> None:
        response = client.get("/api/v1/proxmox/lxc/templates?node=pve-node01")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_create_lxc(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc", json={
            "node": "pve-node01",
            "ostemplate": "local:vztmpl/mission-control-v3.0.0-amd64.tar.zst",
            "hostname": "mc-test",
            "cores": 2,
            "memory": 4096,
            "disk": 8,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["vmid"] is not None
        assert data["node"] == "pve-node01"

    def test_create_lxc_minimal(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc", json={
            "node": "pve-node01",
            "ostemplate": "local:vztmpl/debian-12.tar.zst",
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_create_lxc_missing_template(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc", json={
            "node": "pve-node01",
        })
        assert response.status_code == 422

    def test_clone_lxc(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc/200/clone", json={
            "new_vmid": "250",
            "hostname": "dns-clone",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["vmid"] == "250"

    def test_clone_lxc_not_found(self, client) -> None:
        response = client.post("/api/v1/proxmox/lxc/999/clone")
        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_delete_lxc(self, client) -> None:
        response = client.delete("/api/v1/proxmox/lxc/202")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_lxc_not_found(self, client) -> None:
        response = client.delete("/api/v1/proxmox/lxc/999")
        assert response.status_code == 200
        assert response.json()["success"] is False


# ------------------------------------------------------------------ #
# Dashboard Provider Tests                                            #
# ------------------------------------------------------------------ #


class TestProxmoxDashboardProvider:
    """Tests for the Proxmox dashboard provider."""

    def setup_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    def teardown_method(self) -> None:
        set_mock_mode("healthy")
        reset_proxmox_provider()

    @pytest.mark.asyncio
    async def test_dashboard_provider_data(self) -> None:
        from app.providers.proxmox_dashboard import ProxmoxDashboardProvider

        provider = ProxmoxDashboardProvider()
        result = await provider.get_proxmox_data(None)
        assert result["connected"] is True
        assert result["total_vms"] == 6
        assert result["running"] == 4
        assert result["running_lxc"] == 3

    @pytest.mark.asyncio
    async def test_dashboard_provider_offline(self) -> None:
        set_mock_mode("offline")
        from app.providers.proxmox_dashboard import ProxmoxDashboardProvider

        provider = ProxmoxDashboardProvider()
        result = await provider.get_proxmox_data(None)
        assert result["connected"] is False
        assert result["total_vms"] == 0


# ------------------------------------------------------------------ #
# VirtualizationProvider Abstraction Tests                            #
# ------------------------------------------------------------------ #


class TestVirtualizationProvider:
    """Tests that ProxmoxProvider properly extends VirtualizationProvider."""

    def test_mock_provider_is_virtualization_provider(self) -> None:
        from app.providers.virtualization import VirtualizationProvider

        provider = MockProxmoxProvider()
        assert isinstance(provider, VirtualizationProvider)

    def test_mock_provider_is_proxmox_provider(self) -> None:
        from app.providers.proxmox.base_provider import ProxmoxProvider

        provider = MockProxmoxProvider()
        assert isinstance(provider, ProxmoxProvider)
