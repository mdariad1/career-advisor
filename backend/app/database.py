from __future__ import annotations

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ServerSelectionTimeoutError
from .config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None

# Atlas SRV URIs don't always embed the DB name before '?'.
# We always address the DB explicitly so the code is URI-format agnostic.
DB_NAME = "career_db"


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=5_000,
            connectTimeoutMS=10_000,
            socketTimeoutMS=30_000,
            # Allows Motor to be used in async test contexts without a running loop
            uuidRepresentation="standard",
        )
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[DB_NAME]


def get_collection(name: str) -> AsyncIOMotorCollection:
    return get_db()[name]


async def ping_db() -> dict:
    """Return server info dict if reachable, raise ServerSelectionTimeoutError otherwise."""
    result = await get_client()[DB_NAME].command("ping")
    return result


# ── Typed collection accessors ────────────────────────────────────────────────
# Import lazily inside functions to avoid circular imports at module load time.

def users_col() -> AsyncIOMotorCollection:
    return get_collection("users")

def user_demographics_col() -> AsyncIOMotorCollection:
    return get_collection("user_demographics")

def results_col() -> AsyncIOMotorCollection:
    return get_collection("results")

def nlp_analysis_col() -> AsyncIOMotorCollection:
    return get_collection("nlp_analysis")

def weights_col() -> AsyncIOMotorCollection:
    return get_collection("weights")

def recommendations_col() -> AsyncIOMotorCollection:
    return get_collection("recommendations")

def jobs_snapshot_col() -> AsyncIOMotorCollection:
    return get_collection("jobs_snapshot")

def feedback_col() -> AsyncIOMotorCollection:
    return get_collection("feedback")

def sessions_col() -> AsyncIOMotorCollection:
    return get_collection("sessions")

def career_archetypes_col() -> AsyncIOMotorCollection:
    return get_collection("career_archetypes")

def surveys_col() -> AsyncIOMotorCollection:
    return get_collection("surveys")

def bias_audit_col() -> AsyncIOMotorCollection:
    return get_collection("bias_audit")


async def ensure_indexes() -> None:
    """Create all collections and their indexes.

    Safe to call repeatedly — MongoDB ignores duplicate index creation.
    On Atlas, collections are created lazily; calling this at startup
    guarantees they exist before any query runs.
    """
    db = get_db()

    await db["users"].create_index("email", unique=True)

    await db["user_demographics"].create_index("user_id", unique=True)

    await db["results"].create_index("user_id")
    await db["results"].create_index([("user_id", 1), ("survey_type", 1)])

    await db["nlp_analysis"].create_index("user_id")
    await db["nlp_analysis"].create_index([("user_id", 1), ("session_id", 1)])

    await db["weights"].create_index("user_id", unique=True)

    await db["recommendations"].create_index("user_id")
    await db["recommendations"].create_index([("user_id", 1), ("created_at", -1)])

    await db["jobs_snapshot"].create_index("job_id", unique=True)
    await db["jobs_snapshot"].create_index([("industry", 1), ("country_code", 1)])
    await db["jobs_snapshot"].create_index("synced_at")

    await db["feedback"].create_index("user_id")
    await db["feedback"].create_index("recommendation_id")

    await db["sessions"].create_index("user_id")
    await db["sessions"].create_index("token_hash", unique=True)
    await db["sessions"].create_index("expires_at", expireAfterSeconds=0)

    await db["career_archetypes"].create_index("career_id", unique=True)

    await db["surveys"].create_index("survey_type")
    await db["surveys"].create_index([("survey_type", 1), ("grade", 1)])

    await db["bias_audit"].create_index([("created_at", -1)])

    logger.info("MongoDB indexes ensured for all collections")


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")

