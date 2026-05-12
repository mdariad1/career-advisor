from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional
from pydantic import Field
from .common import MongoModel, PyObjectId


class NlpAnalysisDocument(MongoModel):
    """nlp_analysis collection — stored result of NLP service processing."""

    user_id: PyObjectId
    session_id: PyObjectId
    raw_text: str
    embedding: list[float]              # 384-dim MiniLM vector
    labels: list[str]                   # thematic labels from SVM
    label_scores: dict[str, float]      # per-label confidence scores
    status: str = "pending"             # pending | done | error
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
