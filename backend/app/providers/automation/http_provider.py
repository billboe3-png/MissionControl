"""
Mission Control HTTP Automation Provider

Executes playbook steps via HTTP requests (REST APIs, webhooks).

Sprint 2.8 - Automation & Playbooks.
"""

import json
import logging
import time
from urllib.parse import urljoin

import httpx

from app.providers.automation.base_provider import (
    AutomationProvider,
    ExecutionContext,
    StepResult,
)

logger = logging.getLogger(__name__)


class HTTPAutomationProvider(AutomationProvider):
    """Execute playbook steps via HTTP requests."""

    @property
    def provider_name(self) -> str:
        return "http"

    @property
    def supported_step_types(self) -> list[str]:
        return ["http", "webhook", "api_call"]

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

            try:
                request_data = json.loads(command)
            except json.JSONDecodeError:
                request_data = {
                    "method": "GET",
                    "url": command,
                }

            method = request_data.get("method", "GET").upper()
            url = request_data.get("url", "")
            headers = request_data.get("headers", {})
            body = request_data.get("body")
            timeout = context.timeout_seconds

            if not url:
                return StepResult(
                    success=False,
                    error="No URL specified in HTTP request",
                    exit_code=1,
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                verify=False,
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    content=body if isinstance(body, str) else None,
                )

            duration_ms = int((time.monotonic() - start) * 1000)
            status_code = response.status_code
            success = 200 <= status_code < 300

            stdout = json.dumps({
                "status_code": status_code,
                "headers": dict(response.headers),
                "body": response.text[:10000],
            }, indent=2)

            return StepResult(
                success=success,
                stdout=stdout,
                stderr="" if success else f"HTTP {status_code}: {response.text[:2000]}",
                exit_code=0 if success else status_code,
                duration_ms=duration_ms,
            )

        except httpx.TimeoutException:
            duration_ms = int((time.monotonic() - start) * 1000)
            return StepResult(
                success=False,
                error=f"HTTP request timed out after {context.timeout_seconds}s",
                exit_code=-1,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error("HTTP automation step failed: %s", exc)
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
            errors.append("Command/request is required")
        else:
            try:
                request_data = json.loads(context.command)
                if "url" not in request_data:
                    errors.append("HTTP request must include a 'url' field")
            except json.JSONDecodeError:
                if not context.command.startswith("http"):
                    warnings.append(
                        "Command is not JSON and doesn't look like a URL"
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
