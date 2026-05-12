from __future__ import annotations

from typing import Any, Optional
from pydantic import Field
from .common import MongoModel


class SurveyQuestionDocument(MongoModel):
    """surveys collection — pre-loaded MCQ question bank."""

    survey_type: str        # aptitude | personality
    source: str             # scienceqa | engineering_aptitude
    grade: Optional[int] = None
    question: str
    choices: list[str]
    answer_index: int
    lecture: Optional[str] = None    # ScienceQA post-answer explanation
    solution: Optional[str] = None   # ScienceQA worked solution
    metadata: dict[str, Any] = Field(default_factory=dict)
