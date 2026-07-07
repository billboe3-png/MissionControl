"""
Mission Control Task Service

Provides the Tasks section of the dashboard.

Sprint:
    1.0.3
"""


class TaskService:
    """Task dashboard section."""

    async def get_data(self) -> dict:
        """Return task information."""

        return {
            "count": 0,
            "items": [],
        }


task_service = TaskService()
