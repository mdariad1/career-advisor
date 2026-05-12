from __future__ import annotations

from datetime import datetime, UTC
from pydantic import Field
from .common import MongoModel, PyObjectId


class FeedbackDocument(MongoModel):
    """feedback collection — accept/reject events for every recommendation."""

    user_id: PyObjectId
    recommendation_id: PyObjectId
    action: str             # accept | reject
    top_factor: str         # highest-contributing factor at time of decision
    weights_before: dict    # weight vector before any update
    weights_after: dict     # weight vector after update (same as before for reject)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
