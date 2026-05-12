from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional
from pydantic import EmailStr, Field
from .common import MongoModel


class WeightVector(MongoModel):
    """Per-user scoring weights. Always sum to 1.0, each in [0.05, 0.50]."""

    id: None = None  # not a top-level document
    aptitude: float = Field(default=0.25, ge=0.05, le=0.50)
    personality_fit: float = Field(default=0.30, ge=0.05, le=0.50)
    nlp_similarity: float = Field(default=0.25, ge=0.05, le=0.50)
    market_demand: float = Field(default=0.20, ge=0.05, le=0.50)


class UserDocument(MongoModel):
    """users collection — psychometric profile only (no demographics)."""

    email: EmailStr
    hashed_password: str
    full_name: str
    role: str = "user"
    # Psychometric profile (null until the relevant assessment is completed)
    aptitude_score: Optional[float] = None          # normalised [0, 1]
    ocean_vector: Optional[list[float]] = None      # [O, C, E, A, N] each in [0, 1]
    nlp_labels: Optional[list[str]] = None
    nlp_embedding_id: Optional[str] = None          # ref → nlp_analysis._id
    weights: WeightVector = Field(default_factory=WeightVector)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserCreate(MongoModel):
    """Input schema for registration (never stored directly)."""

    id: None = None
    email: EmailStr
    password: str
    full_name: str
