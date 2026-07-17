import logging

from fastapi import APIRouter

from app.platform import get_platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def status():

    platform = get_platform()

    return await platform.status()
