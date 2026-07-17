"""
Mission Control Automation Provider Base

Abstract base class defining the contract for all automation execution
providers. Each provider implements a specific execution backend.

Sprint 2.8 - Automation & Playbooks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StepResult:
    """Result of executing a single playbook step."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    error: str | None = None


@dataclass
class ExecutionContext:
    """Context passed to providers during step execution."""

    playbook_id: int
    execution_id: int
    step_id: int
    step_name: str
    command: str
    provider: str
    target_host: str | None = None
    shell: str | None = None
    working_directory: str | None = None
    environment_variables: dict[str, str] | None = None
    timeout_seconds: int = 300
    variables: dict[str, str] | None = None


class AutomationProvider(ABC):
    """
    Abstract base class for automation execution providers.

    Each concrete provider must implement:
    - execute_step: Run a single playbook step
    - validate_step: Validate step configuration without executing
    - rollback_step: Execute a rollback command for a step
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier string."""
        ...

    @property
    @abstractmethod
    def supported_step_types(self) -> list[str]:
        """Return list of supported step type identifiers."""
        ...

    @abstractmethod
    async def execute_step(
        self, context: ExecutionContext
    ) -> StepResult:
        """Execute a single playbook step."""
        ...

    @abstractmethod
    async def validate_step(
        self, context: ExecutionContext
    ) -> dict:
        """Validate a step configuration without executing it."""
        ...

    @abstractmethod
    async def rollback_step(
        self, context: ExecutionContext, rollback_command: str
    ) -> StepResult:
        """Execute a rollback command for a failed step."""
        ...
