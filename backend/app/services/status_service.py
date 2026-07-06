from app.platform import get_platform

async def get_status():
    return await get_platform().status()
