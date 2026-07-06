from app.platform import get_platform

async def get_docker_status():
    return await get_platform().docker_status()
