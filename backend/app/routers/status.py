from fastapi import APIRouter

from app.services import get_status

router = APIRouter(tags=["status"])


@router.get("/status")
async def status():
    return await get_status()
