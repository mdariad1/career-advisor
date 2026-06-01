"""Lazy model singletons — loaded once at startup, reused across requests."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_embedder = None
_classifier = None
_mlb = None  # MultiLabelBinarizer fitted during training


def get_embedder():
    """Return the cached SentenceTransformer instance, loading it on first call."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        from .config import settings
        logger.info("Loading sentence-transformer: %s", settings.model_name)
        _embedder = SentenceTransformer(settings.model_name)
        logger.info("Sentence-transformer loaded")
    return _embedder


def get_classifier():
    """Return the cached (classifier, mlb) pair, loading from disk on first call."""
    global _classifier, _mlb
    if _classifier is None:
        import joblib
        from .config import settings
        path = Path(settings.classifier_path)
        if not path.exists():
            raise FileNotFoundError(
                f"SVM classifier not found at '{path}'. "
                "Run `python -m app.train` to train it first."
            )
        bundle = joblib.load(path)
        _classifier = bundle["classifier"]
        _mlb = bundle["mlb"]
        logger.info("SVM classifier loaded from %s", path)
    return _classifier, _mlb


def reset_models() -> None:
    """Force model reload on next access — used in tests."""
    global _embedder, _classifier, _mlb
    _embedder = None
    _classifier = None
    _mlb = None
