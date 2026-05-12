from fastapi import APIRouter, Depends, Query
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def list_jobs(
    industry: str | None = Query(None),
    country_code: str | None = Query(None),
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Query local jobs_snapshot cache with optional skill and location filters."""
    raise NotImplementedError
