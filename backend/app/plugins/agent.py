"""
Mission Control Agent Plugin SDK

Base class for plugins that run inside the Mission Control Agent.
Agent plugins execute locally on managed hosts without exposing
the host directly. They can register commands, scheduled tasks,
background workers, health checks, inventory collectors, and more.
"""

from typing import Any

from app.plugins.base import PluginSDK


class AgentPluginSDK(PluginSDK):
    """
    Abstract base class for agent-side plugins.

    Agent plugins extend managed hosts with:
    - Commands that execute locally
    - Scheduled tasks
    - Background workers
    - Health checks
    - Inventory collectors
    - Performance counters
    - File collectors
    - Event collectors
    - Playbook actions
    - Automation actions
    """

    # ------------------------------------------------------------------ #
    # Commands                                                            #
    # ------------------------------------------------------------------ #

    def get_commands(self) -> list[dict[str, Any]]:
        """Return commands this plugin can execute.

        Each command dict should contain:
        - id: unique command identifier
        - name: human-readable name
        - description: what the command does
        - handler: async callable that executes the command
        """
        return []

    async def execute_command(
        self, command_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a plugin command.

        Returns:
        - success: bool
        - output: command output
        - error: error message if failed
        """
        raise NotImplementedError(f"Command '{command_id}' not implemented")

    # ------------------------------------------------------------------ #
    # Scheduled Tasks                                                     #
    # ------------------------------------------------------------------ #

    def get_scheduled_tasks(self) -> list[dict[str, Any]]:
        """Return scheduled task definitions.

        Each task dict should contain:
        - id: unique task identifier
        - name: human-readable name
        - schedule: cron expression or interval
        - handler: async callable
        """
        return []

    # ------------------------------------------------------------------ #
    # Background Workers                                                  #
    # ------------------------------------------------------------------ #

    def get_background_workers(self) -> list[dict[str, Any]]:
        """Return background worker definitions.

        Each worker dict should contain:
        - id: unique worker identifier
        - name: human-readable name
        - handler: async callable
        """
        return []

    # ------------------------------------------------------------------ #
    # Health Checks                                                       #
    # ------------------------------------------------------------------ #

    async def get_health_status(self) -> dict[str, Any]:
        """Return health status of the agent host from this plugin's perspective.

        Returns:
        - status: "healthy" | "degraded" | "unhealthy"
        - checks: list of individual check results
        - details: additional health information
        """
        return {"status": "healthy", "checks": [], "details": {}}

    # ------------------------------------------------------------------ #
    # Inventory                                                           #
    # ------------------------------------------------------------------ #

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect inventory data from the agent host.

        Returns a dict of inventory data that will be merged
        into the agent's inventory.
        """
        return {}

    # ------------------------------------------------------------------ #
    # Performance Counters                                                #
    # ------------------------------------------------------------------ #

    async def collect_performance_counters(self) -> dict[str, Any]:
        """Collect performance counter data.

        Returns a dict of performance metrics.
        """
        return {}

    # ------------------------------------------------------------------ #
    # File Collection                                                     #
    # ------------------------------------------------------------------ #

    async def collect_files(
        self, paths: list[str]
    ) -> list[dict[str, Any]]:
        """Collect files from the agent host.

        Returns list of file metadata and content.
        """
        return []

    # ------------------------------------------------------------------ #
    # Event Collection                                                    #
    # ------------------------------------------------------------------ #

    async def collect_events(
        self, source: str, since: str | None = None
    ) -> list[dict[str, Any]]:
        """Collect events from the agent host.

        Returns list of event records.
        """
        return []

    # ------------------------------------------------------------------ #
    # Playbook / Automation Actions                                       #
    # ------------------------------------------------------------------ #

    async def execute_playbook_action(
        self, action_id: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a playbook action on this agent.

        Returns action result.
        """
        return {"success": False, "error": "Not implemented"}

    async def execute_automation_action(
        self, action_id: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute an automation action on this agent.

        Returns action result.
        """
        return {"success": False, "error": "Not implemented"}
