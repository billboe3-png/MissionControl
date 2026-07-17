import logging

from fastapi import APIRouter

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

router = APIRouter(prefix="/version", tags=["version"])


@router.get("")
async def version() -> dict[str, str]:
    return {
        "name": settings.project_name,
        "version": "3.0.0",
    }
