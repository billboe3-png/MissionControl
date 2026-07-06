from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/docker", tags=["docker"])


@router.get("")
async def docker():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
