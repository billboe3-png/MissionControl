"""Mission Control Agent - Active Directory plugin using SSH relay."""

import base64
import json
import logging
import re
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class ActiveDirectoryPlugin(AgentPlugin):
    """Active Directory data collector and management plugin using SSH relay."""

    name = "active_directory"
    version = "3.0.0-rc1"
    description = "Active Directory SSH-relay collector and management plugin"
    platform_required = None

    _IDENTITY_NAME_RE = re.compile(r"^[A-Za-z0-9_\-\.\$ ]+$")

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

    @staticmethod
    def _encode_ps(script: str) -> str:
        return base64.b64encode(script.encode("utf-16le")).decode("ascii")

    @staticmethod
    def _ps_escape(value: Any) -> str:
        return str(value).replace("'", "''")

    @staticmethod
    def _b64_utf8(value: str) -> str:
        return base64.b64encode(value.encode("utf-8")).decode("ascii")

    @classmethod
    def _valid_identity_name(cls, value: str) -> bool:
        return bool(cls._IDENTITY_NAME_RE.fullmatch(value or ""))

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

        $replStatus = 'unknown'
        $pending = 0
        $failed = 0
        $repadmin = Get-Command repadmin.exe -ErrorAction SilentlyContinue
        if ($repadmin) {
          $summary = & repadmin /replsummary 2>$null | Out-String
          if ($summary) {
            $failed = @($summary -split "`n" | Where-Object { $_ -match 'FAIL' }).Count
            if ($failed -gt 0) { $replStatus = 'degraded' } else { $replStatus = 'healthy' }
          }
        } else {
          $replStatus = 'healthy'
        }

        @{
            available = $true
            domain = @{ name = $dom.Name; base_dn = $dom.DistinguishedName }
            forest = $forest
            domain_controllers = $dcs
            users = $users
            groups = $groups
            devices = $devices
            health = @{
                status = $replStatus
                replication = @{ status = $replStatus; pending_replications = $pending; failed_replications = $failed }
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
        group_name = args.get("group_name") or ""
        display_name = args.get("display_name") or ""

        cmd_clean = command.removeprefix("ad:").removeprefix("active_directory:")

        if not self._valid_identity_name(sam):
            return {"success": False, "error": "Invalid characters in identity name"}
        if cmd_clean in ("rename",) and not self._valid_identity_name(display_name):
            return {"success": False, "error": "Invalid characters in identity name"}
        if cmd_clean in (
            "add-to-group",
            "remove-from-group",
        ) and not self._valid_identity_name(group_name):
            return {"success": False, "error": "Invalid characters in identity name"}

        safe_sam = self._ps_escape(sam)
        safe_group = self._ps_escape(group_name)
        safe_display = self._ps_escape(display_name)
        pw_b64 = self._b64_utf8(args.get("new_password", "") or "")

        scripts = {
            "test_connection": (
                "if (Get-Module ActiveDirectory -ListAvailable) "
                "{ @{success=$true; message='AD module available'} | ConvertTo-Json } "
                "else { @{success=$false; error='No AD module'} | ConvertTo-Json }"
            ),
            "reset-password": (
                f"$pw = [System.Text.Encoding]::UTF8.GetString("
                f"[System.Convert]::FromBase64String('{pw_b64}')); "
                f"try {{ "
                f"Set-ADAccountPassword -Identity '{safe_sam}' -NewPassword "
                f"(ConvertTo-SecureString $pw -AsPlainText -Force) -Reset -ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json "
                f"}} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json "
                f"}}"
            ),
            "unlock": (
                f"try {{ Unlock-ADAccount -Identity '{safe_sam}' -ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json }} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json }}"
            ),
            "enable": (
                f"try {{ Enable-ADAccount -Identity '{safe_sam}' -ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json }} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json }}"
            ),
            "disable": (
                f"try {{ Disable-ADAccount -Identity '{safe_sam}' -ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json }} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json }}"
            ),
            "rename": (
                f"try {{ Set-ADUser -Identity '{safe_sam}' -DisplayName '{safe_display}' "
                f"-ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json }} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json }}"
            ),
            "get-user-groups": (
                f"$groups = @(Get-ADPrincipalGroupMembership -Identity '{safe_sam}' | "
                f"Select-Object -ExpandProperty Name | ForEach-Object {{@{{name=$_}}}}); "
                f"@{{success=$true; groups=$groups}} | ConvertTo-Json -Depth 3"
            ),
            "add-to-group": (
                f"try {{ Add-ADGroupMember -Identity '{safe_group}' -Members '{safe_sam}' "
                f"-ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json }} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json }}"
            ),
            "remove-from-group": (
                f"try {{ Remove-ADGroupMember -Identity '{safe_group}' -Members '{safe_sam}' "
                f"-Confirm:$false -ErrorAction Stop; "
                f"@{{success=$true}} | ConvertTo-Json }} catch {{ "
                f"@{{success=$false; error=$_.Exception.Message}} | ConvertTo-Json }}"
            ),
        }

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
