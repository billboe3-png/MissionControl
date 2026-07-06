from fastapi import APIRouter

from app.platform import get_platform

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def status():

    platform = get_platform()

    return await platform.status()
