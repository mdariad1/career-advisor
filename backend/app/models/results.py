from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Optional
from pydantic import Field
from .common import MongoModel, PyObjectId


class ResultDocument(MongoModel):
    """results collection — one document per completed assessment session."""

    user_id: PyObjectId
    session_id: PyObjectId
    survey_type: str          # aptitude | personality | open_text
    answers: list[Any]        # raw answers as submitted
    score: Optional[float] = None  # only set for aptitude (normalised [0, 1])
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
