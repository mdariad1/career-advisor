from fastapi import APIRouter, Depends
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Return the user's aggregated psychometric profile and current weight vector."""
    raise NotImplementedError


@router.get("/weights")
async def get_weights(current_user: dict = Depends(get_current_user)):
    raise NotImplementedError


@router.delete("/", status_code=204)
async def delete_account(current_user: dict = Depends(get_current_user)):
    """GDPR Article 17 — cascade-delete user and user_demographics documents."""
    raise NotImplementedError
