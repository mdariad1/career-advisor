"""Classify endpoint tests."""
import pytest

VALID_LABELS = {"analytical", "creative", "interpersonal", "technical", "leadership", "structured"}


async def _get_embedding(client, text: str) -> list[float]:
    resp = await client.post("/embed/", json={"text": text})
    assert resp.status_code == 200
    return resp.json()["embedding"]


async def test_classify_returns_labels_and_scores(client):
    emb = await _get_embedding(client, "I enjoy writing clean, well-tested code.")
    resp = await client.post("/classify/", json={"embedding": emb})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "labels" in data and "scores" in data


async def test_classify_labels_are_subset_of_valid(client):
    emb = await _get_embedding(client, "Data analysis and statistical modelling.")
    resp = await client.post("/classify/", json={"embedding": emb})
    assert resp.status_code == 200, resp.text
    for label in resp.json()["labels"]:
        assert label in VALID_LABELS


async def test_classify_scores_cover_all_labels(client):
    emb = await _get_embedding(client, "I enjoy leading teams and building strategy.")
    resp = await client.post("/classify/", json={"embedding": emb})
    assert resp.status_code == 200, resp.text
    assert set(resp.json()["scores"].keys()) == VALID_LABELS


async def test_classify_scores_are_probabilities(client):
    emb = await _get_embedding(client, "Creative design and artistic exploration.")
    resp = await client.post("/classify/", json={"embedding": emb})
    assert resp.status_code == 200, resp.text
    for score in resp.json()["scores"].values():
        assert 0.0 <= score <= 1.0


async def test_classify_always_returns_at_least_one_label(client):
    emb = await _get_embedding(client, "I process documents and follow procedures carefully.")
    resp = await client.post("/classify/", json={"embedding": emb})
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["labels"]) >= 1


async def test_classify_technical_text_includes_technical_label(client):
    emb = await _get_embedding(client, "I love writing algorithms and optimising system performance.")
    resp = await client.post("/classify/", json={"embedding": emb})
    assert resp.status_code == 200, resp.text
    assert "technical" in resp.json()["labels"]


async def test_classify_wrong_dim_rejected(client):
    resp = await client.post("/classify/", json={"embedding": [0.1] * 100})
    assert resp.status_code == 422


async def test_classify_missing_embedding_rejected(client):
    resp = await client.post("/classify/", json={})
    assert resp.status_code == 422
