"""Auth flow tests — live Atlas cluster, session-scoped event loop."""
import pytest
from httpx import AsyncClient, ASGITransport

TEST_EMAIL = "pytest_auth_probe@example.com"
TEST_PASSWORD = "S3cur3P@ssword!"
TEST_NAME = "Auth Probe"


# ---------------------------------------------------------------------------
# Session-scoped fixtures — Motor client lives for the whole session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="session")
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Per-test cleanup — depends on client so Motor client is already in session loop
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def cleanup_user(client):
    """Remove the probe user (and their sessions) before and after each test."""
    from app.database import sessions_col, user_demographics_col, users_col

    async def _delete():
        raw = await users_col().find_one({"email": TEST_EMAIL})
        if raw:
            uid = str(raw["_id"])
            await sessions_col().delete_many({"user_id": uid})
            await user_demographics_col().delete_many({"user_id": uid})
        await users_col().delete_many({"email": TEST_EMAIL})

    await _delete()
    yield
    await _delete()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _register(client) -> dict:
    resp = await client.post("/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_register_returns_tokens(client):
    data = await _register(client)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email_rejected(client):
    await _register(client)
    resp = await client.post("/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
    })
    assert resp.status_code == 409


async def test_login_valid_credentials(client):
    await _register(client)
    resp = await client.post("/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client):
    await _register(client)
    resp = await client.post("/auth/login", json={
        "email": TEST_EMAIL,
        "password": "wrong-password",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": TEST_PASSWORD,
    })
    assert resp.status_code == 401


async def test_me_with_valid_token(client):
    tokens = await _register(client)
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == TEST_EMAIL
    assert data["full_name"] == TEST_NAME


async def test_me_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code in (401, 403)  # HTTPBearer raises 403; some FastAPI versions map to 401


async def test_refresh_issues_new_tokens(client):
    tokens = await _register(client)
    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


async def test_refresh_token_rotation_revokes_old(client):
    """Using the same refresh token twice must fail on the second attempt."""
    tokens = await _register(client)
    await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


async def test_logout_revokes_session(client):
    tokens = await _register(client)
    resp = await client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 204

    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


async def test_register_with_demographics(client):
    resp = await client.post("/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
        "demographics": {
            "gender": "non-binary",
            "age_group": "18-24",
            "field_of_study": "Computer Science",
        },
    })
    assert resp.status_code == 201

    from app.database import user_demographics_col, users_col
    raw = await users_col().find_one({"email": TEST_EMAIL})
    demo = await user_demographics_col().find_one({"user_id": str(raw["_id"])})
    assert demo is not None
    assert demo["field_of_study"] == "Computer Science"
