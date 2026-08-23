"""Agent-side Veeam relay tests (self-contained, no full agent runtime).

Pins the Task-6 provider payload keys and the Task-5 namespace routing /
backward-compat target fallback that the backend provider and Jobs screen
depend on. Importing the plugin module needs only stdlib plus the
``agent.plugin`` base class (no optional deps are imported at module scope),
so this runs without the full agent runtime or a Veeam PowerShell module.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

_AGENTS_ROOT = Path(__file__).resolve().parents[1]
if str(_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENTS_ROOT))

from agent.plugins.veeam_plugin import VeeamPlugin  # noqa: E402


def _make_plugin() -> VeeamPlugin:
    plugin = VeeamPlugin()
    plugin._api_base = "https://192.168.10.49:9419"
    plugin._username = "kg\\administrator"
    plugin._use_relay = True
    return plugin


class TestRelayPayloadKeys:
    """Pin the provider-correct payload keys from _execute_relay (Task 6)."""

    async def _dispatch(self, op, args=None, collector_result=None):
        plugin = _make_plugin()
        plugin._run_collector_via_relay = AsyncMock(return_value=collector_result)
        return await plugin._execute_relay(op, args or {})

    def test_jobs_key(self):
        result = asyncio.run(
            self._dispatch("veeam:jobs", collector_result=[{"id": "j1"}])
        )
        assert result["success"] is True
        assert result["jobs"] == [{"id": "j1"}]
        assert result["count"] == 1

    def test_sessions_key(self):
        result = asyncio.run(
            self._dispatch("veeam:sessions", collector_result=[{"id": "s1"}])
        )
        assert result["success"] is True
        assert result["sessions"] == [{"id": "s1"}]
        assert result["count"] == 1

    def test_repositories_key(self):
        result = asyncio.run(
            self._dispatch("veeam:repositories", collector_result=[{"id": "r1"}])
        )
        assert result["success"] is True
        assert result["repositories"] == [{"id": "r1"}]

    def test_managed_servers_maps_to_servers_key(self):
        result = asyncio.run(
            self._dispatch("veeam:managed_servers", collector_result=[{"id": "m1"}])
        )
        assert result["success"] is True
        assert result["servers"] == [{"id": "m1"}]
        assert "managed_servers" not in result

    def test_restore_points_key(self):
        result = asyncio.run(
            self._dispatch("veeam:restore_points", collector_result=[{"id": "rp1"}])
        )
        assert result["success"] is True
        assert result["restore_points"] == [{"id": "rp1"}]

    def test_license_key(self):
        result = asyncio.run(
            self._dispatch("veeam:license", collector_result={"edition": "Enterprise"})
        )
        assert result["success"] is True
        assert result["license"] == {"edition": "Enterprise"}

    def test_session_stats_key(self):
        result = asyncio.run(self._dispatch("veeam:session_stats"))
        assert result["stats"] == []
        assert result["count"] == 0

    def test_job_stats_daily_keys(self):
        result = asyncio.run(self._dispatch("veeam:job_stats_daily"))
        assert result["jobs"] == []
        assert result["dates"] == []
        assert result["count"] == 0

    def test_capacity_tier_key(self):
        result = asyncio.run(self._dispatch("veeam:capacity_tier"))
        assert result["object_storages"] == []
        assert result["count"] == 0

    def test_collector_failure_returns_error(self):
        result = asyncio.run(self._dispatch("veeam:jobs", collector_result=None))
        assert result["success"] is False
        assert result["jobs"] == []
        assert result["error"] is not None


class TestRelayTargetRouting:
    """Pin the Task-5 routing: dispatched target_id is threaded through."""

    def test_execute_relay_threads_target_id_to_collector(self):
        plugin = _make_plugin()
        calls = []

        async def fake_collector(collector, target_id=None):
            calls.append((collector, target_id))
            return []

        plugin._run_collector_via_relay = fake_collector
        asyncio.run(plugin._execute_relay("veeam:jobs", {"target_id": 7}))
        assert calls == [("jobs", 7)]

    def test_execute_relay_no_target_id_keeps_none(self):
        plugin = _make_plugin()
        calls = []

        async def fake_collector(collector, target_id=None):
            calls.append((collector, target_id))
            return []

        plugin._run_collector_via_relay = fake_collector
        asyncio.run(plugin._execute_relay("veeam:jobs", {}))
        assert calls == [("jobs", None)]

    def test_start_job_threads_target_id_to_script(self):
        plugin = _make_plugin()
        calls = []

        async def fake_script(script, timeout=60, target_id=None):
            calls.append(target_id)
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        plugin._run_script_via_relay = fake_script
        result = asyncio.run(
            plugin._execute_relay("start_job", {"job_id": "j1", "target_id": 9})
        )
        assert calls == [9]
        assert result["success"] is True

    def test_stop_job_threads_target_id_to_script(self):
        plugin = _make_plugin()
        calls = []

        async def fake_script(script, timeout=60, target_id=None):
            calls.append(target_id)
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        plugin._run_script_via_relay = fake_script
        result = asyncio.run(
            plugin._execute_relay("stop_job", {"job_id": "j1", "target_id": 12})
        )
        assert calls == [12]
        assert result["success"] is True


class TestScriptRelayBackwardCompat:
    """Pin the existing single-target fallback in _run_script_via_relay."""

    def _plugin_with_targets(self, targets):
        plugin = _make_plugin()
        remote_manager = MagicMock()
        remote_manager.targets = targets
        remote_manager.execute_on_target = AsyncMock(
            return_value={
                "success": True,
                "stdout": "{}",
                "stderr": "",
                "exit_code": 0,
            }
        )
        plugin._context["remote_manager"] = remote_manager
        return plugin, remote_manager

    def test_prefers_dispatched_target_id(self):
        plugin, rm = self._plugin_with_targets(
            {
                11: {"hostname": "192.168.10.49", "protocol": "ssh"},
                22: {"hostname": "10.0.0.9", "protocol": "ssh"},
            }
        )
        result = asyncio.run(
            plugin._run_script_via_relay("script", timeout=60, target_id=22)
        )
        assert result["success"] is True
        assert rm.execute_on_target.await_args.kwargs["target_id"] == 22

    def test_falls_back_to_api_base_hostname_when_no_target_id(self):
        plugin, rm = self._plugin_with_targets(
            {
                11: {"hostname": "192.168.10.49", "protocol": "ssh"},
                22: {"hostname": "10.0.0.9", "protocol": "ssh"},
            }
        )
        result = asyncio.run(plugin._run_script_via_relay("script", timeout=60))
        assert result["success"] is True
        assert rm.execute_on_target.await_args.kwargs["target_id"] == 11

    def test_falls_back_to_hostname_when_target_id_unknown(self):
        plugin, rm = self._plugin_with_targets(
            {
                11: {"hostname": "192.168.10.49", "protocol": "ssh"},
            }
        )
        result = asyncio.run(
            plugin._run_script_via_relay("script", timeout=60, target_id=999)
        )
        assert result["success"] is True
        assert rm.execute_on_target.await_args.kwargs["target_id"] == 11

    def test_non_ssh_dispatched_target_falls_back_to_hostname(self):
        plugin, rm = self._plugin_with_targets(
            {
                11: {"hostname": "192.168.10.49", "protocol": "ssh"},
                22: {"hostname": "10.0.0.9", "protocol": "winrm"},
            }
        )
        result = asyncio.run(
            plugin._run_script_via_relay("script", timeout=60, target_id=22)
        )
        assert result["success"] is True
        assert rm.execute_on_target.await_args.kwargs["target_id"] == 11

    def test_no_matching_target_returns_error(self):
        plugin, _rm = self._plugin_with_targets(
            {
                22: {"hostname": "10.0.0.9", "protocol": "ssh"},
            }
        )
        result = asyncio.run(plugin._run_script_via_relay("script", timeout=60))
        assert result["success"] is False
        assert "no ssh target" in result["stderr"]
