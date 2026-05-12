from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional
from pydantic import Field
from .common import MongoModel, PyObjectId


class ShapBreakdown(MongoModel):
    id: None = None
    aptitude: float
    personality_fit: float
    nlp_similarity: float
    market_demand: float


class RecommendationDocument(MongoModel):
    """recommendations collection — top-5 career matches per scoring run."""

    user_id: PyObjectId
    career_id: str
    career_title: str
    score: float                          # composite score in [0, 1]
    contributions: ShapBreakdown          # SHAP percentage breakdown
    explanation: str                      # plain-language summary
    salary_range: Optional[str] = None
    job_count: int = 0
    weights_snapshot: dict = Field(default_factory=dict)  # weight vector at scoring time
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
