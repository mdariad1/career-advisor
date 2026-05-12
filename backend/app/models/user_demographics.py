from __future__ import annotations

from typing import Optional
from pydantic import Field
from .common import MongoModel, PyObjectId


class UserDemographicsDocument(MongoModel):
    """user_demographics collection — isolated from recommendation pipeline.

    Joined ONLY in the /audit pipeline with an admin JWT.
    """

    user_id: PyObjectId
    gender: Optional[str] = None
    age_group: Optional[str] = None
    field_of_study: Optional[str] = None
    socioeconomic_background: Optional[str] = None
