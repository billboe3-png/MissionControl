"""
Mission Control Bash Automation Provider

Executes playbook steps via local bash shell.

Sprint 2.8 - Automation & Playbooks.
"""

import asyncio
import logging
import time

from app.providers.automation.base_provider import (
    AutomationProvider,
    ExecutionContext,
    StepResult,
)

logger = logging.getLogger(__name__)


class BashAutomationProvider(AutomationProvider):
    """Execute playbook steps via local bash shell."""

    @property
    def provider_name(self) -> str:
        return "bash"

    @property
    def supported_step_types(self) -> list[str]:
        return ["bash", "shell", "remote_command"]

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

            env_args = []
            if context.environment_variables:
                for k, v in context.environment_variables.items():
                    env_args.append(f"export {k}='{v}';")

            full_command = ""
            if env_args:
                full_command = " ".join(env_args) + " "
            if context.working_directory:
                full_command += f"cd '{context.working_directory}' && "
            full_command += command

            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=context.timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration_ms = int((time.monotonic() - start) * 1000)
                return StepResult(
                    success=False,
                    error=f"Command timed out after {context.timeout_seconds}s",
                    exit_code=-1,
                    duration_ms=duration_ms,
                )

            duration_ms = int((time.monotonic() - start) * 1000)
            exit_code = process.returncode or 0

            return StepResult(
                success=exit_code == 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                exit_code=exit_code,
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error("Bash automation step failed: %s", exc)
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
