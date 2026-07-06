from fastapi import APIRouter

from app.services import get_docker_status

router = APIRouter(tags=["docker"])


@router.get("/docker")
async def docker():

    return await get_docker_status()
