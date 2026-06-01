"""Recommendations route integration tests — live Atlas cluster."""
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

TEST_EMAIL = "pytest_reco_probe@example.com"
TEST_PASSWORD = "Reco1234!"
TEST_NAME = "Reco Probe"


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
async def cleanup_reco_user(client, auth_tokens):
    yield
    from app.database import nlp_analysis_col, recommendations_col, results_col, sessions_col, users_col
    raw = await users_col().find_one({"email": TEST_EMAIL})
    if raw:
        uid = str(raw["_id"])
        await recommendations_col().delete_many({"user_id": uid})
        await results_col().delete_many({"user_id": uid})
        await nlp_analysis_col().delete_many({"user_id": uid})
        await sessions_col().delete_many({"user_id": uid})
        await users_col().delete_one({"_id": raw["_id"]})


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_recommendations_get_unauthenticated(client):
    resp = await client.get("/recommendations/")
    assert resp.status_code in (401, 403)


async def test_recommendations_post_unauthenticated(client):
    resp = await client.post("/recommendations/")
    assert resp.status_code in (401, 403)


async def test_recommendations_get_before_generate_returns_404(client, auth_headers):
    """GET before any POST must return 404, not crash."""
    resp = await client.get("/recommendations/", headers=auth_headers)
    assert resp.status_code == 404


async def test_recommendations_post_returns_five_items(client, auth_headers):
    resp = await client.post("/recommendations/", headers=auth_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 5


async def test_recommendations_fields_present(client, auth_headers):
    resp = await client.post("/recommendations/", headers=auth_headers)
    assert resp.status_code == 201, resp.text
    rec = resp.json()["recommendations"][0]
    for field in ("id", "career_id", "career_title", "score", "contributions", "explanation"):
        assert field in rec, f"missing field: {field}"


async def test_recommendations_shap_sums_to_score(client, auth_headers):
    """Each record's SHAP contributions must sum to its composite score."""
    resp = await client.post("/recommendations/", headers=auth_headers)
    assert resp.status_code == 201, resp.text
    for rec in resp.json()["recommendations"]:
        total = sum(rec["contributions"].values())
        assert total == pytest.approx(rec["score"], abs=1e-3)


async def test_recommendations_all_scores_in_range(client, auth_headers):
    resp = await client.post("/recommendations/", headers=auth_headers)
    assert resp.status_code == 201, resp.text
    for rec in resp.json()["recommendations"]:
        assert 0.0 <= rec["score"] <= 1.0


async def test_recommendations_sorted_descending(client, auth_headers):
    resp = await client.post("/recommendations/", headers=auth_headers)
    assert resp.status_code == 201, resp.text
    scores = [r["score"] for r in resp.json()["recommendations"]]
    assert scores == sorted(scores, reverse=True)


async def test_recommendations_get_returns_cached_results(client, auth_headers):
    """GET after POST must return the same career IDs (no recompute)."""
    post_resp = await client.post("/recommendations/", headers=auth_headers)
    assert post_resp.status_code == 201, post_resp.text
    post_ids = {r["career_id"] for r in post_resp.json()["recommendations"]}

    get_resp = await client.get("/recommendations/", headers=auth_headers)
    assert get_resp.status_code == 200, get_resp.text
    get_ids = {r["career_id"] for r in get_resp.json()["recommendations"]}

    assert post_ids == get_ids


async def test_recommendations_get_single_by_id(client, auth_headers):
    post_resp = await client.post("/recommendations/", headers=auth_headers)
    assert post_resp.status_code == 201, post_resp.text
    first = post_resp.json()["recommendations"][0]
    rec_id = first["id"]

    resp = await client.get(f"/recommendations/{rec_id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["career_id"] == first["career_id"]
    assert data["score"] == pytest.approx(first["score"])


async def test_second_post_replaces_first(client, auth_headers):
    """A second POST must replace old recommendations, not accumulate them."""
    await client.post("/recommendations/", headers=auth_headers)
    await client.post("/recommendations/", headers=auth_headers)

    get_resp = await client.get("/recommendations/", headers=auth_headers)
    assert get_resp.status_code == 200, get_resp.text
    assert len(get_resp.json()["recommendations"]) == 5


async def test_recommendations_contributions_keys(client, auth_headers):
    resp = await client.post("/recommendations/", headers=auth_headers)
    assert resp.status_code == 201, resp.text
    for rec in resp.json()["recommendations"]:
        c = rec["contributions"]
        assert set(c.keys()) == {"aptitude", "personality_fit", "nlp_similarity", "market_demand"}


async def test_recommendations_invalid_id_returns_422(client, auth_headers):
    resp = await client.get("/recommendations/not-a-valid-id", headers=auth_headers)
    assert resp.status_code == 422


async def test_recommendations_unknown_id_returns_404(client, auth_headers):
    from bson import ObjectId
    fake_id = str(ObjectId())
    resp = await client.get(f"/recommendations/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404
