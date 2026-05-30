"""Survey routes — MCQ delivery and deterministic scoring.

Supported survey types:
  aptitude    — science/engineering MCQs; score = correct / total  → [0, 1]
  personality — OCEAN Big Five Likert scale; score → [O, C, E, A, N] each [0, 1]
  open_text   — free-form response; forwarded to NLP service asynchronously
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, UTC
from typing import Any

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..database import (
    nlp_analysis_col,
    results_col,
    surveys_col,
    users_col,
)
from ..dependencies import get_current_user
from ..models.nlp_analysis import NlpAnalysisDocument
from ..models.results import ResultDocument

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_SURVEY_TYPES = {"aptitude", "personality", "open_text"}
DEFAULT_APTITUDE_COUNT = 20
DEFAULT_PERSONALITY_PER_DIM = 5          # 5 questions × 5 dims = 25 total
OCEAN_DIMS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


# ── Request / response schemas ────────────────────────────────────────────────

class StartRequest(BaseModel):
    survey_type: str
    count: int = DEFAULT_APTITUDE_COUNT   # used for aptitude; personality always 5-per-dim


class SubmitRequest(BaseModel):
    session_id: str
    answers: list[int]   # ordered list of answer indices matching questions returned by /start


class OpenTextRequest(BaseModel):
    session_id: str
    response_text: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_answer(doc: dict) -> dict:
    """Return a question dict safe to send to the client (no answer_index)."""
    return {
        "id": str(doc["_id"]),
        "question": doc["question"],
        "choices": doc["choices"],
        "grade": doc.get("grade"),
        "lecture": doc.get("lecture"),   # shown post-submit for aptitude
        "survey_type": doc["survey_type"],
    }


async def _fetch_aptitude_questions(count: int) -> list[dict]:
    """Return `count` random aptitude questions from the surveys collection."""
    pipeline = [
        {"$match": {"survey_type": "aptitude"}},
        {"$sample": {"size": count}},
    ]
    return await surveys_col().aggregate(pipeline).to_list(length=count)


async def _fetch_personality_questions(per_dim: int = DEFAULT_PERSONALITY_PER_DIM) -> list[dict]:
    """Return a balanced set of personality questions — `per_dim` per OCEAN dimension."""
    questions: list[dict] = []
    for dim in OCEAN_DIMS:
        pipeline = [
            {"$match": {"survey_type": "personality", "metadata.ocean_dimension": dim}},
            {"$sample": {"size": per_dim}},
        ]
        questions.extend(await surveys_col().aggregate(pipeline).to_list(length=per_dim))
    random.shuffle(questions)
    return questions


def _score_aptitude(questions: list[dict], answers: list[int]) -> dict:
    """Return aptitude scoring breakdown."""
    correct = sum(
        1 for q, a in zip(questions, answers)
        if a == q.get("answer_index")
    )
    total = len(questions)
    return {
        "score": round(correct / total, 4) if total else 0.0,
        "correct": correct,
        "total": total,
    }


def _score_personality(questions: list[dict], answers: list[int]) -> list[float]:
    """Return OCEAN vector [O, C, E, A, N], each normalised to [0, 1]."""
    buckets: dict[str, list[float]] = {dim: [] for dim in OCEAN_DIMS}

    for q, a in zip(questions, answers):
        meta = q.get("metadata", {})
        dim = meta.get("ocean_dimension")
        polarity = meta.get("polarity", 1)
        if dim not in buckets:
            continue
        raw = a / 4.0                          # Likert 0-4 → [0, 1]
        score = raw if polarity == 1 else 1 - raw
        buckets[dim].append(score)

    vector = []
    for dim in OCEAN_DIMS:
        scores = buckets[dim]
        vector.append(round(sum(scores) / len(scores), 4) if scores else 0.5)
    return vector


async def _call_nlp_service(user_id: str, session_id: str, text: str) -> None:
    """Fire-and-forget call to NLP service. Failures are logged, not raised."""
    url = f"{settings.nlp_service_url}/analyse"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"user_id": user_id, "session_id": session_id, "text": text})
            if resp.status_code == 200:
                data = resp.json()
                await nlp_analysis_col().update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "embedding": data.get("embedding", []),
                        "labels": data.get("labels", []),
                        "label_scores": data.get("label_scores", {}),
                        "status": "done",
                        "processed_at": datetime.now(UTC),
                    }},
                )
            else:
                logger.warning("NLP service returned %s for session %s", resp.status_code, session_id)
    except Exception as exc:
        logger.warning("NLP service unavailable (%s) — session %s stays pending", exc, session_id)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_survey(body: StartRequest, current_user: dict = Depends(get_current_user)):
    """Pick questions from the bank and create a pending ResultDocument."""
    if body.survey_type not in VALID_SURVEY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"survey_type must be one of {sorted(VALID_SURVEY_TYPES)}",
        )

    session_id = ObjectId()

    if body.survey_type == "aptitude":
        if body.count < 1 or body.count > 50:
            raise HTTPException(status_code=422, detail="count must be between 1 and 50")
        questions = await _fetch_aptitude_questions(body.count)
        if not questions:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="No aptitude questions found — seed the surveys collection first")

    elif body.survey_type == "personality":
        questions = await _fetch_personality_questions()
        if not questions:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="No personality questions found — seed the surveys collection first")

    else:  # open_text — no MCQ questions
        questions = []

    question_ids = [str(q["_id"]) for q in questions]

    result_doc = ResultDocument(
        user_id=current_user["user_id"],
        session_id=str(session_id),
        survey_type=body.survey_type,
        question_ids=question_ids,
        status="started",
    )
    await results_col().insert_one(result_doc.model_dump_mongo())

    return {
        "session_id": str(session_id),
        "survey_type": body.survey_type,
        "question_count": len(questions),
        "questions": [_strip_answer(q) for q in questions],
    }


@router.post("/submit")
async def submit_answers(body: SubmitRequest, current_user: dict = Depends(get_current_user)):
    """Score submitted answers, persist result, and update the user's profile."""
    result = await results_col().find_one({
        "session_id": body.session_id,
        "user_id": current_user["user_id"],
    })
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey session not found")
    if result.get("status") == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Survey already submitted")

    survey_type = result["survey_type"]
    if survey_type == "open_text":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use POST /survey/submit-text for open-text sessions",
        )

    question_ids = result.get("question_ids", [])
    if len(body.answers) != len(question_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Expected {len(question_ids)} answers, got {len(body.answers)}",
        )

    # Fetch questions in submission order
    oid_list = [ObjectId(qid) for qid in question_ids]
    raw_questions = await surveys_col().find({"_id": {"$in": oid_list}}).to_list(length=len(oid_list))
    q_map = {str(q["_id"]): q for q in raw_questions}
    ordered_questions = [q_map[qid] for qid in question_ids if qid in q_map]

    # Score
    score: float | None = None
    ocean_vector: list[float] | None = None
    response: dict[str, Any]

    if survey_type == "aptitude":
        breakdown = _score_aptitude(ordered_questions, body.answers)
        score = breakdown["score"]
        response = {"survey_type": "aptitude", "session_id": body.session_id, **breakdown}

        # Attach lecture/solution for each question
        response["questions"] = [
            {**_strip_answer(q), "your_answer": a, "correct_answer": q["answer_index"]}
            for q, a in zip(ordered_questions, body.answers)
        ]

        # Update user aptitude_score
        await users_col().update_one(
            {"_id": ObjectId(current_user["user_id"])},
            {"$set": {"aptitude_score": score, "updated_at": datetime.now(UTC)}},
        )

    else:  # personality
        ocean_vector = _score_personality(ordered_questions, body.answers)
        response = {
            "survey_type": "personality",
            "session_id": body.session_id,
            "ocean_vector": dict(zip(OCEAN_DIMS, ocean_vector)),
        }

        # Update user ocean_vector
        await users_col().update_one(
            {"_id": ObjectId(current_user["user_id"])},
            {"$set": {"ocean_vector": ocean_vector, "updated_at": datetime.now(UTC)}},
        )

    # Persist completed result
    await results_col().update_one(
        {"session_id": body.session_id},
        {"$set": {
            "answers": body.answers,
            "score": score,
            "ocean_vector": ocean_vector,
            "status": "completed",
            "completed_at": datetime.now(UTC),
        }},
    )

    return response


@router.post("/submit-text", status_code=status.HTTP_202_ACCEPTED)
async def submit_open_text(body: OpenTextRequest, current_user: dict = Depends(get_current_user)):
    """Accept an open-text response and enqueue asynchronous NLP processing."""
    result = await results_col().find_one({
        "session_id": body.session_id,
        "user_id": current_user["user_id"],
    })
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey session not found")
    if result.get("survey_type") != "open_text":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This session is not an open-text session",
        )
    if result.get("status") == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already submitted")

    nlp_doc = NlpAnalysisDocument(
        user_id=current_user["user_id"],
        session_id=body.session_id,
        raw_text=body.response_text,
        embedding=[],
        labels=[],
        label_scores={},
        status="pending",
    )
    await nlp_analysis_col().insert_one(nlp_doc.model_dump_mongo())

    # Mark result as completed (text received)
    await results_col().update_one(
        {"session_id": body.session_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(UTC)}},
    )

    # Non-blocking NLP call (fails gracefully if service is unavailable)
    import asyncio
    asyncio.create_task(_call_nlp_service(
        current_user["user_id"], body.session_id, body.response_text
    ))

    return {"session_id": body.session_id, "status": "pending"}


@router.get("/status/{session_id}")
async def get_nlp_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Return the NLP processing status for an open-text session."""
    doc = await nlp_analysis_col().find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NLP session not found")

    response: dict[str, Any] = {"session_id": session_id, "status": doc["status"]}
    if doc["status"] == "done":
        response["labels"] = doc.get("labels", [])
        response["label_scores"] = doc.get("label_scores", {})
    return response
