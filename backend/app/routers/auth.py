from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

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


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    raise NotImplementedError


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    raise NotImplementedError


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    raise NotImplementedError


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    raise NotImplementedError
