from fastapi import APIRouter, Depends
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """Compute and return top-5 career matches with SHAP breakdowns and matched live job listings."""
    raise NotImplementedError


@router.get("/{recommendation_id}")
async def get_recommendation(recommendation_id: str, current_user: dict = Depends(get_current_user)):
    raise NotImplementedError
