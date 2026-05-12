from __future__ import annotations

from datetime import datetime, UTC
from pydantic import Field
from .common import MongoModel


class AttributeMetric(MongoModel):
    id: None = None
    attribute: str                    # gender | age_group | field_of_study | socioeconomic_background
    disparate_impact_ratio: float
    equal_opportunity_score: float
    flagged: bool                     # True if disparate_impact_ratio < 0.80


class BiasAuditDocument(MongoModel):
    """bias_audit collection — read-only snapshots triggered by admin."""

    triggered_by: str                 # admin user_id
    metrics: list[AttributeMetric]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
