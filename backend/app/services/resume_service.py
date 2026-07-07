"""
Mission Control Resume Service
"""


class ResumeService:
    """Resume previous work."""

    async def get_data(self) -> dict:
        return {
            "available": False,
            "title": None,
            "description": None,
        }


resume_service = ResumeService()
