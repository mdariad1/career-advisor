from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers import embed, classify, analyse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load models at startup so the first request is not slow
    try:
        from .models import get_embedder, get_classifier
        get_embedder()
        get_classifier()
        logger.info("NLP models loaded successfully")
    except FileNotFoundError as exc:
        logger.warning("Classifier not found at startup: %s — run `python -m app.train`", exc)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Career Advisor NLP Service",
        description="MiniLM embedding and SVM thematic classification for open-text responses.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(embed.router, prefix="/embed", tags=["embed"])
    app.include_router(classify.router, prefix="/classify", tags=["classify"])
    app.include_router(analyse.router, prefix="/analyse", tags=["analyse"])

    @app.get("/health", tags=["health"])
    async def health():
        from .models import _embedder, _classifier
        return {
            "status": "ok",
            "embedder_loaded": _embedder is not None,
            "classifier_loaded": _classifier is not None,
        }

    return app


app = create_app()
