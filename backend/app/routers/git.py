import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/git", tags=["git"])


@router.get("")
async def git():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
