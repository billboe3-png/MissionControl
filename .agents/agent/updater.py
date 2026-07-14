"""Mission Control Agent - Self-update mechanism."""

import logging
import subprocess
import sys

from agent.client import AgentClient

logger = logging.getLogger("mc-agent")


class AgentUpdater:
    """Handles agent self-updates from Mission Control server."""

    def __init__(self, client: AgentClient, current_version: str):
        self.client = client
        self.current_version = current_version

    async def check_for_update(self) -> dict:
        """Check if a newer version is available."""
        try:
            result = await self.client.get(
                "/api/v1/version",
            )
            server_version = result.get("version", self.current_version)
            update_available = self._compare_versions(
                server_version, self.current_version
            )
            return {
                "update_available": update_available,
                "latest_version": server_version,
                "current_version": self.current_version,
            }
        except Exception as e:
            logger.debug("Version check failed: %s", e)
            return {
                "update_available": False,
                "latest_version": self.current_version,
                "current_version": self.current_version,
            }

    async def perform_update(self) -> dict:
        """Perform the agent update."""
        try:
            result = await self.check_for_update()
            if not result["update_available"]:
                return {
                    "updated": False,
                    "message": "Already on latest version",
                }

            logger.info(
                "Updating agent from %s to %s",
                self.current_version,
                result["latest_version"],
            )

            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade",
                 "mission-control-agent"],
                check=True,
                timeout=120,
            )

            return {
                "updated": True,
                "message": f"Updated to {result['latest_version']}",
                "previous_version": self.current_version,
                "new_version": result["latest_version"],
            }
        except Exception as e:
            logger.error("Update failed: %s", e)
            return {
                "updated": False,
                "message": f"Update failed: {e}",
            }

    @staticmethod
    def _compare_versions(new: str, current: str) -> bool:
        """Check if new version is newer than current."""
        try:
            from packaging.version import Version

            return Version(new) > Version(current)
        except Exception:
            return new != current
