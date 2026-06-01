"""Analyse endpoint — combined embed + classify, called by the backend survey router."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

_SCORE_THRESHOLD = 0.25


class AnalyseRequest(BaseModel):
    user_id: str
    session_id: str
    text: str


class AnalyseResponse(BaseModel):
    embedding: list[float]
    labels: list[str]
    label_scores: dict[str, float]


@router.post("/", response_model=AnalyseResponse)
async def analyse_text(body: AnalyseRequest):
    """Embed text and classify thematic labels in a single call (used by backend survey flow)."""
    if not body.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="text must not be empty")

    import numpy as np
    from ..models import get_classifier, get_embedder

    embedder = get_embedder()
    vec = embedder.encode(body.text, show_progress_bar=False, normalize_embeddings=True)
    embedding: list[float] = vec.tolist()

    clf, mlb = get_classifier()
    X = vec.reshape(1, -1)
    proba = clf.predict_proba(X)[0]

    label_scores = {label: round(float(p), 4) for label, p in zip(mlb.classes_, proba)}
    labels = [label for label, p in label_scores.items() if p >= _SCORE_THRESHOLD]
    if not labels:
        labels = [max(label_scores, key=label_scores.get)]

    return AnalyseResponse(embedding=embedding, labels=labels, label_scores=label_scores)
