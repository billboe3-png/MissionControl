from fastapi import APIRouter

from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/version", tags=["version"])


@router.get("")
async def version() -> dict[str, str]:
    return {
        "name": settings.project_name,
        "version": "0.1.0",
    }
