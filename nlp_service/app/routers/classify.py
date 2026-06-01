"""Classify endpoint — SVM thematic label classification over a 384-dim embedding."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

_SCORE_THRESHOLD = 0.25  # min probability to include a label as active


class ClassifyRequest(BaseModel):
    embedding: list[float]


class ClassifyResponse(BaseModel):
    labels: list[str]
    scores: dict[str, float]


@router.post("/", response_model=ClassifyResponse)
async def classify_embedding(body: ClassifyRequest):
    """Apply trained SVM classifier to a 384-dim embedding; return thematic labels and scores."""
    if len(body.embedding) != 384:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Expected 384-dim embedding, got {len(body.embedding)}",
        )

    import numpy as np
    from ..models import get_classifier

    clf, mlb = get_classifier()
    X = np.array(body.embedding, dtype=float).reshape(1, -1)
    proba = clf.predict_proba(X)[0]  # shape: (n_labels,)

    scores = {label: round(float(p), 4) for label, p in zip(mlb.classes_, proba)}
    labels = [label for label, p in scores.items() if p >= _SCORE_THRESHOLD]
    if not labels:
        labels = [max(scores, key=scores.get)]  # always return at least one

    return ClassifyResponse(labels=labels, scores=scores)
