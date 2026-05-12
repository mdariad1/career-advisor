from __future__ import annotations

from typing import Annotated, Any
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(str):
    """Serialises MongoDB ObjectId as a plain string in JSON while accepting ObjectId inputs."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v!r}")

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: Any, handler: Any) -> dict:
        return {"type": "string", "format": "objectid"}


OptionalId = Annotated[PyObjectId | None, Field(default=None, alias="_id")]


class MongoModel(BaseModel):
    """Base for all MongoDB document models.

    - ``id`` maps to the ``_id`` field in MongoDB documents.
    - ``model_dump_mongo()`` returns a dict ready for Motor upserts
      (converts the ``id`` back to ObjectId for the ``_id`` field).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: OptionalId = None

    def model_dump_mongo(self, **kwargs: Any) -> dict:
        d = self.model_dump(by_alias=True, exclude_none=True, **kwargs)
        if "_id" in d and d["_id"] is not None:
            d["_id"] = ObjectId(d["_id"])
        return d
