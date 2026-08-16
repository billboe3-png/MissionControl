"""Mission Control Agent - Self-update mechanism."""

import asyncio
import hashlib
import logging
import sys
from datetime import UTC, datetime

from agent.client import AgentClient

logger = logging.getLogger("mc-agent")


class AgentUpdater:
    """Handles agent self-updates from Mission Control server."""

    def __init__(self, client: AgentClient, current_version: str):
        self.client = client
        self.current_version = current_version
        self._rollback_version: dict | None = None
        self._maintenance_window: tuple[int, int] | None = None
        self._deferred_updates: dict[str, str] = {}

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

            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install",
                "--upgrade", "mission-control-agent",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(  # noqa: RUF059
                proc.communicate(), timeout=120,
            )

            if proc.returncode != 0:
                msg = stderr.decode().strip()
                logger.error("Update failed: %s", msg)
                return {
                    "updated": False,
                    "message": f"pip upgrade failed: {msg}",
                }

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

    # ------------------------------------------------------------------ #
    # Signature Verification                                              #
    # ------------------------------------------------------------------ #

    async def check_signature(
        self, update_url: str, expected_hash: str
    ) -> bool:
        """Download an update artifact and verify its SHA-256 hash."""
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c",
                f"import urllib.request; urllib.request.urlretrieve("
                f"'{update_url}', '_update_artifact.bin')",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=60)

            if proc.returncode != 0:
                logger.error("Failed to download update artifact")
                return False

            sha256 = hashlib.sha256()
            with open("_update_artifact.bin", "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            actual_hash = sha256.hexdigest()
            if actual_hash != expected_hash:
                logger.error(
                    "Signature mismatch: expected %s, got %s",
                    expected_hash,
                    actual_hash,
                )
                return False

            logger.info("Update signature verified: %s", actual_hash)
            return True
        except Exception as e:
            logger.error("Signature check failed: %s", e)
            return False

    # ------------------------------------------------------------------ #
    # Rollback                                                            #
    # ------------------------------------------------------------------ #

    def create_rollback_point(self) -> dict:
        """Snapshot current version info for later rollback."""
        self._rollback_version = {
            "version": self.current_version,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        logger.info(
            "Rollback point created for version %s",
            self.current_version,
        )
        return self._rollback_version

    def rollback(self) -> dict:
        """Restore previous version from a rollback point."""
        if self._rollback_version is None:
            return {
                "rolled_back": False,
                "message": "No rollback point available",
            }

        target = self._rollback_version["version"]
        logger.info(
            "Rolling back from %s to %s",
            self.current_version,
            target,
        )
        self._rollback_version = None
        return {
            "rolled_back": True,
            "previous_version": self.current_version,
            "restored_version": target,
        }

    # ------------------------------------------------------------------ #
    # Maintenance Window                                                  #
    # ------------------------------------------------------------------ #

    def set_maintenance_window(
        self, start_hour: int, end_hour: int
    ) -> None:
        """Define a maintenance window (hour range 0-23)."""
        self._maintenance_window = (start_hour, end_hour)
        logger.info(
            "Maintenance window set: %02d:00 - %02d:00",
            start_hour,
            end_hour,
        )

    def is_in_maintenance_window(self) -> bool:
        """Check if the current time falls within the maintenance window."""
        if self._maintenance_window is None:
            return True

        start, end = self._maintenance_window
        now = datetime.now().hour

        if start <= end:
            return start <= now < end
        # Wraps midnight (e.g. 22 -> 6)
        return now >= start or now < end

    # ------------------------------------------------------------------ #
    # Deferred Updates                                                    #
    # ------------------------------------------------------------------ #

    def defer_update(self, version: str, until: str) -> None:
        """Defer updates to a specific version until an ISO date string."""
        self._deferred_updates[version] = until
        logger.info(
            "Update to %s deferred until %s", version, until,
        )

    def is_deferred(self, version: str) -> bool:
        """Check if updates to a version are currently deferred."""
        until_str = self._deferred_updates.get(version)
        if until_str is None:
            return False

        try:
            until = datetime.fromisoformat(until_str)
            if until.tzinfo is None:
                until = until.replace(tzinfo=UTC)
            if datetime.now(UTC) >= until:
                del self._deferred_updates[version]
                return False
            return True
        except (ValueError, TypeError):
            del self._deferred_updates[version]
            return False
