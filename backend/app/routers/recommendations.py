"""Recommendations routes — career scoring formula and SHAP breakdown.

Scoring formula (per CLAUDE.md):
  score(career, user) = w_apt * aptitude
                      + w_pf  * personality_fit   (OCEAN cosine similarity)
                      + w_nlp * nlp_similarity     (embedding cosine > label Jaccard > 0.5)
                      + w_md  * market_demand      (archetype.market_demand_seed)

SHAP breakdown is analytically exact: each term is the weighted component contribution,
and the four contributions sum exactly to the composite score.
"""
from __future__ import annotations

import math
from datetime import datetime, UTC
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import (
    career_archetypes_col,
    jobs_snapshot_col,
    nlp_analysis_col,
    recommendations_col,
    users_col,
)
from ..dependencies import get_current_user

router = APIRouter()

TOP_N = 5

_DEFAULT_WEIGHTS: dict[str, float] = {
    "aptitude": 0.25,
    "personality_fit": 0.30,
    "nlp_similarity": 0.25,
    "market_demand": 0.20,
}


# ── Maths helpers ─────────────────────────────────────────────────────────────

def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_career(
    aptitude: float,
    user_ocean: list[float] | None,
    user_embedding: list[float],
    user_labels: list[str],
    archetype: dict,
    weights: dict,
) -> tuple[float, dict[str, float]]:
    """Return (composite_score, shap_contributions) for one career archetype."""

    # Personality fit: OCEAN cosine similarity, neutral 0.5 if not assessed
    arch_ocean = archetype.get("ocean_vector") or []
    pf = _cosine(user_ocean or [], arch_ocean) if (user_ocean and arch_ocean) else 0.5

    # NLP similarity: embedding cosine > label Jaccard > neutral 0.5
    arch_centroid: list[float] = archetype.get("nlp_centroid") or []
    arch_labels: list[str] = archetype.get("thematic_labels") or []
    if user_embedding and arch_centroid and len(user_embedding) == len(arch_centroid):
        nlp = _cosine(user_embedding, arch_centroid)
    elif user_labels and arch_labels:
        nlp = _jaccard(user_labels, arch_labels)
    else:
        nlp = 0.5

    md = float(archetype.get("market_demand_seed", 0.5))

    w = weights
    contributions = {
        "aptitude":        round(w["aptitude"]        * aptitude, 4),
        "personality_fit": round(w["personality_fit"] * pf,       4),
        "nlp_similarity":  round(w["nlp_similarity"]  * nlp,      4),
        "market_demand":   round(w["market_demand"]   * md,       4),
    }
    score = round(sum(contributions.values()), 4)
    return score, contributions


def _explanation(career_title: str, score: float, c: dict[str, float]) -> str:
    return (
        f"{career_title} is a {round(score * 100)}% match for your profile. "
        f"Aptitude contributes {c['aptitude']:.3f}, "
        f"personality fit {c['personality_fit']:.3f}, "
        f"skills similarity {c['nlp_similarity']:.3f}, "
        f"and market demand {c['market_demand']:.3f}."
    )


# ── Serialisation helper ──────────────────────────────────────────────────────

def _serialise(doc: dict) -> dict[str, Any]:
    """Convert a raw MongoDB document to a JSON-safe dict."""
    out = {k: v for k, v in doc.items() if k != "_id"}
    out["id"] = str(doc["_id"])
    if isinstance(out.get("created_at"), datetime):
        out["created_at"] = out["created_at"].isoformat()
    return out


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def generate_recommendations(current_user: dict = Depends(get_current_user)):
    """Score all career archetypes against the user's profile and persist the top 5."""
    uid = current_user["user_id"]

    user = await users_col().find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    archetypes = await career_archetypes_col().find({}).to_list(length=200)
    if not archetypes:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Career archetypes not seeded — run seed_archetypes() first",
        )

    # User assessment data
    user_ocean: list[float] | None = user.get("ocean_vector")
    aptitude: float = user.get("aptitude_score") or 0.5
    weights: dict = user.get("weights") or _DEFAULT_WEIGHTS

    # Most recent completed NLP analysis
    nlp_doc = await nlp_analysis_col().find_one(
        {"user_id": uid, "status": "done"},
        sort=[("processed_at", -1)],
    )
    user_embedding: list[float] = (nlp_doc.get("embedding") or []) if nlp_doc else []
    user_labels: list[str] = (nlp_doc.get("labels") or []) if nlp_doc else []

    # Score every archetype
    scored: list[tuple[float, dict, dict]] = []
    for arch in archetypes:
        score, contributions = _score_career(
            aptitude, user_ocean, user_embedding, user_labels, arch, weights
        )
        scored.append((score, contributions, arch))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:TOP_N]

    # Build and persist documents
    now = datetime.now(UTC)
    docs = []
    for score, contributions, arch in top:
        job_count = await jobs_snapshot_col().count_documents(
            {"industry": arch["career_id"]}, limit=1000
        )
        docs.append({
            "user_id": uid,
            "career_id": arch["career_id"],
            "career_title": arch["career_title"],
            "score": score,
            "contributions": contributions,
            "explanation": _explanation(arch["career_title"], score, contributions),
            "salary_range": None,
            "job_count": job_count,
            "weights_snapshot": dict(weights),
            "created_at": now,
        })

    await recommendations_col().delete_many({"user_id": uid})
    result = await recommendations_col().insert_many(docs)

    for doc, oid in zip(docs, result.inserted_ids):
        doc["id"] = str(oid)

    return {"recommendations": [_serialise(d) for d in docs]}


@router.get("/")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """Return the most recent stored recommendations for this user."""
    uid = current_user["user_id"]
    docs = await recommendations_col().find(
        {"user_id": uid},
        sort=[("score", -1)],
    ).to_list(length=TOP_N)

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations yet — POST /recommendations to generate",
        )

    return {"recommendations": [_serialise(d) for d in docs]}


@router.get("/{recommendation_id}")
async def get_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return a single recommendation by ID."""
    try:
        oid = ObjectId(recommendation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid recommendation ID",
        )

    doc = await recommendations_col().find_one({"_id": oid, "user_id": current_user["user_id"]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    return _serialise(doc)
