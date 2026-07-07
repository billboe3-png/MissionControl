from fastapi import APIRouter

from app.models.docker import DockerResponse
from app.services.docker_service import get_docker_status

router = APIRouter(
    prefix="/system/docker",
    tags=["Docker"],
)


@router.get("", response_model=DockerResponse)
async def docker_status():
    return await get_docker_status()
