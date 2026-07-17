"""
Mission Control Remote Dashboard Provider

Provides aggregate data for the remote operations dashboard card.

Sprint 2.1.0 - Remote Operations Framework.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.command_history import CommandHistory
from app.models.db.remote_host import RemoteHost

logger = logging.getLogger(__name__)


class RemoteProvider:
    """Aggregate remote operations data for the dashboard card."""

    async def get_remote_data(self, db: Session) -> dict:
        """
        Return aggregate remote ops stats:
        - totalHosts: count of all remote hosts
        - enabledHosts: count of enabled hosts
        - recentCommands: last 5 command history entries
        """
        try:
            total_result = db.execute(
                select(func.count()).select_from(RemoteHost)
            )
            total_hosts = total_result.scalar() or 0

            enabled_result = db.execute(
                select(func.count()).select_from(RemoteHost).where(
                    RemoteHost.enabled.is_(True)
                )
            )
            enabled_hosts = enabled_result.scalar() or 0

            recent_result = db.execute(
                select(CommandHistory)
                .order_by(CommandHistory.started_at.desc())
                .limit(5)
            )
            recent_commands = recent_result.scalars().all()

            return {
                "totalHosts": total_hosts,
                "enabledHosts": enabled_hosts,
                "recentCommands": [
                    {
                        "id": cmd.id,
                        "hostId": cmd.host_id,
                        "command": cmd.command,
                        "success": cmd.success,
                        "startedAt": (
                            cmd.started_at.isoformat()
                            if cmd.started_at
                            else None
                        ),
                    }
                    for cmd in recent_commands
                ],
            }
        except Exception:
            logger.exception("Failed to fetch remote dashboard data")
            return {
                "totalHosts": 0,
                "enabledHosts": 0,
                "recentCommands": [],
            }
