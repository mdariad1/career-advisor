from __future__ import annotations

from datetime import datetime, UTC
from pydantic import Field
from .common import MongoModel, PyObjectId


class SessionDocument(MongoModel):
    """sessions collection — server-side refresh-token revocation list."""

    user_id: PyObjectId
    token_hash: str        # SHA-256 of the refresh token
    expires_at: datetime   # TTL index on this field
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
