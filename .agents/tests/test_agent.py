"""Tests for Mission Control Agent standalone components."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.command_queue import CommandQueue
from agent.config import AgentSettings
from agent.executor import CommandExecutor
from agent.inventory import InventoryCollector
from agent.plugin import PluginManager

# ------------------------------------------------------------------ #
# Config Tests                                                        #
# ------------------------------------------------------------------ #


class TestAgentSettings:
    def test_default_settings(self):
        settings = AgentSettings()
        assert settings.heartbeat_interval == 30
        assert settings.inventory_interval == 300
        assert settings.verify_ssl is True
        assert settings.command_timeout == 60

    def test_custom_settings(self, monkeypatch):
        monkeypatch.delenv("MC_SERVER_URL", raising=False)
        monkeypatch.delenv("MC_API_KEY", raising=False)
        monkeypatch.delenv("MC_AGENT_ID", raising=False)
        monkeypatch.delenv("MC_HEARTBEAT_INTERVAL", raising=False)
        settings = AgentSettings(
            server_url="https://custom.server.com",
            api_key="test_key",
            agent_id=42,
            heartbeat_interval=60,
        )
        assert settings.server_url == "https://custom.server.com"
        assert settings.api_key == "test_key"
        assert settings.agent_id == 42
        assert settings.heartbeat_interval == 60


# ------------------------------------------------------------------ #
# Command Queue Tests                                                 #
# ------------------------------------------------------------------ #


class TestCommandQueue:
    def test_queue_and_dequeue(self, tmp_path):
        queue = CommandQueue(data_dir=tmp_path)
        queue.queue_command({"id": 1, "command": "test"})
        queue.queue_command({"id": 2, "command": "test2"})

        assert queue.get_pending_count() == 2

        cmd = queue.dequeue_command()
        assert cmd is not None
        assert cmd["id"] == 1

        cmd = queue.dequeue_command()
        assert cmd is not None
        assert cmd["id"] == 2

        assert queue.get_pending_count() == 0

    def test_dequeue_empty(self, tmp_path):
        queue = CommandQueue(data_dir=tmp_path)
        assert queue.dequeue_command() is None

    def test_result_queue(self, tmp_path):
        queue = CommandQueue(data_dir=tmp_path)
        queue.queue_result({"command_id": 1, "success": True})
        assert queue.get_results_count() == 1

        result = queue.dequeue_result()
        assert result is not None
        assert result["command_id"] == 1

    def test_clear(self, tmp_path):
        queue = CommandQueue(data_dir=tmp_path)
        queue.queue_command({"id": 1})
        queue.queue_result({"id": 1})
        queue.clear()
        assert queue.get_pending_count() == 0
        assert queue.get_results_count() == 0

    def test_max_size(self, tmp_path):
        queue = CommandQueue(data_dir=tmp_path, max_size=3)
        for i in range(5):
            queue.queue_command({"id": i})
        assert queue.get_pending_count() == 3


# ------------------------------------------------------------------ #
# Inventory Tests                                                     #
# ------------------------------------------------------------------ #


class TestInventoryCollector:
    def test_collect_system(self):
        collector = InventoryCollector()
        inventory = collector.collect()
        assert "system" in inventory
        assert "hostname" in inventory["system"]
        assert "platform" in inventory["system"]

    def test_collect_cpu(self):
        collector = InventoryCollector()
        inventory = collector.collect()
        assert "cpu" in inventory
        assert "logical_cores" in inventory["cpu"]

    def test_collect_memory(self):
        collector = InventoryCollector()
        inventory = collector.collect()
        assert "memory" in inventory
        assert "total" in inventory["memory"]
        assert inventory["memory"]["total"] > 0

    def test_collect_disks(self):
        collector = InventoryCollector()
        inventory = collector.collect()
        assert "disks" in inventory
        assert isinstance(inventory["disks"], list)

    def test_collect_network(self):
        collector = InventoryCollector()
        inventory = collector.collect()
        assert "network" in inventory
        assert "interfaces" in inventory["network"]

    def test_collect_health_metrics(self):
        collector = InventoryCollector()
        metrics = collector.collect_health_metrics()
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics

    def test_collect_full_inventory(self):
        collector = InventoryCollector()
        inventory = collector.collect()
        expected_keys = [
            "system", "cpu", "memory", "disks",
            "network", "services", "docker", "software",
        ]
        for key in expected_keys:
            assert key in inventory, f"Missing key: {key}"


# ------------------------------------------------------------------ #
# Executor Tests                                                      #
# ------------------------------------------------------------------ #


class TestCommandExecutor:
    @pytest.mark.asyncio
    async def test_execute_shell(self):
        executor = CommandExecutor(timeout=10)
        result = await executor.execute(
            "echo hello", command_type="execute"
        )
        assert result["success"] is True
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_execute_failing_command(self):
        executor = CommandExecutor(timeout=10)
        result = await executor.execute(
            "exit 1", command_type="execute"
        )
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_execute_script(self):
        executor = CommandExecutor(timeout=10)
        result = await executor.execute(
            "echo 'script output'", command_type="script"
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unknown_command_type(self):
        executor = CommandExecutor(timeout=10)
        result = await executor.execute(
            "test", command_type="unknown"
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_upload_file(self):
        executor = CommandExecutor(timeout=10)
        import base64

        content = base64.b64encode(b"test content").decode()
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt"
        ) as tmp:
            tmp_path = tmp.name

        try:
            result = await executor.execute(
                command="",
                command_type="upload",
                file_path=tmp_path,
                file_name="test.txt",
                file_content_b64=content,
            )
            assert result["success"] is True
            with open(tmp_path, "rb") as f:
                assert f.read() == b"test content"
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_download_file(self):
        executor = CommandExecutor(timeout=10)
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", mode="w"
        ) as tmp:
            tmp.write("download me")
            tmp_path = tmp.name

        try:
            result = await executor.execute(
                command="",
                command_type="download",
                file_path=tmp_path,
            )
            assert result["success"] is True
            assert "file_content_b64" in result
        finally:
            os.unlink(tmp_path)


# ------------------------------------------------------------------ #
# Plugin Manager Tests                                                #
# ------------------------------------------------------------------ #


class TestPluginManager:
    @pytest.mark.asyncio
    async def test_discover_plugins(self):
        manager = PluginManager()
        discovered = await manager.discover_plugins()
        assert isinstance(discovered, list)

    @pytest.mark.asyncio
    async def test_initialize_empty(self):
        manager = PluginManager()
        results = await manager.initialize_plugins({})
        assert isinstance(results, dict)

    def test_get_active_plugins_empty(self):
        manager = PluginManager()
        assert manager.get_active_plugins() == ""

    @pytest.mark.asyncio
    async def test_shutdown_all(self):
        manager = PluginManager()
        await manager.shutdown_all()
        assert manager.plugin_count == 0


# ------------------------------------------------------------------ #
# Health Determination Tests                                          #
# ------------------------------------------------------------------ #


class TestHealthDetermination:
    def _make_agent(self):
        from agent.agent import MissionControlAgent

        config = AgentSettings(
            server_url="https://test.local",
            api_key="test_key",
            agent_id=1,
        )
        with patch.object(MissionControlAgent, "__init__", lambda self, c: None):
            agent = MissionControlAgent.__new__(MissionControlAgent)
            agent.config = config
            return agent

    def test_healthy(self):
        agent = self._make_agent()
        assert agent._determine_health({}) == "healthy"
        assert agent._determine_health({
            "cpu_percent": 50, "memory_percent": 60, "disk_percent": 70
        }) == "healthy"

    def test_warning_cpu(self):
        agent = self._make_agent()
        assert agent._determine_health({"cpu_percent": 90}) == "warning"

    def test_warning_memory(self):
        agent = self._make_agent()
        assert agent._determine_health({"memory_percent": 86}) == "warning"

    def test_warning_disk(self):
        agent = self._make_agent()
        assert agent._determine_health({"disk_percent": 91}) == "warning"

    def test_critical_cpu(self):
        agent = self._make_agent()
        assert agent._determine_health({"cpu_percent": 96}) == "critical"

    def test_critical_memory(self):
        agent = self._make_agent()
        assert agent._determine_health({"memory_percent": 96}) == "critical"

    def test_critical_disk(self):
        agent = self._make_agent()
        assert agent._determine_health({"disk_percent": 96}) == "critical"

    def test_boundary_85_is_warning(self):
        agent = self._make_agent()
        assert agent._determine_health({"cpu_percent": 86}) == "warning"

    def test_boundary_95_is_critical(self):
        agent = self._make_agent()
        assert agent._determine_health({"cpu_percent": 96}) == "critical"


# ------------------------------------------------------------------ #
# Agent Updater Tests                                                 #
# ------------------------------------------------------------------ #


class TestAgentUpdater:
    @pytest.mark.asyncio
    async def test_check_for_update_available(self):
        from agent.updater import AgentUpdater

        client = AsyncMock()
        client.get = AsyncMock(return_value={"version": "2.0.0"})
        updater = AgentUpdater(client, "1.0.0")
        result = await updater.check_for_update()
        assert result["update_available"] is True
        assert result["latest_version"] == "2.0.0"
        assert result["current_version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_check_for_update_none_available(self):
        from agent.updater import AgentUpdater

        client = AsyncMock()
        client.get = AsyncMock(return_value={"version": "1.0.0"})
        updater = AgentUpdater(client, "1.0.0")
        result = await updater.check_for_update()
        assert result["update_available"] is False

    @pytest.mark.asyncio
    async def test_check_for_update_server_error(self):
        from agent.updater import AgentUpdater

        client = AsyncMock()
        client.get = AsyncMock(side_effect=Exception("connection"))
        updater = AgentUpdater(client, "1.0.0")
        result = await updater.check_for_update()
        assert result["update_available"] is False
        assert result["current_version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_perform_update_no_update_needed(self):
        from agent.updater import AgentUpdater

        client = AsyncMock()
        client.get = AsyncMock(return_value={"version": "1.0.0"})
        updater = AgentUpdater(client, "1.0.0")
        result = await updater.perform_update()
        assert result["updated"] is False

    def test_compare_versions(self):
        from agent.updater import AgentUpdater

        assert AgentUpdater._compare_versions("2.0.0", "1.0.0") is True
        assert AgentUpdater._compare_versions("1.0.0", "2.0.0") is False
        assert AgentUpdater._compare_versions("1.0.0", "1.0.0") is False


# ------------------------------------------------------------------ #
# Agent Client Tests                                                  #
# ------------------------------------------------------------------ #


class TestAgentClient:
    @pytest.mark.asyncio
    async def test_set_api_key(self):
        from agent.client import AgentClient

        client = AgentClient("https://test.local", api_key="old")
        client.set_api_key("new_key")
        assert client.api_key == "new_key"

    @pytest.mark.asyncio
    async def test_post_success(self):
        from agent.client import AgentClient

        client = AgentClient(
            "https://test.local", api_key="key", max_retries=1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.post("/api/test", {"data": 1})
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_get_success(self):
        from agent.client import AgentClient

        client = AgentClient(
            "https://test.local", api_key="key", max_retries=1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.get("/api/test")
        assert result == {"items": []}


# ------------------------------------------------------------------ #
# Heartbeat Manager Tests                                             #
# ------------------------------------------------------------------ #


class TestHeartbeatManager:
    @pytest.mark.asyncio
    async def test_send_heartbeat(self):
        from agent.config import AgentSettings
        from agent.heartbeat import HeartbeatManager

        config = AgentSettings()
        client = AsyncMock()
        client.post = AsyncMock(return_value={"commands": []})
        hm = HeartbeatManager(client, config)
        result = await hm.send_heartbeat(
            agent_id=1, health="healthy",
            cpu_percent=50.0, memory_percent=60.0,
        )
        assert result == {"commands": []}
        client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_heartbeat_with_commands(self):
        from agent.config import AgentSettings
        from agent.heartbeat import HeartbeatManager

        config = AgentSettings()
        client = AsyncMock()
        pending = [{"id": 1, "command_type": "execute", "command": "ls"}]
        client.post = AsyncMock(return_value={"commands": pending})
        hm = HeartbeatManager(client, config)
        result = await hm.send_heartbeat(agent_id=1)
        assert len(result["commands"]) == 1


# ------------------------------------------------------------------ #
# Registration Manager Tests                                          #
# ------------------------------------------------------------------ #


class TestRegistrationManager:
    @pytest.mark.asyncio
    async def test_register(self):
        from agent.config import AgentSettings
        from agent.registration import RegistrationManager

        config = AgentSettings()
        client = AsyncMock()
        client.post = AsyncMock(return_value={
            "agent_id": 42,
            "api_key": "abc123def456",
        })
        rm = RegistrationManager(client, config)
        result = await rm.register(
            hostname="test-host",
            os_name="Linux",
            os_version="6.1.0",
            ip_address="10.0.0.1",
            agent_version="1.0.0",
        )
        assert result["agent_id"] == 42
        assert result["api_key"] == "abc123def456"

    @pytest.mark.asyncio
    async def test_register_failure(self):
        from agent.config import AgentSettings
        from agent.registration import RegistrationManager

        config = AgentSettings()
        client = AsyncMock()
        client.post = AsyncMock(side_effect=Exception("network"))
        rm = RegistrationManager(client, config)
        with pytest.raises(Exception, match="network"):
            await rm.register(
                hostname="host", os_name="Linux",
                os_version="6.1", ip_address="10.0.0.1",
                agent_version="1.0.0",
            )
