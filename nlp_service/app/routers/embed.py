"""Embed endpoint — MiniLM-L6-v2 text embedding."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

EMBEDDING_DIM = 384
_SCORE_THRESHOLD = 0.25  # min probability to include a label


class EmbedRequest(BaseModel):
    text: str
    normalize_skills: bool = False


class EmbedResponse(BaseModel):
    embedding: list[float]
    dim: int = EMBEDDING_DIM


@router.post("/", response_model=EmbedResponse)
async def embed_text(body: EmbedRequest):
    """Encode text with sentence-transformers/all-MiniLM-L6-v2 → 384-dim vector."""
    if not body.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="text must not be empty")

    from ..models import get_embedder
    embedder = get_embedder()
    vec = embedder.encode(body.text, show_progress_bar=False, normalize_embeddings=True)
    return EmbedResponse(embedding=vec.tolist(), dim=len(vec))
