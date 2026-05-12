from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

EMBEDDING_DIM = 384


class EmbedRequest(BaseModel):
    text: str
    normalize_skills: bool = False


class EmbedResponse(BaseModel):
    embedding: list[float]
    dim: int = EMBEDDING_DIM


@router.post("/", response_model=EmbedResponse)
async def embed_text(body: EmbedRequest):
    """
    Preprocess (NLTK) → sentence-transformers/all-MiniLM-L6-v2 → 384-dim vector.
    Set normalize_skills=True for job listing skill normalisation mode.
    """
    raise NotImplementedError
