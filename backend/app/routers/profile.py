"""Profile routes — aggregated psychometric profile and weight vector."""
from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import (
    nlp_analysis_col,
    results_col,
    sessions_col,
    user_demographics_col,
    users_col,
)
from ..dependencies import get_current_user

router = APIRouter()

OCEAN_DIMS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

_DEFAULT_WEIGHTS = {
    "aptitude": 0.25,
    "personality_fit": 0.30,
    "nlp_similarity": 0.25,
    "market_demand": 0.20,
}


@router.get("/")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Return the user's aggregated psychometric profile and current weight vector."""
    user = await users_col().find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    ocean_vector = user.get("ocean_vector")
    ocean_dict = dict(zip(OCEAN_DIMS, ocean_vector)) if ocean_vector else None

    # Most recent completed NLP analysis (if any)
    nlp_labels: list[str] | None = user.get("nlp_labels")
    nlp_label_scores: dict[str, float] | None = None
    nlp_doc = await nlp_analysis_col().find_one(
        {"user_id": current_user["user_id"], "status": "done"},
        sort=[("processed_at", -1)],
    )
    if nlp_doc:
        nlp_labels = nlp_doc.get("labels") or nlp_labels
        nlp_label_scores = nlp_doc.get("label_scores")

    weights = user.get("weights") or _DEFAULT_WEIGHTS

    return {
        "user_id": current_user["user_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "aptitude_score": user.get("aptitude_score"),
        "ocean_vector": ocean_dict,
        "nlp_labels": nlp_labels,
        "nlp_label_scores": nlp_label_scores,
        "weights": weights,
        "assessments_completed": {
            "aptitude": user.get("aptitude_score") is not None,
            "personality": ocean_vector is not None,
            "open_text": nlp_labels is not None,
        },
    }


@router.get("/weights")
async def get_weights(current_user: dict = Depends(get_current_user)):
    """Return the user's current scoring weight vector."""
    user = await users_col().find_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"weights": 1},
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    weights = user.get("weights") or {}
    return {
        "aptitude": weights.get("aptitude", _DEFAULT_WEIGHTS["aptitude"]),
        "personality_fit": weights.get("personality_fit", _DEFAULT_WEIGHTS["personality_fit"]),
        "nlp_similarity": weights.get("nlp_similarity", _DEFAULT_WEIGHTS["nlp_similarity"]),
        "market_demand": weights.get("market_demand", _DEFAULT_WEIGHTS["market_demand"]),
    }


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: dict = Depends(get_current_user)):
    """GDPR Article 17 — cascade-delete user and all associated data."""
    uid = current_user["user_id"]

    await sessions_col().delete_many({"user_id": uid})
    await results_col().delete_many({"user_id": uid})
    await nlp_analysis_col().delete_many({"user_id": uid})
    await user_demographics_col().delete_one({"user_id": uid})
    await users_col().delete_one({"_id": ObjectId(uid)})
