"""Feedback route integration tests — live Atlas cluster."""
import pytest
from httpx import AsyncClient, ASGITransport

# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="session")
async def client(app, seeded_surveys, seeded_archetypes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Probe user ────────────────────────────────────────────────────────────────

TEST_EMAIL = "pytest_feedback_probe@example.com"
TEST_PASSWORD = "Feedback1234!"
TEST_NAME = "Feedback Probe"


@pytest.fixture(scope="session")
async def auth_tokens(client):
    from app.database import sessions_col, users_col

    raw = await users_col().find_one({"email": TEST_EMAIL})
    if raw:
        await sessions_col().delete_many({"user_id": str(raw["_id"])})
        await users_col().delete_one({"_id": raw["_id"]})

    resp = await client.post("/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture(scope="session")
def auth_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


@pytest.fixture(scope="session", autouse=True)
async def cleanup_feedback_user(client, auth_tokens):
    yield
    from app.database import (
        feedback_col, nlp_analysis_col, recommendations_col,
        results_col, sessions_col, users_col,
    )
    raw = await users_col().find_one({"email": TEST_EMAIL})
    if raw:
        uid = str(raw["_id"])
        await feedback_col().delete_many({"user_id": uid})
        await recommendations_col().delete_many({"user_id": uid})
        await results_col().delete_many({"user_id": uid})
        await nlp_analysis_col().delete_many({"user_id": uid})
        await sessions_col().delete_many({"user_id": uid})
        await users_col().delete_one({"_id": raw["_id"]})


# ── Helper ────────────────────────────────────────────────────────────────────

async def _generate_and_get_first_rec_id(client, headers) -> str:
    """POST /recommendations and return the top recommendation's ID."""
    resp = await client.post("/recommendations/", headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["recommendations"][0]["id"]


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_feedback_unauthenticated(client):
    resp = await client.post("/feedback/", json={"recommendation_id": "x", "action": "accept"})
    assert resp.status_code in (401, 403)


async def test_feedback_invalid_action_rejected(client, auth_headers):
    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/", json={"recommendation_id": rec_id, "action": "maybe"},
                             headers=auth_headers)
    assert resp.status_code == 422


async def test_feedback_invalid_recommendation_id(client, auth_headers):
    resp = await client.post("/feedback/",
                             json={"recommendation_id": "not-an-objectid", "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 422


async def test_feedback_unknown_recommendation_returns_404(client, auth_headers):
    from bson import ObjectId
    resp = await client.post("/feedback/",
                             json={"recommendation_id": str(ObjectId()), "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 404


async def test_feedback_reject_returns_unchanged_weights(client, auth_headers):
    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "reject"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["action"] == "reject"
    assert data["weights_before"] == data["weights_after"]


async def test_feedback_accept_returns_200_with_weights(client, auth_headers):
    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["action"] == "accept"
    assert "weights_before" in data
    assert "weights_after" in data
    assert "top_factor" in data


async def test_feedback_accept_bumps_top_factor(client, auth_headers):
    """After accept, the top_factor weight must be higher in weights_after."""
    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    top = data["top_factor"]
    assert data["weights_after"][top] > data["weights_before"][top]


async def test_feedback_weights_sum_to_one_after_accept(client, auth_headers):
    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    w = resp.json()["weights_after"]
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-4)


async def test_feedback_weights_in_valid_range(client, auth_headers):
    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    for key, val in resp.json()["weights_after"].items():
        assert 0.05 <= val <= 0.50, f"{key}={val} out of [0.05, 0.50]"


async def test_feedback_accept_persists_weights_to_user(client, auth_headers):
    """weights_after must be written to the user document in the DB."""
    from app.database import users_col
    from bson import ObjectId

    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "accept"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    expected = resp.json()["weights_after"]

    me = await client.get("/auth/me", headers=auth_headers)
    user_raw = await users_col().find_one({"_id": ObjectId(me.json()["user_id"])})
    stored = user_raw.get("weights", {})

    for key in ("aptitude", "personality_fit", "nlp_similarity", "market_demand"):
        assert stored[key] == pytest.approx(expected[key], abs=1e-5)


async def test_feedback_event_persisted_to_db(client, auth_headers):
    from app.database import feedback_col

    rec_id = await _generate_and_get_first_rec_id(client, auth_headers)
    resp = await client.post("/feedback/",
                             json={"recommendation_id": rec_id, "action": "reject"},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text

    me = await client.get("/auth/me", headers=auth_headers)
    uid = me.json()["user_id"]
    doc = await feedback_col().find_one({"user_id": uid, "recommendation_id": rec_id})
    assert doc is not None
    assert doc["action"] == "reject"
