"""
Mission Control Agent Automation Provider

Executes playbook steps via the Mission Control Agent
installed on remote hosts.

Sprint 2.8 - Automation & Playbooks.
"""

import json
import logging
import time

import httpx

from app.providers.automation.base_provider import (
    AutomationProvider,
    ExecutionContext,
    StepResult,
)

logger = logging.getLogger(__name__)


class AgentAutomationProvider(AutomationProvider):
    """Execute playbook steps via Mission Control Agent."""

    @property
    def provider_name(self) -> str:
        return "agent"

    @property
    def supported_step_types(self) -> list[str]:
        return [
            "remote_command",
            "powershell",
            "bash",
            "python",
            "file_transfer",
        ]

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

            agent_url = context.target_host or "http://localhost:9090"

            async with httpx.AsyncClient(timeout=context.timeout_seconds) as client:
                response = await client.post(
                    f"{agent_url}/api/v1/execute",
                    json={
                        "command": command,
                        "shell": context.shell or "bash",
                        "working_directory": context.working_directory,
                        "environment": context.environment_variables,
                    },
                )
                response.raise_for_status()

                data = response.json()
                duration_ms = int(
                    (time.monotonic() - start) * 1000
                )

                return StepResult(
                    success=data.get("exit_code", -1) == 0,
                    stdout=data.get("stdout", ""),
                    stderr=data.get("stderr", ""),
                    exit_code=data.get("exit_code", -1),
                    duration_ms=duration_ms,
                )

        except Exception as exc:
            duration_ms = int(
                (time.monotonic() - start) * 1000
            )
            logger.error(
                "Agent automation step failed: %s", exc
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
            errors.append(
                "Agent URL (target_host) is required"
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
            shell=context.shell,
            working_directory=context.working_directory,
            environment_variables=context.environment_variables,
            timeout_seconds=context.timeout_seconds,
            variables=context.variables,
        )
        return await self.execute_step(rollback_ctx)
