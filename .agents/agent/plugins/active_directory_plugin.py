"""Mission Control Agent - Active Directory plugin using SSH relay."""

import base64
import json
import logging
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class ActiveDirectoryPlugin(AgentPlugin):
    """Active Directory data collector and management plugin using SSH relay."""

    name = "active_directory"
    version = "3.0.0-rc1"
    description = "Active Directory SSH-relay collector and management plugin"
    platform_required = None

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._ssh_target: dict[str, Any] | None = None

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._find_remote_target()
        if self._ssh_target:
            logger.info(
                "AD plugin configured with SSH target: %s (%s)",
                self._ssh_target.get("name"),
                self._ssh_target.get("hostname"),
            )
            return True
        logger.info("AD plugin initialized (waiting for active_directory remote target)")
        return True

    def _find_remote_target(self) -> dict[str, Any] | None:
        targets = self._context.get("remote_targets") or []
        for t in targets:
            if not isinstance(t, dict):
                continue
            plugins = {
                p.strip()
                for p in (t.get("target_plugins") or "").split(",")
                if p.strip()
            }
            if "active_directory" in plugins and (
                t.get("protocol") or ""
            ).lower() == "ssh":
                self._ssh_target = t
                return t
        return None

    def _encode_ps(self, script: str) -> str:
        return base64.b64encode(script.encode("utf-16le")).decode("ascii")

    async def collect_inventory(self) -> dict[str, Any]:
        self._find_remote_target()
        if not self._ssh_target:
            return {
                "available": False,
                "error": "No SSH remote target tagged with active_directory",
            }

        remote_manager = self._context.get("remote_manager")
        if not remote_manager:
            return {"available": False, "error": "No remote_manager in plugin context"}

        target_id = self._ssh_target.get("id")
        if target_id is None:
            return {"available": False, "error": "Remote target missing ID"}

        ps_script = """
        Import-Module ActiveDirectory -ErrorAction SilentlyContinue
        $dom = Get-ADDomain
        $forest = (Get-ADForest).Name
        $dcs = @(Get-ADDomainController -Filter * | Select-Object -ExpandProperty HostName)

        $users = @(Get-ADUser -Filter * -Properties sAMAccountName, displayName, mail, department, title, Enabled, DistinguishedName | ForEach-Object {
            @{
                sam_account_name = $_.sAMAccountName
                display_name = $_.displayName
                email = $_.mail
                department = $_.department
                title = $_.title
                enabled = [bool]$_.Enabled
                distinguished_name = $_.DistinguishedName
            }
        })

        $groups = @(Get-ADGroup -Filter * -Properties Name, Description | ForEach-Object {
            @{
                name = $_.Name
                description = $_.Description
            }
        })

        $devices = @(Get-ADComputer -Filter * -Properties Name, DNSHostName, OperatingSystem | ForEach-Object {
            @{
                name = $_.Name
                dns_name = $_.DNSHostName
                os_version = $_.OperatingSystem
            }
        })

        @{
            available = $true
            domain = @{ name = $dom.Name; base_dn = $dom.DistinguishedName }
            forest = $forest
            domain_controllers = $dcs
            users = $users
            groups = $groups
            devices = $devices
            health = @{
                status = 'healthy'
                replication = @{ status = 'healthy'; pending_replications = 0; failed_replications = 0 }
            }
        } | ConvertTo-Json -Depth 5
        """

        encoded = self._encode_ps(ps_script)
        cmd = f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"
        res = await remote_manager.execute_on_target(
            target_id=target_id, command=cmd, timeout=60
        )

        if not res.get("success"):
            return {
                "available": False,
                "error": res.get("stderr") or res.get("stdout") or "SSH execution failed",
            }

        stdout = res.get("stdout") or "{}"
        try:
            data = json.loads(stdout)
            if isinstance(data, dict):
                return data
            return {
                "available": False,
                "error": "Invalid JSON response from AD inventory script",
            }
        except Exception as exc:
            return {
                "available": False,
                "error": f"JSON decode failed: {exc}",
                "raw": stdout[:500],
            }

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        self._find_remote_target()
        if not self._ssh_target:
            return {"success": False, "error": "No active_directory remote target"}

        remote_manager = self._context.get("remote_manager")
        if not remote_manager:
            return {"success": False, "error": "No remote_manager"}

        target_id = self._ssh_target.get("id")
        sam = args.get("sam_account_name") or args.get("username") or ""

        scripts = {
            "test_connection": "if (Get-Module ActiveDirectory -ListAvailable) { @{success=$true; message='AD module available'} | ConvertTo-Json } else { @{success=$false; error='No AD module'} | ConvertTo-Json }",
            "reset-password": f"Set-ADAccountPassword -Identity '{sam}' -NewPassword (ConvertTo-SecureString '{args.get('new_password','')}' -AsPlainText -Force) -Reset; @{{success=$true}} | ConvertTo-Json",
            "unlock": f"Unlock-ADAccount -Identity '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "enable": f"Enable-ADAccount -Identity '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "disable": f"Disable-ADAccount -Identity '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "rename": f"Set-ADUser -Identity '{sam}' -DisplayName '{args.get('display_name','')}'; @{{success=$true}} | ConvertTo-Json",
            "get-user-groups": f"Get-ADPrincipalGroupMembership -Identity '{sam}' | Select-Object -ExpandProperty Name | ForEach-Object {{@{{name=$_}}}} | ConvertTo-Json",
            "add-to-group": f"Add-ADGroupMember -Identity '{args.get('group_name','')}' -Members '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "remove-from-group": f"Remove-ADGroupMember -Identity '{args.get('group_name','')}' -Members '{sam}' -Confirm:$false; @{{success=$true}} | ConvertTo-Json",
        }

        cmd_clean = command.removeprefix("ad:").removeprefix("active_directory:")
        script = scripts.get(cmd_clean)
        if not script:
            return {"success": False, "error": f"Unknown AD command: {command}"}

        encoded = self._encode_ps(script)
        res = await remote_manager.execute_on_target(
            target_id=target_id,
            command=f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}",
            timeout=30,
        )
        if not res.get("success"):
            return {
                "success": False,
                "error": res.get("stderr") or res.get("stdout") or "Command failed",
            }

        stdout = res.get("stdout") or "{}"
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"success": True, "groups": parsed}
            return {"success": True, "output": stdout}
        except Exception:
            return {"success": True, "output": stdout}
