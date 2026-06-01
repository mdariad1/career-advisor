"""Jobs route integration tests — live Atlas cluster."""
import pytest
from httpx import AsyncClient, ASGITransport

# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="session")
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
async def auth_tokens(client):
    from app.database import sessions_col, users_col

    email = "pytest_jobs_probe@example.com"
    raw = await users_col().find_one({"email": email})
    if raw:
        await sessions_col().delete_many({"user_id": str(raw["_id"])})
        await users_col().delete_one({"_id": raw["_id"]})

    resp = await client.post("/auth/register", json={
        "email": email,
        "password": "Jobs1234!",
        "full_name": "Jobs Probe",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture(scope="session")
def auth_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


@pytest.fixture(scope="session", autouse=True)
async def cleanup_jobs_user(client, auth_tokens):
    yield
    from app.database import sessions_col, users_col
    raw = await users_col().find_one({"email": "pytest_jobs_probe@example.com"})
    if raw:
        uid = str(raw["_id"])
        await sessions_col().delete_many({"user_id": uid})
        await users_col().delete_one({"_id": raw["_id"]})


# ── Seeded jobs fixture ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
async def seeded_jobs():
    """Insert a handful of test job snapshots; clean up at session end."""
    from datetime import datetime, UTC
    from app.database import jobs_snapshot_col

    col = jobs_snapshot_col()
    docs = [
        {
            "job_id": f"test_job_{i}",
            "title": f"Test Job {i}",
            "company": "Test Co",
            "industry": "technology" if i % 2 == 0 else "healthcare",
            "country_code": "GB" if i < 3 else "US",
            "skills": ["python", "sql"],
            "raw_skills": ["Python", "SQL"],
            "is_stale": False,
            "synced_at": datetime.now(UTC),
        }
        for i in range(6)
    ]
    result = await col.insert_many(docs)
    yield
    await col.delete_many({"_id": {"$in": result.inserted_ids}})


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_jobs_unauthenticated(client):
    resp = await client.get("/jobs/")
    assert resp.status_code in (401, 403)


async def test_jobs_returns_list(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)


async def test_jobs_total_reflects_seeded_count(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] >= 6


async def test_jobs_industry_filter(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/?industry=technology", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for job in data["jobs"]:
        assert job["industry"] == "technology"


async def test_jobs_country_filter(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/?country_code=GB", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    for job in resp.json()["jobs"]:
        assert job["country_code"] == "GB"


async def test_jobs_combined_filters(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/?industry=technology&country_code=GB", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    for job in resp.json()["jobs"]:
        assert job["industry"] == "technology"
        assert job["country_code"] == "GB"


async def test_jobs_limit_param(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/?limit=2", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["jobs"]) <= 2


async def test_jobs_skip_param(client, auth_headers, seeded_jobs):
    all_resp = await client.get("/jobs/?limit=100", headers=auth_headers)
    skip_resp = await client.get("/jobs/?skip=2&limit=100", headers=auth_headers)
    assert all_resp.status_code == 200 and skip_resp.status_code == 200
    # Skipping 2 should return fewer results
    assert len(skip_resp.json()["jobs"]) <= len(all_resp.json()["jobs"])


async def test_jobs_returns_skip_and_limit_in_response(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/?skip=1&limit=3", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["skip"] == 1
    assert data["limit"] == 3


async def test_jobs_empty_result_for_unknown_filter(client, auth_headers, seeded_jobs):
    resp = await client.get("/jobs/?industry=nonexistent_industry_xyz", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 0
    assert data["jobs"] == []
