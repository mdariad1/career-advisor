from __future__ import annotations

from datetime import datetime, timedelta, UTC

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel, EmailStr

from ..auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    sha256_hex,
    verify_password,
)
from ..config import settings
from ..database import sessions_col, user_demographics_col, users_col
from ..dependencies import get_current_user
from ..models.sessions import SessionDocument
from ..models.user import UserDocument
from ..models.user_demographics import UserDemographicsDocument

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    demographics: dict | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


def _token_pair(user_id: str, role: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id),
    )


async def _store_session(user_id: str, refresh_token: str) -> None:
    doc = SessionDocument(
        user_id=user_id,
        token_hash=sha256_hex(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    await sessions_col().insert_one(doc.model_dump_mongo())


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(body: RegisterRequest):
    col = users_col()
    if await col.find_one({"email": body.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = UserDocument(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    result = await col.insert_one(user.model_dump_mongo())
    user_id = str(result.inserted_id)

    if body.demographics:
        demo = UserDemographicsDocument(user_id=user_id, **body.demographics)
        await user_demographics_col().insert_one(demo.model_dump_mongo())

    tokens = _token_pair(user_id, "user")
    await _store_session(user_id, tokens.refresh_token)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    raw = await users_col().find_one({"email": body.email})
    if not raw or not verify_password(body.password, raw["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_id = str(raw["_id"])
    role = raw.get("role", "user")
    tokens = _token_pair(user_id, role)
    await _store_session(user_id, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = decode_refresh_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    token_hash = sha256_hex(body.refresh_token)
    session = await sessions_col().find_one({"token_hash": token_hash})
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found or expired")

    user_id = payload["sub"]
    user_raw = await users_col().find_one({"_id": ObjectId(user_id)})
    role = user_raw.get("role", "user") if user_raw else "user"

    await sessions_col().delete_one({"token_hash": token_hash})
    tokens = _token_pair(user_id, role)
    await _store_session(user_id, tokens.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    try:
        decode_refresh_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    token_hash = sha256_hex(body.refresh_token)
    await sessions_col().delete_one({"token_hash": token_hash})


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    raw = await users_col().find_one({"_id": ObjectId(current_user["user_id"])})
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "user_id": str(raw["_id"]),
        "email": raw["email"],
        "full_name": raw["full_name"],
        "role": raw.get("role", "user"),
    }
