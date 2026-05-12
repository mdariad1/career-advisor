"""Live connectivity and model round-trip tests against the Atlas cluster."""
import pytest
from bson import ObjectId


# ── Connection ────────────────────────────────────────────────────────────────

async def test_ping():
    """Verify we can reach the Atlas cluster."""
    from app.database import ping_db
    result = await ping_db()
    assert result.get("ok") == 1.0


async def test_list_collections():
    """Ensure all collections exist in career_db after index initialisation."""
    from app.database import get_db, ensure_indexes
    await ensure_indexes()
    db = get_db()
    names = set(await db.list_collection_names())
    expected = {
        "users", "user_demographics", "results", "nlp_analysis", "weights",
        "recommendations", "jobs_snapshot", "feedback", "sessions",
        "career_archetypes", "surveys", "bias_audit",
    }
    missing = expected - names
    assert not missing, f"Missing collections: {missing}"


# ── Model round-trips ─────────────────────────────────────────────────────────

async def test_user_insert_and_fetch():
    """Insert a UserDocument, fetch it back, verify field fidelity, then clean up."""
    from app.database import users_col
    from app.models.user import UserDocument

    col = users_col()
    # Remove any leftover probe document from a previous run
    await col.delete_many({"email": "pytest_probe@example.com"})

    user = UserDocument(
        email="pytest_probe@example.com",
        hashed_password="$2b$12$placeholder",
        full_name="Pytest Probe",
    )
    result = await col.insert_one(user.model_dump_mongo())
    inserted_id = result.inserted_id

    raw = await col.find_one({"_id": inserted_id})
    assert raw is not None
    assert raw["email"] == "pytest_probe@example.com"
    assert raw["weights"]["aptitude"] == pytest.approx(0.25)

    # round-trip back through the model
    fetched = UserDocument(**{**raw, "_id": str(raw["_id"])})
    assert fetched.full_name == "Pytest Probe"
    assert fetched.weights.personality_fit == pytest.approx(0.30)

    await col.delete_one({"_id": inserted_id})


async def test_weights_document():
    """Insert a WeightsDocument with custom values and verify it round-trips."""
    from app.database import weights_col
    from app.models.weights import WeightsDocument

    col = weights_col()
    uid = str(ObjectId())
    wdoc = WeightsDocument(
        user_id=uid,
        aptitude=0.35,
        personality_fit=0.30,
        nlp_similarity=0.20,
        market_demand=0.15,
    )
    result = await col.insert_one(wdoc.model_dump_mongo())
    inserted_id = result.inserted_id

    raw = await col.find_one({"_id": inserted_id})
    assert raw["aptitude"] == pytest.approx(0.35)
    assert raw["market_demand"] == pytest.approx(0.15)

    await col.delete_one({"_id": inserted_id})


async def test_nlp_analysis_document():
    """Insert an NlpAnalysisDocument (stub embedding) and fetch it back."""
    from app.database import nlp_analysis_col
    from app.models.nlp_analysis import NlpAnalysisDocument

    col = nlp_analysis_col()
    uid = str(ObjectId())
    sid = str(ObjectId())
    doc = NlpAnalysisDocument(
        user_id=uid,
        session_id=sid,
        raw_text="I love solving complex engineering problems.",
        embedding=[0.1] * 384,
        labels=["analytical", "technical"],
        label_scores={"analytical": 0.82, "technical": 0.76},
        status="done",
    )
    result = await col.insert_one(doc.model_dump_mongo())
    inserted_id = result.inserted_id

    raw = await col.find_one({"_id": inserted_id})
    assert raw["status"] == "done"
    assert len(raw["embedding"]) == 384
    assert "analytical" in raw["labels"]

    await col.delete_one({"_id": inserted_id})


async def test_jobs_snapshot_document():
    """Insert a JobSnapshotDocument and verify it round-trips cleanly."""
    from app.database import jobs_snapshot_col
    from app.models.jobs_snapshot import JobSnapshotDocument

    col = jobs_snapshot_col()
    await col.delete_many({"job_id": "pytest-job-001"})  # clean any pre-existing

    job = JobSnapshotDocument(
        job_id="pytest-job-001",
        title="Software Engineer",
        company="ACME Corp",
        industry="technology",
        country_code="GB",
        skills=["Python", "Data Analysis"],
    )
    result = await col.insert_one(job.model_dump_mongo())
    inserted_id = result.inserted_id

    raw = await col.find_one({"job_id": "pytest-job-001"})
    assert raw is not None
    assert raw["company"] == "ACME Corp"
    assert "Python" in raw["skills"]

    await col.delete_one({"_id": inserted_id})
