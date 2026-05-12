from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional
from pydantic import Field
from .common import MongoModel


class CareerArchetypeDocument(MongoModel):
    """career_archetypes collection — reference vectors for each career category."""

    career_id: str          # canonical slug, e.g. "software_engineer"
    career_title: str
    ocean_vector: list[float]          # mean Big Five vector [O, C, E, A, N]
    nlp_centroid: list[float]          # mean 384-dim embedding from training corpus
    thematic_labels: list[str]
    market_demand_seed: float = 0.5   # initial signal from Kaggle job market dataset
    sample_size: int = 0
    source: str = "empirical"         # empirical | theoretical_fallback
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
