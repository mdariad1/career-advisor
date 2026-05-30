"""Profile route integration tests — live Atlas cluster."""
import pytest
from httpx import AsyncClient, ASGITransport

# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="session")
async def client(app, seeded_surveys):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Probe user ────────────────────────────────────────────────────────────────

TEST_EMAIL = "pytest_profile_probe@example.com"
TEST_PASSWORD = "Profile1234!"
TEST_NAME = "Profile Probe"


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
async def cleanup_profile_user(client, auth_tokens):
    yield
    from app.database import nlp_analysis_col, results_col, sessions_col, users_col
    raw = await users_col().find_one({"email": TEST_EMAIL})
    if raw:
        uid = str(raw["_id"])
        await results_col().delete_many({"user_id": uid})
        await nlp_analysis_col().delete_many({"user_id": uid})
        await sessions_col().delete_many({"user_id": uid})
        await users_col().delete_one({"_id": raw["_id"]})


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _start_and_submit_aptitude(client, headers, count=5) -> float:
    """Start + submit an aptitude survey with all correct answers; return score."""
    from app.database import surveys_col
    from bson import ObjectId

    resp = await client.post("/survey/start",
                             json={"survey_type": "aptitude", "count": count},
                             headers=headers)
    assert resp.status_code == 201, resp.text
    start = resp.json()

    ids = [ObjectId(q["id"]) for q in start["questions"]]
    docs = await surveys_col().find({"_id": {"$in": ids}}).to_list(length=count)
    q_map = {str(d["_id"]): d["answer_index"] for d in docs}
    correct = [q_map[q["id"]] for q in start["questions"]]

    resp = await client.post("/survey/submit",
                             json={"session_id": start["session_id"], "answers": correct},
                             headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["score"]


async def _start_and_submit_personality(client, headers) -> dict:
    """Start + submit a personality survey with all-neutral answers; return ocean dict."""
    resp = await client.post("/survey/start",
                             json={"survey_type": "personality"},
                             headers=headers)
    assert resp.status_code == 201, resp.text
    start = resp.json()

    neutral = [2] * start["question_count"]
    resp = await client.post("/survey/submit",
                             json={"session_id": start["session_id"], "answers": neutral},
                             headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["ocean_vector"]


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_profile_unauthenticated_returns_401(client):
    resp = await client.get("/profile/")
    assert resp.status_code in (401, 403)


async def test_weights_unauthenticated_returns_401(client):
    resp = await client.get("/profile/weights")
    assert resp.status_code in (401, 403)


async def test_profile_defaults_for_new_user(client, auth_headers):
    resp = await client.get("/profile/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == TEST_EMAIL
    assert data["full_name"] == TEST_NAME
    # Fresh user — no assessments yet
    assert data["aptitude_score"] is None
    assert data["ocean_vector"] is None
    assert data["nlp_labels"] is None
    assert data["assessments_completed"]["aptitude"] is False
    assert data["assessments_completed"]["personality"] is False
    assert data["assessments_completed"]["open_text"] is False


async def test_weights_returns_defaults_for_new_user(client, auth_headers):
    resp = await client.get("/profile/weights", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    w = resp.json()
    assert w["aptitude"] == pytest.approx(0.25)
    assert w["personality_fit"] == pytest.approx(0.30)
    assert w["nlp_similarity"] == pytest.approx(0.25)
    assert w["market_demand"] == pytest.approx(0.20)


async def test_profile_reflects_aptitude_score(client, auth_headers):
    score = await _start_and_submit_aptitude(client, auth_headers, count=5)
    resp = await client.get("/profile/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["aptitude_score"] == pytest.approx(score)
    assert data["assessments_completed"]["aptitude"] is True


async def test_profile_reflects_ocean_vector(client, auth_headers):
    ocean = await _start_and_submit_personality(client, auth_headers)
    resp = await client.get("/profile/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ocean_vector"] is not None
    dims = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    for dim in dims:
        assert dim in data["ocean_vector"]
        assert data["ocean_vector"][dim] == pytest.approx(ocean[dim])
    assert data["assessments_completed"]["personality"] is True


async def test_profile_weights_field_present(client, auth_headers):
    """Profile response must include the weights sub-document."""
    resp = await client.get("/profile/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "weights" in data
    w = data["weights"]
    assert "aptitude" in w
    assert "personality_fit" in w
    assert "nlp_similarity" in w
    assert "market_demand" in w


async def test_delete_account_returns_204(client, auth_tokens):
    """Register a throwaway user, delete their account, verify 204 and user gone."""
    from app.database import users_col

    tmp_email = "pytest_delete_probe@example.com"
    reg = await client.post("/auth/register", json={
        "email": tmp_email,
        "password": "Delete1234!",
        "full_name": "Delete Probe",
    })
    assert reg.status_code == 201, reg.text
    tmp_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    resp = await client.delete("/profile/", headers=tmp_headers)
    assert resp.status_code == 204

    # User document should be gone
    assert await users_col().find_one({"email": tmp_email}) is None


async def test_delete_account_cascades_sessions(client):
    """After account deletion, sessions for that user must also be removed."""
    from app.database import sessions_col, users_col
    from bson import ObjectId

    tmp_email = "pytest_cascade_probe@example.com"
    reg = await client.post("/auth/register", json={
        "email": tmp_email,
        "password": "Cascade1234!",
        "full_name": "Cascade Probe",
    })
    assert reg.status_code == 201, reg.text
    tokens = reg.json()
    tmp_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Find the user to check sessions
    raw = await users_col().find_one({"email": tmp_email})
    uid = str(raw["_id"])

    await client.delete("/profile/", headers=tmp_headers)

    remaining = await sessions_col().count_documents({"user_id": uid})
    assert remaining == 0
