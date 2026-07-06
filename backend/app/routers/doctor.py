from fastapi import APIRouter

from app.services import get_doctor

router = APIRouter(tags=["doctor"])


@router.get("/doctor")
async def doctor():
    return await get_doctor()
