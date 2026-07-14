"""
Mission Control Proxmox Automation Provider

Executes Proxmox actions via API calls.

Sprint 2.8 - Automation & Playbooks.
"""

import logging
import time

from app.providers.automation.base_provider import (
    AutomationProvider,
    ExecutionContext,
    StepResult,
)

logger = logging.getLogger(__name__)


class ProxmoxAutomationProvider(AutomationProvider):
    """Execute Proxmox VE actions via API."""

    @property
    def provider_name(self) -> str:
        return "proxmox"

    @property
    def supported_step_types(self) -> list[str]:
        return ["proxmox_action", "remote_command"]

    async def execute_step(
        self, context: ExecutionContext
    ) -> StepResult:
        start = time.monotonic()

        try:
            command = context.command

            if context.variables:
                for key, value in context.variables.items():
                    command = command.replace(
                        f"{{{{{key}}}}}", value
                    )

            from app.providers.remote.provider_factory import (
                get_remote_provider,
            )

            provider = get_remote_provider("ssh")

            hostname = context.target_host or "localhost"

            result = await provider.execute_command(
                hostname=hostname,
                port=22,
                username="",
                password=None,
                ssh_key=None,
                command=command,
                shell="bash",
                ip_address=None,
            )

            duration_ms = int(
                (time.monotonic() - start) * 1000
            )

            return StepResult(
                success=result.get("exit_code", -1) == 0,
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                exit_code=result.get("exit_code", -1),
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int(
                (time.monotonic() - start) * 1000
            )
            logger.error(
                "Proxmox automation step failed: %s", exc
            )
            return StepResult(
                success=False,
                error=str(exc),
                exit_code=-1,
                duration_ms=duration_ms,
            )

    async def validate_step(
        self, context: ExecutionContext
    ) -> dict:
        warnings = []
        errors = []

        if not context.command:
            errors.append("Command is required")
        if not context.target_host:
            warnings.append(
                "No Proxmox host specified, will use default"
            )

        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
        }

    async def rollback_step(
        self, context: ExecutionContext, rollback_command: str
    ) -> StepResult:
        rollback_ctx = ExecutionContext(
            playbook_id=context.playbook_id,
            execution_id=context.execution_id,
            step_id=context.step_id,
            step_name=f"{context.step_name} (rollback)",
            command=rollback_command,
            provider=context.provider,
            target_host=context.target_host,
            shell="bash",
            working_directory=context.working_directory,
            environment_variables=context.environment_variables,
            timeout_seconds=context.timeout_seconds,
            variables=context.variables,
        )
        return await self.execute_step(rollback_ctx)
