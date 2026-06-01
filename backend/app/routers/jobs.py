"""Jobs route — paginated query of the local jobs_snapshot cache."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..database import jobs_snapshot_col
from ..dependencies import get_current_user

router = APIRouter()

_MAX_LIMIT = 100


@router.get("/")
async def list_jobs(
    industry: str | None = Query(None, description="Filter by industry slug"),
    country_code: str | None = Query(None, description="Filter by ISO country code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=_MAX_LIMIT),
    current_user: dict = Depends(get_current_user),
):
    """Return a paginated slice of the jobs_snapshot cache with optional filters."""
    query: dict = {"is_stale": False}
    if industry:
        query["industry"] = industry
    if country_code:
        query["country_code"] = country_code

    col = jobs_snapshot_col()
    total = await col.count_documents(query)
    docs = await col.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(length=limit)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "jobs": docs,
    }
