from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

router = APIRouter()

ThematicLabel = Literal[
    "analytical", "creative", "interpersonal",
    "technical", "leadership", "structured"
]


class ClassifyRequest(BaseModel):
    embedding: list[float]


class ClassifyResponse(BaseModel):
    labels: list[ThematicLabel]
    scores: dict[str, float]


@router.post("/", response_model=ClassifyResponse)
async def classify_embedding(body: ClassifyRequest):
    """Apply trained SVM classifier over a 384-dim embedding vector."""
    raise NotImplementedError
