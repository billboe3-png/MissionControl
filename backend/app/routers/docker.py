import logging

from fastapi import APIRouter, Depends

from app.core.auth_dependency import get_current_user
from app.models.docker import DockerResponse
from app.services.docker_service import get_docker_status

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system/docker",
    tags=["Docker"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=DockerResponse)
async def docker_status():
    return await get_docker_status()
