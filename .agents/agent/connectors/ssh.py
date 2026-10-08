"""Mission Control Agent - SSH connector."""

import asyncio
import base64
import json
import logging
from typing import Any

from .base import RemoteConnector

logger = logging.getLogger("mc-agent")


class SSHConnector(RemoteConnector):
    """Connect to Linux targets via SSH using paramiko."""

    def __init__(self, target: dict[str, Any]):
        super().__init__(target)
        self._client = None

    def _get_client(self):
        import traceback

        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict[str, Any] = {
            "hostname": self.hostname,
            "port": self.port,
            "username": self.username,
            "timeout": 10,
            "allow_agent": False,
            "look_for_keys": False,
            "compress": False,
        }

        # Always prefer password auth when available.
        if self.password:
            connect_kwargs["password"] = self.password
        elif self.ssh_key:
            import io

            key_file = io.StringIO(self.ssh_key)
            try:
                connect_kwargs["pkey"] = paramiko.RSAKey.from_private_key(key_file)
            except Exception as exc:
                logger.warning(
                    "SSHConnector ignoring invalid RSA key for %s; no password available: %s",
                    self.hostname,
                    exc,
                )

        logger.info(
            "SSHConnector connecting to %s:%s as %s (password=%s key=%s)",
            self.hostname,
            self.port,
            self.username,
            "yes" if self.password else "no",
            "yes" if self.ssh_key else "no",
        )
        try:
            client.connect(**connect_kwargs)
            logger.info("SSHConnector connected to %s:%s", self.hostname, self.port)
        except Exception as exc:
            logger.error(
                "SSHConnector connect failed to %s:%s: %s\n%s",
                self.hostname,
                self.port,
                repr(exc),
                traceback.format_exc(),
            )
            client.close()
            raise
        return client

    async def _run_cmd(self, command: str, timeout: int = 30) -> dict:
        """Run a command on the remote host via SSH."""
        try:

            def _exec():
                client = self._get_client()
                try:
                    _, stdout, stderr = client.exec_command(command, timeout=timeout)
                    exit_code = stdout.channel.recv_exit_status()
                    out = stdout.read().decode(errors="replace")
                    err = stderr.read().decode(errors="replace")
                    return exit_code, out, err
                finally:
                    client.close()

            loop = asyncio.get_event_loop()
            exit_code, stdout, stderr = await asyncio.wait_for(
                loop.run_in_executor(None, _exec), timeout=timeout + 5
            )
            return {
                "success": exit_code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
            }
        except TimeoutError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": -1,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    async def test_connection(self) -> dict:
        result = await self._run_cmd("hostname", timeout=10)
        if result["success"]:
            return {
                "connected": True,
                "hostname": result["stdout"].strip(),
                "latency_ms": 0,
            }
        return {"connected": False, "error": result["stderr"], "latency_ms": 0}

    async def execute(self, command: str, timeout: int = 60) -> dict:
        return await self._run_cmd(command, timeout=timeout)

    async def collect_system_inventory(self) -> dict:
        script = (
            "echo '{'; "
            "echo '\"os\": {'; "
            "echo '  \"name\": \"'$(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')'\", '; "
            "echo '  \"kernel\": \"'$(uname -r)'\", '; "
            "echo '  \"arch\": \"'$(uname -m)'\", '; "
            "echo '  \"uptime\": \"'$(uptime -p 2>/dev/null || uptime)'\", '; "
            "echo '},'; "
            "echo '\"cpu\": {'; "
            "echo '  \"cores\": \"'$(nproc)'\", '; "
            'echo \'  "percent": "\'$(cat /proc/loadavg | awk "{print \\$1}")\'"\'; '
            "echo '},'; "
            "echo '\"memory\": {'; "
            "echo '  \"total_mb\": \"'$(free -m | awk '/Mem:/{print $2}')'\", '; "
            "echo '  \"used_mb\": \"'$(free -m | awk '/Mem:/{print $3}')'\", '; "
            "echo '  \"free_mb\": \"'$(free -m | awk '/Mem:/{print $4}')'\"'; "
            "echo '},'; "
            "echo '\"disks\": ['; "
            "df -h --output=source,size,used,avail,pcent,target 2>/dev/null | tail -n+2 | "
            'awk \'{printf "{\\"id\\":\\"%s\\",\\"size\\":\\"%s\\",\\"used\\":\\"%s\\",\\"free\\":\\"%s\\",\\"percent\\":\\"%s\\",\\"mount\\":\\"%s\\"},", $1,$2,$3,$4,$5,$6}\'; '
            "echo '],'; "
            "echo '\"network\": {'; "
            "echo '  \"interfaces\": ['; "
            'ip -4 addr show 2>/dev/null | awk \'/inet /{printf "{\\"iface\\":\\"%s\\",\\"ip\\":\\"%s\\"},", $NF, $2}\' | sed \'s/,$//\' ; '
            "echo '  ]'; "
            "echo '}'; "
            "echo '}'"
        )
        result = await self._run_cmd(f"bash -c '{script}'", timeout=15)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return {"raw": result["stdout"]}
        return {"error": result["stderr"]}

    async def collect_hyperv_inventory(self) -> dict | None:
        """Collect Hyper-V inventory via PowerShell over SSH (Windows hosts)."""
        script = (
            "if (Get-Command Get-VM -ErrorAction SilentlyContinue) { "
            "  $vms = Get-VM | Select-Object Name, State, CPUUsage, "
            "    MemoryAssigned, MemoryStartup, Uptime, Status, Generation, "
            "    VMId, ComputerName | ConvertTo-Json -Depth 3; "
            "  $sw = Get-VMSwitch | Select-Object Name, SwitchType | "
            "    ConvertTo-Json; "
            "  @{ vm_count=(Get-VM).Count; vms=$vms; switches=$sw } | "
            "  ConvertTo-Json -Depth 3 "
            "} else { 'null' }"
        )
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        result = await self._run_cmd(
            f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}",
            timeout=30,
        )
        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                if data and data.get("vm_count", 0) > 0:
                    vms_raw = data.get("vms", "[]")
                    switches_raw = data.get("switches", "[]")
                    vms = json.loads(vms_raw) if isinstance(vms_raw, str) else vms_raw
                    switches = (
                        json.loads(switches_raw)
                        if isinstance(switches_raw, str)
                        else switches_raw
                    )
                    if isinstance(vms, dict):
                        vms = [vms]
                    if isinstance(switches, dict):
                        switches = [switches]
                    return {
                        "vm_count": data["vm_count"],
                        "vms": [
                            {
                                "name": v.get("Name", ""),
                                "state": v.get("State", "Unknown"),
                                "cpu_usage": v.get("CPUUsage", 0),
                                "memory_mb": round(
                                    (v.get("MemoryAssigned") or 0) / (1024 * 1024), 0
                                ),
                                "memory_startup_mb": round(
                                    (v.get("MemoryStartup") or 0) / (1024 * 1024), 0
                                ),
                                "uptime": str(v.get("Uptime", "")),
                                "status": v.get("Status", ""),
                                "generation": v.get("Generation", 0),
                                "vm_id": v.get("VMId", ""),
                                "computer_name": v.get("ComputerName", ""),
                            }
                            for v in vms
                        ],
                        "switches": [
                            {"name": s.get("Name", ""), "type": s.get("SwitchType", "")}
                            for s in switches
                        ],
                    }
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    async def collect_proxmox_inventory(self) -> dict | None:
        """Collect Proxmox VE cluster data via pvesh CLI."""
        check = await self._run_cmd(
            "which pvesh 2>/dev/null && pvesh version 2>/dev/null", timeout=10
        )
        if not check["success"] or not check["stdout"].strip():
            return None

        nodes_result = await self._run_cmd(
            "pvesh get /nodes --output-format json 2>/dev/null || echo '[]'",
            timeout=15,
        )
        nodes = []
        if nodes_result["success"]:
            try:  # noqa: SIM105
                nodes = json.loads(nodes_result["stdout"])
            except (json.JSONDecodeError, TypeError):
                pass

        vms_result = await self._run_cmd(
            "pvesh get /cluster/resources --type vm --output-format json 2>/dev/null || echo '[]'",
            timeout=15,
        )
        vms = []
        if vms_result["success"]:
            try:  # noqa: SIM105
                vms = json.loads(vms_result["stdout"])
            except (json.JSONDecodeError, TypeError):
                pass

        lxc_result = await self._run_cmd(
            "pvesh get /cluster/resources --type lxc --output-format json 2>/dev/null || echo '[]'",
            timeout=15,
        )
        lxc = []
        if lxc_result["success"]:
            try:  # noqa: SIM105
                lxc = json.loads(lxc_result["stdout"])
            except (json.JSONDecodeError, TypeError):
                pass

        storage_result = await self._run_cmd(
            "pvesh get /cluster/resources --type storage --output-format json 2>/dev/null || echo '[]'",
            timeout=15,
        )
        storage = []
        if storage_result["success"]:
            try:  # noqa: SIM105
                storage = json.loads(storage_result["stdout"])
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "vm_count": len(vms),
            "lxc_count": len(lxc),
            "nodes": nodes,
            "vms": vms,
            "lxc": lxc,
            "storage": storage,
        }

    async def collect_services(self) -> list[dict]:
        script = (
            "systemctl list-units --type=service --state=running --no-pager --no-legend 2>/dev/null | "
            'awk \'{printf "{\\"name\\":\\"%s\\",\\"status\\":\\"running\\"}\\n", $1}\''
        )
        result = await self._run_cmd(script, timeout=10)
        if result["success"]:
            services = []
            for line in result["stdout"].strip().split("\n"):
                if line.strip():
                    try:  # noqa: SIM105
                        services.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return services
        return []

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
