from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def status():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
