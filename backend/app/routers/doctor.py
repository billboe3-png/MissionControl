from fastapi import APIRouter

from app.platform import get_platform

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("")
async def doctor():

    platform = get_platform()

    return await platform.doctor()
