import sys
import os

# Make 'app' resolve to nlp_service/app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../nlp_service"))

import pytest


@pytest.fixture(scope="session")
def trained_model():
    """Ensure the SVM classifier exists before any NLP test runs.

    Trains from the hand-crafted dataset if the model file is absent.
    """
    from pathlib import Path
    from app.config import settings

    path = Path(settings.classifier_path)
    if not path.exists():
        from app.train import train
        train()
    assert path.exists(), "SVM classifier missing after training"
    return path


@pytest.fixture(scope="session")
def app(trained_model):
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="session")
async def client(app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
