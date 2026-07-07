"""
Mission Control Note Service
"""


class NoteService:
    """Notes dashboard section."""

    async def get_data(self) -> dict:

        return {
            "count": 0,
            "items": [],
        }


note_service = NoteService()
