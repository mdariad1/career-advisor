"""Embed endpoint tests."""
import pytest


async def test_embed_returns_384_dim(client):
    resp = await client.post("/embed/", json={"text": "I enjoy solving engineering problems."})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["dim"] == 384
    assert len(data["embedding"]) == 384


async def test_embed_values_are_floats(client):
    resp = await client.post("/embed/", json={"text": "I love data analysis and modelling."})
    assert resp.status_code == 200, resp.text
    assert all(isinstance(v, float) for v in resp.json()["embedding"])


async def test_embed_normalised(client):
    """Normalised embeddings should have unit L2 norm."""
    import math
    resp = await client.post("/embed/", json={"text": "Leadership and team management."})
    assert resp.status_code == 200, resp.text
    vec = resp.json()["embedding"]
    norm = math.sqrt(sum(v ** 2 for v in vec))
    assert norm == pytest.approx(1.0, abs=1e-3)


async def test_embed_different_texts_give_different_vectors(client):
    resp_a = await client.post("/embed/", json={"text": "I love creative design work."})
    resp_b = await client.post("/embed/", json={"text": "Statistical modelling excites me."})
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    assert resp_a.json()["embedding"] != resp_b.json()["embedding"]


async def test_embed_same_text_gives_same_vector(client):
    text = "Consistent, deterministic embedding."
    resp_a = await client.post("/embed/", json={"text": text})
    resp_b = await client.post("/embed/", json={"text": text})
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    assert resp_a.json()["embedding"] == resp_b.json()["embedding"]


async def test_embed_empty_text_rejected(client):
    resp = await client.post("/embed/", json={"text": "   "})
    assert resp.status_code == 422


async def test_embed_missing_text_rejected(client):
    resp = await client.post("/embed/", json={})
    assert resp.status_code == 422
