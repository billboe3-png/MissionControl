from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/git", tags=["git"])


@router.get("")
async def git():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
