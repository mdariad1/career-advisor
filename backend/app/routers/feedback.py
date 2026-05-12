from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from ..dependencies import get_current_user

router = APIRouter()


class FeedbackRequest(BaseModel):
    recommendation_id: str
    action: str  # accept | reject


@router.post("/", status_code=status.HTTP_200_OK)
async def submit_feedback(body: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """
    Accept: trigger weight update (α=0.025 on highest-contributing factor,
    then re-normalise). Reject: log event only.
    Returns updated weight vector.
    """
    raise NotImplementedError
