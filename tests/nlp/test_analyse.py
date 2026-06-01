"""Analyse endpoint tests — combined embed + classify, as called by backend survey flow."""
import pytest

VALID_LABELS = {"analytical", "creative", "interpersonal", "technical", "leadership", "structured"}

_PAYLOAD = {
    "user_id": "test_user_001",
    "session_id": "test_session_001",
    "text": "I enjoy solving complex engineering problems and working closely with teammates.",
}


async def test_analyse_returns_200(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text


async def test_analyse_returns_all_fields(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "embedding" in data
    assert "labels" in data
    assert "label_scores" in data


async def test_analyse_embedding_is_384_dim(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["embedding"]) == 384


async def test_analyse_labels_valid(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    for label in resp.json()["labels"]:
        assert label in VALID_LABELS


async def test_analyse_label_scores_cover_all_labels(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert set(resp.json()["label_scores"].keys()) == VALID_LABELS


async def test_analyse_scores_are_probabilities(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    for score in resp.json()["label_scores"].values():
        assert 0.0 <= score <= 1.0


async def test_analyse_at_least_one_label(client):
    resp = await client.post("/analyse/", json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["labels"]) >= 1


async def test_analyse_analytical_text_detected(client):
    resp = await client.post("/analyse/", json={
        "user_id": "u", "session_id": "s",
        "text": "I love statistical analysis, data modelling, and evidence-based decision making.",
    })
    assert resp.status_code == 200, resp.text
    assert "analytical" in resp.json()["labels"]


async def test_analyse_technical_text_detected(client):
    resp = await client.post("/analyse/", json={
        "user_id": "u", "session_id": "s",
        "text": "Writing clean code, debugging systems, and building infrastructure excite me.",
    })
    assert resp.status_code == 200, resp.text
    assert "technical" in resp.json()["labels"]


async def test_analyse_empty_text_rejected(client):
    resp = await client.post("/analyse/", json={"user_id": "u", "session_id": "s", "text": "  "})
    assert resp.status_code == 422


async def test_analyse_missing_fields_rejected(client):
    resp = await client.post("/analyse/", json={"text": "some text"})
    assert resp.status_code == 422
