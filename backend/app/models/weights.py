from __future__ import annotations

from datetime import datetime, UTC
from pydantic import Field
from .common import MongoModel, PyObjectId


class WeightsDocument(MongoModel):
    """weights collection — one document per user, updated by feedback loop."""

    user_id: PyObjectId
    aptitude: float = 0.25
    personality_fit: float = 0.30
    nlp_similarity: float = 0.25
    market_demand: float = 0.20
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
