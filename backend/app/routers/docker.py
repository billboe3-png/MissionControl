from fastapi import APIRouter

from app.platform import get_platform

router = APIRouter(prefix="/docker", tags=["docker"])


@router.get("")
async def docker():

    platform = get_platform()

    return await platform.docker_status()
