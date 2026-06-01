"""NLP service health check."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../nlp_service"))


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["embedder_loaded"] is True
    assert data["classifier_loaded"] is True
