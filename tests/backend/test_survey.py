"""Survey route integration tests — live Atlas cluster."""
import pytest
from httpx import AsyncClient, ASGITransport

# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="session")
async def client(app, seeded_surveys):
    """HTTP client; depends on seeded_surveys so the question bank is ready first."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Registered user shared across survey tests ────────────────────────────────

TEST_EMAIL = "pytest_survey_probe@example.com"
TEST_PASSWORD = "Survey1234!"
TEST_NAME = "Survey Probe"


@pytest.fixture(scope="session")
async def auth_tokens(client):
    """Register a probe user and return their token pair."""
    from app.database import sessions_col, users_col

    # Clean up any leftover from a previous run
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
async def cleanup_survey_user(client, auth_tokens):
    """Delete the probe user and all their data at session end."""
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

async def _start(client, headers, survey_type, count=None) -> dict:
    payload = {"survey_type": survey_type}
    if count is not None:
        payload["count"] = count
    resp = await client.post("/survey/start", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Aptitude tests ────────────────────────────────────────────────────────────

async def test_aptitude_start_returns_questions(client, auth_headers):
    data = await _start(client, auth_headers, "aptitude", count=10)
    assert data["survey_type"] == "aptitude"
    assert data["question_count"] == 10
    assert len(data["questions"]) == 10
    q = data["questions"][0]
    assert "id" in q and "question" in q and "choices" in q
    assert "answer_index" not in q           # must not leak correct answer


async def test_aptitude_questions_have_four_choices(client, auth_headers):
    data = await _start(client, auth_headers, "aptitude", count=5)
    for q in data["questions"]:
        assert len(q["choices"]) == 4


async def test_aptitude_submit_perfect_score(client, auth_headers):
    """Submit all correct answers and verify score == 1.0."""
    from app.database import surveys_col
    from bson import ObjectId

    start = await _start(client, auth_headers, "aptitude", count=5)
    session_id = start["session_id"]

    # Fetch correct answer_index values directly from DB
    ids = [ObjectId(q["id"]) for q in start["questions"]]
    docs = await surveys_col().find({"_id": {"$in": ids}}).to_list(length=5)
    q_map = {str(d["_id"]): d["answer_index"] for d in docs}
    correct_answers = [q_map[q["id"]] for q in start["questions"]]

    resp = await client.post("/survey/submit",
                             json={"session_id": session_id, "answers": correct_answers},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["score"] == pytest.approx(1.0)
    assert data["correct"] == 5
    assert data["total"] == 5


async def test_aptitude_submit_zero_score(client, auth_headers):
    """Submit all wrong answers and verify score == 0.0."""
    start = await _start(client, auth_headers, "aptitude", count=5)
    session_id = start["session_id"]

    from app.database import surveys_col
    from bson import ObjectId

    ids = [ObjectId(q["id"]) for q in start["questions"]]
    docs = await surveys_col().find({"_id": {"$in": ids}}).to_list(length=5)
    q_map = {str(d["_id"]): d["answer_index"] for d in docs}

    # Pick a wrong answer for each question
    wrong_answers = []
    for q in start["questions"]:
        correct = q_map[q["id"]]
        wrong = (correct + 1) % len(q["choices"])
        wrong_answers.append(wrong)

    resp = await client.post("/survey/submit",
                             json={"session_id": session_id, "answers": wrong_answers},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["score"] == pytest.approx(0.0)


async def test_aptitude_submit_updates_user_profile(client, auth_headers):
    """Completed aptitude survey must update aptitude_score on the user document."""
    from app.database import surveys_col, users_col
    from bson import ObjectId

    start = await _start(client, auth_headers, "aptitude", count=5)
    ids = [ObjectId(q["id"]) for q in start["questions"]]
    docs = await surveys_col().find({"_id": {"$in": ids}}).to_list(length=5)
    q_map = {str(d["_id"]): d["answer_index"] for d in docs}
    correct_answers = [q_map[q["id"]] for q in start["questions"]]

    await client.post("/survey/submit",
                      json={"session_id": start["session_id"], "answers": correct_answers},
                      headers=auth_headers)

    resp = await client.get("/auth/me", headers=auth_headers)
    user_id = resp.json()["user_id"]
    user_raw = await users_col().find_one({"_id": ObjectId(user_id)})
    assert user_raw["aptitude_score"] is not None
    assert 0.0 <= user_raw["aptitude_score"] <= 1.0


async def test_aptitude_double_submit_rejected(client, auth_headers):
    """Submitting the same session twice must return 409."""
    from app.database import surveys_col
    from bson import ObjectId

    start = await _start(client, auth_headers, "aptitude", count=3)
    ids = [ObjectId(q["id"]) for q in start["questions"]]
    docs = await surveys_col().find({"_id": {"$in": ids}}).to_list(length=3)
    q_map = {str(d["_id"]): d["answer_index"] for d in docs}
    answers = [q_map[q["id"]] for q in start["questions"]]

    payload = {"session_id": start["session_id"], "answers": answers}
    await client.post("/survey/submit", json=payload, headers=auth_headers)
    resp = await client.post("/survey/submit", json=payload, headers=auth_headers)
    assert resp.status_code == 409


async def test_aptitude_wrong_answer_count_rejected(client, auth_headers):
    start = await _start(client, auth_headers, "aptitude", count=5)
    resp = await client.post("/survey/submit",
                             json={"session_id": start["session_id"], "answers": [0, 1]},
                             headers=auth_headers)
    assert resp.status_code == 422


async def test_invalid_survey_type_rejected(client, auth_headers):
    resp = await client.post("/survey/start",
                             json={"survey_type": "unknown"},
                             headers=auth_headers)
    assert resp.status_code == 422


# ── Personality tests ─────────────────────────────────────────────────────────

async def test_personality_start_returns_25_questions(client, auth_headers):
    data = await _start(client, auth_headers, "personality")
    assert data["survey_type"] == "personality"
    assert data["question_count"] == 25
    assert len(data["questions"]) == 25
    # Choices must be the Likert scale (5 options)
    for q in data["questions"]:
        assert len(q["choices"]) == 5


async def test_personality_submit_produces_ocean_vector(client, auth_headers):
    start = await _start(client, auth_headers, "personality")
    # Answer 2 (Neutral) for every question → mid-range ocean vector
    neutral_answers = [2] * start["question_count"]
    resp = await client.post("/survey/submit",
                             json={"session_id": start["session_id"], "answers": neutral_answers},
                             headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["survey_type"] == "personality"
    ocean = data["ocean_vector"]
    dims = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    for dim in dims:
        assert dim in ocean
        assert 0.0 <= ocean[dim] <= 1.0


async def test_personality_submit_updates_user_profile(client, auth_headers):
    from app.database import users_col
    from bson import ObjectId

    start = await _start(client, auth_headers, "personality")
    await client.post("/survey/submit",
                      json={"session_id": start["session_id"],
                            "answers": [4] * start["question_count"]},
                      headers=auth_headers)

    resp = await client.get("/auth/me", headers=auth_headers)
    user_id = resp.json()["user_id"]
    user_raw = await users_col().find_one({"_id": ObjectId(user_id)})
    assert user_raw["ocean_vector"] is not None
    assert len(user_raw["ocean_vector"]) == 5


# ── Open-text tests ───────────────────────────────────────────────────────────

async def test_open_text_start_returns_no_questions(client, auth_headers):
    data = await _start(client, auth_headers, "open_text")
    assert data["survey_type"] == "open_text"
    assert data["question_count"] == 0
    assert data["questions"] == []


async def test_open_text_submit_returns_pending(client, auth_headers):
    start = await _start(client, auth_headers, "open_text")
    resp = await client.post("/survey/submit-text",
                             json={"session_id": start["session_id"],
                                   "response_text": "I enjoy solving complex engineering problems."},
                             headers=auth_headers)
    assert resp.status_code == 202, resp.text
    data = resp.json()
    assert data["status"] == "pending"
    assert data["session_id"] == start["session_id"]


async def test_open_text_status_returns_pending(client, auth_headers):
    start = await _start(client, auth_headers, "open_text")
    await client.post("/survey/submit-text",
                      json={"session_id": start["session_id"],
                            "response_text": "I love creative design and building things."},
                      headers=auth_headers)

    resp = await client.get(f"/survey/status/{start['session_id']}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] in ("pending", "done")


async def test_open_text_session_cannot_use_mcq_submit(client, auth_headers):
    start = await _start(client, auth_headers, "open_text")
    resp = await client.post("/survey/submit",
                             json={"session_id": start["session_id"], "answers": []},
                             headers=auth_headers)
    assert resp.status_code == 422


async def test_mcq_session_cannot_use_text_submit(client, auth_headers):
    start = await _start(client, auth_headers, "aptitude", count=3)
    resp = await client.post("/survey/submit-text",
                             json={"session_id": start["session_id"],
                                   "response_text": "some text"},
                             headers=auth_headers)
    assert resp.status_code == 422
