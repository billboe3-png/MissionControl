import logging

from fastapi import APIRouter

from app.platform import get_platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("")
async def doctor():

    platform = get_platform()

    return await platform.doctor()
