from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Optional
from pydantic import Field
from .common import MongoModel, PyObjectId


class ResultDocument(MongoModel):
    """results collection — one document per survey session (created at start, completed on submit)."""

    user_id: PyObjectId
    session_id: PyObjectId
    survey_type: str                            # aptitude | personality | open_text
    question_ids: list[str] = []               # ObjectId strings of questions asked
    answers: list[Any] = []                    # raw submitted answer indices
    score: Optional[float] = None              # aptitude: correct / total, normalised [0, 1]
    ocean_vector: Optional[list[float]] = None # personality: [O, C, E, A, N] each [0, 1]
    status: str = "started"                    # started | completed
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
