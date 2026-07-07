"""
Docker Service

Provides Docker information through the platform abstraction.
"""

from app.platform import get_platform


async def get_docker_status():
    """Return Docker status from the active platform."""
    return await get_platform().docker_status()
