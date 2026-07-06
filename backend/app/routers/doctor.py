from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("")
async def doctor():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
