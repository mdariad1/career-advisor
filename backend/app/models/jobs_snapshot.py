from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional
from pydantic import Field
from .common import MongoModel


class JobSnapshotDocument(MongoModel):
    """jobs_snapshot collection — live job listings cache from JobDataPool."""

    job_id: str             # JobDataPool canonical ID (unique index key)
    title: str
    company: str
    industry: str
    country_code: str
    salary_range: Optional[str] = None
    skills: list[str] = Field(default_factory=list)       # normalised canonical skill labels
    raw_skills: list[str] = Field(default_factory=list)   # original strings from API
    is_stale: bool = False
    synced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
