from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Any
from ..dependencies import get_current_user

router = APIRouter()


class StartSessionRequest(BaseModel):
    survey_type: str  # aptitude | personality | open_text


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answers: list[Any]


class OpenTextSubmitRequest(BaseModel):
    session_id: str
    response_text: str


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_session(body: StartSessionRequest, current_user: dict = Depends(get_current_user)):
    raise NotImplementedError


@router.post("/submit")
async def submit_answers(body: SubmitAnswerRequest, current_user: dict = Depends(get_current_user)):
    raise NotImplementedError


@router.post("/submit-text", status_code=status.HTTP_202_ACCEPTED)
async def submit_open_text(body: OpenTextSubmitRequest, current_user: dict = Depends(get_current_user)):
    """Accepts open-text response and enqueues NLP processing asynchronously."""
    raise NotImplementedError


@router.get("/status/{session_id}")
async def get_nlp_status(session_id: str, current_user: dict = Depends(get_current_user)):
    raise NotImplementedError
