"""Audit route — admin-only bias analysis across demographic attributes.

Algorithm (per CLAUDE.md):
  1. Fetch the most-recent recommendation score for every user.
  2. Join with user_demographics (admin-only collection).
  3. For each of the four demographic attributes, compute per-group mean scores.
  4. Disparate Impact Ratio (DIR) = min_group_mean / max_group_mean.
  5. Equal Opportunity Score (EOS) = min_group_mean / overall_mean.
  6. FLAG if DIR < 0.80 (4/5ths rule).
  7. Persist snapshot to bias_audit; return report.
"""
from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import bias_audit_col, recommendations_col, user_demographics_col
from ..dependencies import require_admin

router = APIRouter()

_DEMO_ATTRIBUTES = ["gender", "age_group", "field_of_study", "socioeconomic_background"]
_DIR_THRESHOLD = 0.80


# ── Bias computation ──────────────────────────────────────────────────────────

def _attribute_metric(attribute: str, rows: list[dict]) -> dict[str, Any]:
    """Compute DIR and EOS for one demographic attribute over the joined rows."""
    groups: dict[str, list[float]] = {}
    for row in rows:
        val = (row.get(attribute) or "Unknown").strip() or "Unknown"
        groups.setdefault(val, []).append(row["score"])

    if len(groups) < 2:
        return {
            "attribute": attribute,
            "disparate_impact_ratio": 1.0,
            "equal_opportunity_score": 1.0,
            "flagged": False,
        }

    group_means = {k: sum(v) / len(v) for k, v in groups.items()}
    all_scores = [s for v in groups.values() for s in v]
    overall_mean = sum(all_scores) / len(all_scores)

    max_mean = max(group_means.values())
    min_mean = min(group_means.values())

    dir_ratio = round(min_mean / max_mean, 4) if max_mean > 0 else 1.0
    eos = round(min_mean / overall_mean, 4) if overall_mean > 0 else 1.0

    return {
        "attribute": attribute,
        "disparate_impact_ratio": dir_ratio,
        "equal_opportunity_score": eos,
        "flagged": dir_ratio < _DIR_THRESHOLD,
    }


def _serialise(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    out["id"] = str(doc["_id"])
    if isinstance(out.get("created_at"), datetime):
        out["created_at"] = out["created_at"].isoformat()
    return out


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/run", status_code=status.HTTP_201_CREATED)
async def run_audit(admin: dict = Depends(require_admin)):
    """Compute disparate-impact metrics and persist a bias_audit snapshot."""

    # Most recent recommendation score per user
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$group": {"_id": "$user_id", "score": {"$first": "$score"}}},
    ]
    rec_docs = await recommendations_col().aggregate(pipeline).to_list(length=10_000)
    score_by_uid: dict[str, float] = {d["_id"]: d["score"] for d in rec_docs}

    # Fetch demographics for those users
    demo_docs = await user_demographics_col().find(
        {"user_id": {"$in": list(score_by_uid.keys())}}
    ).to_list(length=10_000)
    demo_by_uid: dict[str, dict] = {d["user_id"]: d for d in demo_docs}

    # Build joined rows (users with both a score and a demographics doc)
    joined = [
        {"score": score_by_uid[uid], **demo_by_uid[uid]}
        for uid in score_by_uid
        if uid in demo_by_uid
    ]

    metrics = [_attribute_metric(attr, joined) for attr in _DEMO_ATTRIBUTES]

    doc = {
        "triggered_by": admin["user_id"],
        "metrics": metrics,
        "user_count": len(score_by_uid),
        "matched_count": len(joined),
        "created_at": datetime.now(UTC),
    }
    result = await bias_audit_col().insert_one(doc)
    doc["id"] = str(result.inserted_id)

    return _serialise(doc)


@router.get("/reports")
async def list_reports(admin: dict = Depends(require_admin)):
    """Return all bias audit snapshots, newest first."""
    docs = await bias_audit_col().find({}, sort=[("created_at", -1)]).to_list(length=100)
    return {"reports": [_serialise(d) for d in docs]}


@router.get("/reports/{report_id}")
async def get_report(report_id: str, admin: dict = Depends(require_admin)):
    """Return a single bias audit report by ID."""
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid report ID",
        )

    doc = await bias_audit_col().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return _serialise(doc)
