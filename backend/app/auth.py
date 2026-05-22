from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, UTC

import bcrypt
from jose import jwt, JWTError

from .config import settings

_BCRYPT_ROUNDS = 12
_ACCESS_TYPE = "access"
_REFRESH_TYPE = "refresh"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, role: str = "user") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "type": _ACCESS_TYPE,
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": _REFRESH_TYPE,
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm="HS256")


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token. Raises JWTError on any failure."""
    payload = jwt.decode(token, settings.jwt_refresh_secret, algorithms=["HS256"])
    if payload.get("type") != _REFRESH_TYPE:
        raise JWTError("Not a refresh token")
    return payload


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
