from app.platform import get_platform

async def get_doctor():
    return await get_platform().doctor()
