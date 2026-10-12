"""
Mission Control Hyper-V Replication — shared query and response builder.

The same PowerShell query is executed two ways:
  - directly over WinRM/SSH by HyperVPowerShellProvider, or
  - through the agent command queue by the agent-backed providers.
Every provider funnels the raw exec result through
``replication_from_result`` so the router always receives a
HyperVReplicationResponse-shaped dict — never an AttributeError.
"""

from __future__ import annotations

import base64
import json
import re

# Array-safe: @() keeps a single replication item a real array so
# ConvertTo-Json emits a list, not a bare object.  -Depth 4 covers the
# hashtable -> items -> PSCustomObject nesting.
REPLICATION_SCRIPT = (
    "$repl = @(Get-VMReplication -ErrorAction SilentlyContinue | Where-Object { $null -ne $_ }); "
    "if ($repl.Count -eq 0) { "
    "Write-Output (@{connected=$true;replicating=0;total=0;items=@()} | ConvertTo-Json -Compress); "
    "return } "
    "$items = @($repl | ForEach-Object { "
    "$health = 'Unknown'; "
    "try { $h = $_.ReplicationHealth; if ($null -ne $h) { $health = $h.ToString() } } catch {} "
    "$state = 'Unknown'; "
    "try { $s = $_.State; if ($null -ne $s) { $state = $s.ToString() } } catch {} "
    "$freq = 0; "
    "try { $f = $_.ReplicationFrequencySec; if ($null -ne $f) { $freq = $f } } catch {} "
    "$lastTime = ''; "
    "try { $t = $_.LastReplicationTime; if ($null -ne $t) { $lastTime = $t.ToString('yyyy-MM-dd HH:mm:ss') } } catch {} "
    "$resultCode = 0; "
    "try { $rc = $_.LastReplicationResultCode; if ($null -ne $rc) { $resultCode = $rc } } catch {} "
    "$bytesSent = 0; "
    "try { $bs = $_.ReplicationBytesSent; if ($null -ne $bs) { $bytesSent = $bs } } catch {} "
    "$bytesReceived = 0; "
    "try { $br = $_.ReplicationBytesReceived; if ($null -ne $br) { $bytesReceived = $br } } catch {} "
    "[PSCustomObject]@{ "
    "VMName=$_.VMName; "
    "ReplicaServer=$_.ReplicaServer; "
    "ReplicaServerPort=$_.ReplicaServerPort; "
    "State=$state; "
    "Health=$health; "
    "ReplicationFrequencySec=$freq; "
    "LastReplicationTime=$lastTime; "
    "LastReplicationResultCode=$resultCode; "
    "ReplicationBytesSent=$bytesSent; "
    "ReplicationBytesReceived=$bytesReceived; "
    "} "
    "}); "
    "$replicating = @($repl | Where-Object { $_.State -eq 'Replicating' }).Count; "
    "Write-Output (@{connected=$true;replicating=$replicating;total=$repl.Count;items=$items} "
    "| ConvertTo-Json -Depth 4 -Compress)"
)

_EMPTY_RESPONSE: dict = {
    "connected": False,
    "replicating": 0,
    "total": 0,
    "items": [],
}


def powershell_relay_command(script: str = REPLICATION_SCRIPT) -> str:
    """Wrap a PowerShell script for relay to a remote Windows target.

    Remote targets are reached through the agent's ``ssh`` connector, so the
    command lands in the target's login shell.  A Windows OpenSSH default
    shell is ``cmd.exe``, which would try to run ``$repl = ...`` as a program.
    The UTF-16LE ``-EncodedCommand`` form is shell-agnostic (the same pattern
    the Veeam relay executor uses for SQLCMD).
    """
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return f"powershell.exe -NoProfile -NonInteractive -EncodedCommand {encoded}"


def _extract_json(stdout: str) -> dict | list | None:
    """Extract the first JSON document from PowerShell output."""
    text = (stdout or "").strip()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _to_int(value, default: int = 0) -> int:
    """Coerce PowerShell output (None, floats, numeric strings) to int."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+", value)
        if match:
            return int(match.group())
    return default


def _to_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def replication_from_result(result: dict) -> dict:
    """Build a HyperVReplicationResponse-shaped dict from an exec result.

    ``result`` is ``{"success": bool, "stdout": str, "stderr": str}`` —
    the shape returned by both the WinRM/SSH exec helpers and the agent
    command-queue wait helper.  Never raises: bad output degrades to an
    empty (but schema-valid) response.
    """
    if not result.get("success"):
        error = result.get("stderr") or result.get("error") or "Hyper-V replication query failed"
        return {**_EMPTY_RESPONSE, "error": error}

    data = _extract_json(result.get("stdout") or "")
    if not isinstance(data, dict):
        # No replication configured, or unparseable output: show an empty
        # state instead of erroring the page.
        return {"connected": True, "replicating": 0, "total": 0, "items": []}

    raw_items = data.get("items") or []
    if isinstance(raw_items, dict):
        # PowerShell collapses a single-element array to a bare object.
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        raw_items = []

    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        last_time = _to_str(raw.get("LastReplicationTime"))
        items.append({
            "vm_name": _to_str(raw.get("VMName")),
            "replica_server": _to_str(raw.get("ReplicaServer")),
            "replica_port": _to_int(raw.get("ReplicaServerPort"), 443),
            "state": _to_str(raw.get("State"), "Unknown"),
            "health": _to_str(raw.get("Health"), "Unknown"),
            "frequency_seconds": _to_int(raw.get("ReplicationFrequencySec")),
            "last_replication_time": last_time or None,
            "last_result_code": _to_int(raw.get("LastReplicationResultCode")),
            "bytes_sent": _to_int(raw.get("ReplicationBytesSent")),
            "bytes_received": _to_int(raw.get("ReplicationBytesReceived")),
        })

    return {
        "connected": bool(data.get("connected", True)),
        "replicating": _to_int(data.get("replicating")),
        "total": _to_int(data.get("total"), len(items)),
        "items": items,
    }
