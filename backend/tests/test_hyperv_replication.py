"""
Mission Control Hyper-V Replication Tests

Covers the shared replication query/result builder and every provider
that serves GET /hyperv/replication.  Regression test for the 500 caused
by AgentHyperVProvider missing get_replication (EVPDC02).
"""

import base64

import pytest

from app.providers.hyperv.agent_provider import AgentHyperVProvider
from app.providers.hyperv.base_provider import HyperVProvider
from app.providers.hyperv.local_agent_provider import LocalAgentHyperVProvider
from app.providers.hyperv.mock_provider import MockHyperVProvider
from app.providers.hyperv.replication import (
    REPLICATION_SCRIPT,
    powershell_relay_command,
    replication_from_result,
)
from app.schemas.hyperv import HyperVReplicationResponse


def _stdout(payload: str) -> dict:
    return {"success": True, "stdout": payload, "stderr": ""}


# ------------------------------------------------------------------ #
# PowerShell script                                                   #
# ------------------------------------------------------------------ #


class TestReplicationScript:
    def test_script_is_single_line(self) -> None:
        assert "\n" not in REPLICATION_SCRIPT

    def test_script_wraps_collections_in_array_subexpression(self) -> None:
        # Without @(), PowerShell collapses a single replication item to a
        # bare object and ConvertTo-Json emits a dict instead of a list.
        assert "@($repl | ForEach-Object" in REPLICATION_SCRIPT
        assert "@($repl | Where-Object" in REPLICATION_SCRIPT
        assert "$repl = @(" in REPLICATION_SCRIPT

    def test_script_uses_sufficient_json_depth(self) -> None:
        assert "-Depth 4" in REPLICATION_SCRIPT

    def test_script_has_no_double_quotes(self) -> None:
        # The command is relayed verbatim through the agent command queue;
        # single quotes only, matching the existing VM action scripts.
        assert '"' not in REPLICATION_SCRIPT

    def test_relay_command_is_encoded_single_arg(self) -> None:
        # A Windows target reached over the agent's ssh connector lands in
        # cmd.exe, so the script must be sent as -EncodedCommand.
        cmd = powershell_relay_command()
        assert cmd.startswith("powershell.exe -NoProfile -NonInteractive -EncodedCommand ")
        assert "\n" not in cmd and '"' not in cmd
        encoded = cmd.rsplit(" ", 1)[1]
        assert base64.b64decode(encoded).decode("utf-16-le") == REPLICATION_SCRIPT


# ------------------------------------------------------------------ #
# Result parsing                                                      #
# ------------------------------------------------------------------ #


class TestReplicationFromResult:
    def test_failed_result_returns_error(self) -> None:
        resp = replication_from_result(
            {"success": False, "stdout": "", "stderr": "boom"}
        )
        assert resp["connected"] is False
        assert resp["error"] == "boom"
        assert resp["items"] == []
        HyperVReplicationResponse(**resp)

    def test_failed_result_uses_error_key_when_no_stderr(self) -> None:
        resp = replication_from_result({"success": False, "stdout": ""})
        assert resp["connected"] is False
        assert resp["error"]
        HyperVReplicationResponse(**resp)

    def test_unparseable_stdout_returns_empty(self) -> None:
        resp = replication_from_result(_stdout("not json at all"))
        assert resp["connected"] is True
        assert resp["items"] == []
        assert resp["replicating"] == 0
        HyperVReplicationResponse(**resp)

    def test_empty_stdout_returns_empty(self) -> None:
        resp = replication_from_result(_stdout(""))
        assert resp["connected"] is True
        assert resp["items"] == []
        HyperVReplicationResponse(**resp)

    def test_no_replication_configured(self) -> None:
        resp = replication_from_result(
            _stdout('{"connected":true,"replicating":0,"total":0,"items":[]}')
        )
        assert resp["connected"] is True
        assert resp["total"] == 0
        assert resp["items"] == []
        HyperVReplicationResponse(**resp)

    def test_multiple_items_mapped(self) -> None:
        stdout = (
            '{"connected":true,"replicating":1,"total":2,"items":['
            '{"VMName":"EVP-APP01","ReplicaServer":"EVPDC02","ReplicaServerPort":443,'
            '"State":"Replicating","Health":"Ok","ReplicationFrequencySec":30,'
            '"LastReplicationTime":"2026-10-08 10:00:00","LastReplicationResultCode":0,'
            '"ReplicationBytesSent":1024,"ReplicationBytesReceived":2048},'
            '{"VMName":"EVP-DB01","ReplicaServer":"EVPDC02","ReplicaServerPort":443,'
            '"State":"Critical","Health":"Critical","ReplicationFrequencySec":300,'
            '"LastReplicationTime":"2026-10-08 09:00:00","LastReplicationResultCode":12,'
            '"ReplicationBytesSent":0,"ReplicationBytesReceived":0}'
            "]}"
        )
        resp = replication_from_result(_stdout(stdout))
        assert resp["connected"] is True
        assert resp["replicating"] == 1
        assert resp["total"] == 2
        assert len(resp["items"]) == 2
        first = resp["items"][0]
        assert first["vm_name"] == "EVP-APP01"
        assert first["replica_server"] == "EVPDC02"
        assert first["state"] == "Replicating"
        assert first["health"] == "Ok"
        assert first["frequency_seconds"] == 30
        assert first["last_result_code"] == 0
        assert resp["items"][1]["health"] == "Critical"
        HyperVReplicationResponse(**resp)

    def test_single_item_collapsed_to_dict_still_yields_list(self) -> None:
        # Legacy/edge PowerShell output: one item serialized as a bare object.
        stdout = (
            '{"connected":true,"replicating":1,"total":1,'
            '"items":{"VMName":"EVP-APP01","ReplicaServer":"EVPDC02",'
            '"ReplicaServerPort":443,"State":"Replicating","Health":"Ok",'
            '"ReplicationFrequencySec":30,"LastReplicationTime":"2026-10-08 10:00:00",'
            '"LastReplicationResultCode":0,"ReplicationBytesSent":1,'
            '"ReplicationBytesReceived":2}}'
        )
        resp = replication_from_result(_stdout(stdout))
        assert isinstance(resp["items"], list)
        assert len(resp["items"]) == 1
        assert resp["items"][0]["vm_name"] == "EVP-APP01"
        HyperVReplicationResponse(**resp)

    def test_null_fields_are_coerced(self) -> None:
        # PowerShell emits nulls for not-yet-synced replicas; Pydantic int/str
        # fields reject None, which previously produced a 500.
        stdout = (
            '{"connected":true,"replicating":1,"total":1,"items":['
            '{"VMName":"EVP-APP01","ReplicaServer":null,"ReplicaServerPort":null,'
            '"State":"Replicating","Health":"Ok","ReplicationFrequencySec":null,'
            '"LastReplicationTime":null,"LastReplicationResultCode":null,'
            '"ReplicationBytesSent":null,"ReplicationBytesReceived":null}]}'
        )
        resp = replication_from_result(_stdout(stdout))
        item = resp["items"][0]
        assert item["replica_server"] == ""
        assert item["replica_port"] == 443
        assert item["frequency_seconds"] == 0
        assert item["last_replication_time"] is None
        assert item["last_result_code"] == 0
        HyperVReplicationResponse(**resp)

    def test_numeric_strings_coerced(self) -> None:
        stdout = (
            '{"connected":true,"replicating":"1","total":"2","items":['
            '{"VMName":"VM1","ReplicaServer":"R1","ReplicaServerPort":"443",'
            '"State":"Replicating","Health":"Ok","ReplicationFrequencySec":"30",'
            '"LastReplicationTime":"2026-10-08 10:00:00",'
            '"LastReplicationResultCode":"0","ReplicationBytesSent":"1024",'
            '"ReplicationBytesReceived":"2048"}]}'
        )
        resp = replication_from_result(_stdout(stdout))
        assert resp["replicating"] == 1
        assert resp["total"] == 2
        assert resp["items"][0]["replica_port"] == 443
        assert resp["items"][0]["bytes_sent"] == 1024
        HyperVReplicationResponse(**resp)

    def test_non_dict_items_ignored(self) -> None:
        stdout = '{"connected":true,"replicating":0,"total":1,"items":["oops"]}'
        resp = replication_from_result(_stdout(stdout))
        assert resp["items"] == []
        HyperVReplicationResponse(**resp)


# ------------------------------------------------------------------ #
# Provider implementations                                            #
# ------------------------------------------------------------------ #


def _fake_dispatch_ok(stdout: str):
    async def dispatch(command_str: str) -> dict:
        return {"success": True, "command_id": 42}

    async def wait(command_id: int) -> dict:
        return {"success": True, "state": None, "stdout": stdout, "stderr": ""}

    return dispatch, wait


_AGENT_STDOUT = (
    '{"connected":true,"replicating":1,"total":1,"items":['
    '{"VMName":"EVP-APP01","ReplicaServer":"EVPDC02","ReplicaServerPort":443,'
    '"State":"Replicating","Health":"Ok","ReplicationFrequencySec":30,'
    '"LastReplicationTime":"2026-10-08 10:00:00","LastReplicationResultCode":0,'
    '"ReplicationBytesSent":1024,"ReplicationBytesReceived":2048}]}'
)


class TestAgentProviderReplication:
    @pytest.mark.asyncio
    async def test_returns_live_replication_data(self) -> None:
        dispatch, wait = _fake_dispatch_ok(_AGENT_STDOUT)
        provider = AgentHyperVProvider(
            {"vms": []},
            target_hostname="EVPDC02",
            dispatch_cmd=dispatch,
            wait_cmd=wait,
        )
        resp = await provider.get_replication()
        assert resp["connected"] is True
        assert resp["replicating"] == 1
        assert len(resp["items"]) == 1
        assert resp["items"][0]["vm_name"] == "EVP-APP01"
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_dispatches_shared_script(self) -> None:
        seen: list[str] = []

        async def dispatch(command_str: str) -> dict:
            seen.append(command_str)
            return {"success": True, "command_id": 7}

        async def wait(command_id: int) -> dict:
            return {"success": True, "state": None, "stdout": _AGENT_STDOUT, "stderr": ""}

        provider = AgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=wait
        )
        await provider.get_replication()
        assert seen == [powershell_relay_command()]
        assert seen[0] != REPLICATION_SCRIPT

    @pytest.mark.asyncio
    async def test_no_dispatch_returns_error_not_raise(self) -> None:
        provider = AgentHyperVProvider({"vms": []})
        resp = await provider.get_replication()
        assert resp["connected"] is False
        assert resp["error"]
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_failed_command_returns_error_not_raise(self) -> None:
        async def dispatch(command_str: str) -> dict:
            return {"success": True, "command_id": 1}

        async def wait(command_id: int) -> dict:
            return {"success": False, "stdout": "", "stderr": "target offline"}

        provider = AgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=wait
        )
        resp = await provider.get_replication()
        assert resp["connected"] is False
        assert resp["error"] == "target offline"
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_dispatch_failure_propagates(self) -> None:
        async def dispatch(command_str: str) -> dict:
            return {"success": False, "error": "Agent is offline"}

        provider = AgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=None
        )
        resp = await provider.get_replication()
        assert resp["connected"] is False
        assert "Agent is offline" in resp["error"]
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_sync_dispatch_lambda_supported(self) -> None:
        # provider_factory / hyperv_service fallbacks pass a *sync* lambda
        # returning a dict; awaiting it directly raised TypeError
        # ("object dict can't be used in 'await' expression").
        provider = AgentHyperVProvider(
            {"vms": []},
            target_id=2,
            dispatch_cmd=lambda command_str: {"success": False, "error": "Agent offline for commands"},
        )
        resp = await provider.get_replication()
        assert resp["connected"] is False
        assert "Agent offline for commands" in resp["error"]
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_sync_wait_lambda_supported(self) -> None:
        provider = AgentHyperVProvider(
            {"vms": []},
            dispatch_cmd=lambda command_str: {"success": True, "command_id": 7},
            wait_cmd=lambda command_id: {"success": False, "stdout": "", "stderr": "sync wait result"},
        )
        resp = await provider.get_replication()
        assert resp["connected"] is False
        assert resp["error"] == "sync wait result"
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_restart_vm_dispatches_encoded_command(self) -> None:
        # VM actions over the relay path hit cmd.exe just like the query —
        # the restart button must ship an -EncodedCommand too.
        seen: list[str] = []

        async def dispatch(command_str: str) -> dict:
            seen.append(command_str)
            return {"success": True, "command_id": 11}

        async def wait(command_id: int) -> dict:
            return {"success": True, "state": "Running", "stdout": "MC_STATE=Running", "stderr": ""}

        provider = AgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=wait
        )
        resp = await provider.restart_vm("EVP-APP01")
        assert resp["success"] is True
        assert len(seen) == 1
        assert seen[0].startswith("powershell.exe -NoProfile -NonInteractive -EncodedCommand ")
        decoded = base64.b64decode(seen[0].rsplit(" ", 1)[1]).decode("utf-16-le")
        assert "Restart-VM -Name 'EVP-APP01' -Force" in decoded
        assert "MC_STATE=" in decoded

    @pytest.mark.asyncio
    async def test_stop_vm_dispatches_encoded_command(self) -> None:
        seen: list[str] = []

        async def dispatch(command_str: str) -> dict:
            seen.append(command_str)
            return {"success": True, "command_id": 12}

        async def wait(command_id: int) -> dict:
            return {"success": True, "state": "Off", "stdout": "MC_STATE=Off", "stderr": ""}

        provider = AgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=wait
        )
        resp = await provider.stop_vm("EVP-APP01", force=True)
        assert resp["success"] is True
        decoded = base64.b64decode(seen[0].rsplit(" ", 1)[1]).decode("utf-16-le")
        assert "Stop-VM -Name 'EVP-APP01' -Force" in decoded


class TestLocalAgentProviderReplication:
    @pytest.mark.asyncio
    async def test_returns_live_replication_data(self) -> None:
        dispatch, wait = _fake_dispatch_ok(_AGENT_STDOUT)
        provider = LocalAgentHyperVProvider(
            {"vms": []}, hostname="EVPDC02", dispatch_cmd=dispatch, wait_cmd=wait
        )
        resp = await provider.get_replication()
        assert resp["connected"] is True
        assert resp["replicating"] == 1
        assert len(resp["items"]) == 1
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_no_dispatch_returns_error_not_raise(self) -> None:
        provider = LocalAgentHyperVProvider({"vms": []})
        resp = await provider.get_replication()
        assert resp["connected"] is False
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_dispatches_raw_script_for_local_executor(self) -> None:
        # The local agent runs commands through "powershell -Command", so the
        # script is sent raw here — not the -EncodedCommand relay wrapper.
        seen: list[str] = []

        async def dispatch(command_str: str) -> dict:
            seen.append(command_str)
            return {"success": True, "command_id": 5}

        async def wait(command_id: int) -> dict:
            return {"success": True, "state": None, "stdout": _AGENT_STDOUT, "stderr": ""}

        provider = LocalAgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=wait
        )
        await provider.get_replication()
        assert seen == [REPLICATION_SCRIPT]

    @pytest.mark.asyncio
    async def test_restart_vm_dispatches_raw_command(self) -> None:
        seen: list[str] = []

        async def dispatch(command_str: str) -> dict:
            seen.append(command_str)
            return {"success": True, "command_id": 13}

        async def wait(command_id: int) -> dict:
            return {"success": True, "state": "Running", "stdout": "MC_STATE=Running", "stderr": ""}

        provider = LocalAgentHyperVProvider(
            {"vms": []}, dispatch_cmd=dispatch, wait_cmd=wait
        )
        resp = await provider.restart_vm("EVP-APP01")
        assert resp["success"] is True
        assert seen[0].startswith("$ErrorActionPreference='Stop';")
        assert "-EncodedCommand" not in seen[0]
        assert "Restart-VM -Name 'EVP-APP01' -Force" in seen[0]

    @pytest.mark.asyncio
    async def test_sync_dispatch_lambda_supported(self) -> None:
        provider = LocalAgentHyperVProvider(
            {"vms": []},
            dispatch_cmd=lambda command_str: {"success": False, "error": "Agent offline for commands"},
        )
        resp = await provider.get_replication()
        assert resp["connected"] is False
        assert "Agent offline for commands" in resp["error"]
        HyperVReplicationResponse(**resp)


class TestOtherProvidersReplication:
    @pytest.mark.asyncio
    async def test_mock_provider_returns_schema_valid_empty(self) -> None:
        # MockHyperVProvider inherits the base default; this is the exact
        # AttributeError regression (endpoint returned 500).
        resp = await MockHyperVProvider().get_replication()
        assert resp["replicating"] == 0
        assert resp["items"] == []
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_base_default_is_schema_valid(self) -> None:
        class _Minimal(HyperVProvider):
            async def get_checkpoints(self, vm_id=None):
                return {}

            async def create_checkpoint(self, vm_id, name=None):
                return {}

            async def delete_checkpoint(self, vm_id, checkpoint_id):
                return {}

            async def test_connection(self):
                return {}

            async def get_summary(self):
                return {}

            async def get_vms(self):
                return {}

            async def get_vm_detail(self, vm_id):
                return {}

            async def get_networks(self):
                return {}

            async def get_storage(self):
                return {}

            async def get_snapshots(self, vm_id=None):
                return {}

            async def get_health(self):
                return {}

            async def start_vm(self, vm_id):
                return {}

            async def stop_vm(self, vm_id, force=False):
                return {}

            async def restart_vm(self, vm_id):
                return {}

            async def pause_vm(self, vm_id):
                return {}

            async def resume_vm(self, vm_id):
                return {}

            async def create_snapshot(self, vm_id, name=None):
                return {}

            async def delete_snapshot(self, vm_id, snapshot_id):
                return {}

        resp = await _Minimal().get_replication()
        assert resp["connected"] is False
        HyperVReplicationResponse(**resp)

    @pytest.mark.asyncio
    async def test_every_provider_serves_get_replication(self) -> None:
        # The router must never hit an AttributeError for any provider.
        providers = [
            MockHyperVProvider(),
            AgentHyperVProvider({"vms": []}),
            LocalAgentHyperVProvider({"vms": []}),
        ]
        for provider in providers:
            resp = await provider.get_replication()
            HyperVReplicationResponse(**resp)
