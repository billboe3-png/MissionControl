"""
Mission Control Version API

Returns comprehensive version information including edition, build,
database schema version, and agent compatibility.
"""

import time

from fastapi import APIRouter

router = APIRouter(prefix="/version", tags=["version"])

APP_VERSION = "3.0.0"
DB_SCHEMA_VERSION = "3.0.0"
MIN_AGENT_VERSION = "3.0.0"
PLUGIN_SDK_VERSION = "3.0.0"
EDITION = "community"

_start_time = time.time()


@router.get("")
async def get_version() -> dict:
    """Return full version information."""
    return {
        "version": APP_VERSION,
        "edition": EDITION,
        "build": APP_VERSION,
        "db_schema_version": DB_SCHEMA_VERSION,
        "min_agent_version": MIN_AGENT_VERSION,
        "plugin_sdk_version": PLUGIN_SDK_VERSION,
        "uptime_seconds": round(time.time() - _start_time, 1),
    }
