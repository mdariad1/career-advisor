from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from .config import settings

DB_NAME = "career_db"
_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=5_000,
            uuidRepresentation="standard",
        )
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[DB_NAME]


def nlp_analysis_col() -> AsyncIOMotorCollection:
    return get_db()["nlp_analysis"]
