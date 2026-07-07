"""
Mission Control Project Service
"""


class ProjectService:
    """Project dashboard section."""

    async def get_data(self) -> dict:

        return {
            "count": 0,
            "items": [],
        }


project_service = ProjectService()
