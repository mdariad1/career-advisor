"""Feedback route — accept/reject signal with online weight update.

Weight update (accept only):
  1. Identify the top-contributing SHAP factor for the accepted recommendation.
  2. Bump that weight by α = 0.025.
  3. Re-normalise all four weights to sum to 1.0.
  4. Clamp each weight to [0.05, 0.50], then re-normalise once more.
  5. Persist the new weights to users.weights and record a FeedbackDocument.

Reject: log the event only — no weight change.
"""
from __future__ import annotations

from datetime import datetime, UTC

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from ..database import feedback_col, recommendations_col, users_col
from ..dependencies import get_current_user

router = APIRouter()

_ALPHA = 0.025
_W_MIN = 0.05
_W_MAX = 0.50
_WEIGHT_KEYS = ["aptitude", "personality_fit", "nlp_similarity", "market_demand"]
_DEFAULT_WEIGHTS: dict[str, float] = {
    "aptitude": 0.25,
    "personality_fit": 0.30,
    "nlp_similarity": 0.25,
    "market_demand": 0.20,
}


# ── Schema ────────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    recommendation_id: str
    action: str  # accept | reject

    @field_validator("action")
    @classmethod
    def _validate_action(cls, v: str) -> str:
        if v not in ("accept", "reject"):
            raise ValueError("action must be 'accept' or 'reject'")
        return v


# ── Weight update ─────────────────────────────────────────────────────────────

def _update_weights(weights: dict, top_factor: str) -> dict:
    """Bump top_factor by α, normalise to sum=1.0, clamp to [W_MIN, W_MAX]."""
    w = {k: float(weights.get(k, _DEFAULT_WEIGHTS[k])) for k in _WEIGHT_KEYS}
    w[top_factor] += _ALPHA

    # First normalise
    total = sum(w.values())
    w = {k: v / total for k, v in w.items()}

    # Clamp
    w = {k: max(_W_MIN, min(_W_MAX, v)) for k, v in w.items()}

    # Re-normalise after clamping
    total = sum(w.values())
    return {k: round(v / total, 6) for k, v in w.items()}


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_200_OK)
async def submit_feedback(body: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Record accept/reject for a recommendation; accept triggers a weight update."""
    uid = current_user["user_id"]

    # Validate recommendation exists and belongs to this user
    try:
        rec_oid = ObjectId(body.recommendation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid recommendation_id",
        )

    rec = await recommendations_col().find_one({"_id": rec_oid, "user_id": uid})
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    # Load current weights
    user = await users_col().find_one({"_id": ObjectId(uid)}, {"weights": 1})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    weights_before: dict = user.get("weights") or _DEFAULT_WEIGHTS

    # Determine highest-contributing SHAP factor
    contributions: dict = rec.get("contributions", {})
    top_factor = max(contributions, key=lambda k: contributions[k]) if contributions else "aptitude"

    # Update weights on accept
    if body.action == "accept":
        weights_after = _update_weights(weights_before, top_factor)
        await users_col().update_one(
            {"_id": ObjectId(uid)},
            {"$set": {"weights": weights_after, "updated_at": datetime.now(UTC)}},
        )
    else:
        weights_after = dict(weights_before)

    # Persist feedback event
    await feedback_col().insert_one({
        "user_id": uid,
        "recommendation_id": body.recommendation_id,
        "action": body.action,
        "top_factor": top_factor,
        "weights_before": weights_before,
        "weights_after": weights_after,
        "created_at": datetime.now(UTC),
    })

    return {
        "action": body.action,
        "top_factor": top_factor,
        "weights_before": weights_before,
        "weights_after": weights_after,
    }
