"""
MikroTik Sync Module
"""
import logging

from sqlalchemy.orm import Session

from app.plugins.installed.official_mikrotik.service import mikrotik_service

logger = logging.getLogger("plugin.mikrotik.sync")


async def sync_all(db: Session) -> dict[str, int]:
    """Sync status/facts for all enabled MikroTik servers."""
    return await mikrotik_service.sync_all(db)
