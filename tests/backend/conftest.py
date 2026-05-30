import sys
import os

# Make sure 'app' resolves to backend/app when running tests from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

import pytest


@pytest.fixture(scope="session")
async def seeded_surveys():
    """Ensure the surveys collection has sample questions for the duration of the test session.

    Inserts any missing questions at session start; removes only the ones inserted
    by this session at teardown (leaves pre-existing questions untouched).
    """
    from app.database import surveys_col
    from app.seed import ALL_QUESTIONS

    col = surveys_col()

    # Record which questions we insert so we can clean up precisely
    inserted_ids = []
    for q in ALL_QUESTIONS:
        existing = await col.find_one({"question": q["question"]})
        if existing is None:
            doc = {k: v for k, v in q.items() if v is not None}
            doc.setdefault("metadata", {})
            result = await col.insert_one(doc)
            inserted_ids.append(result.inserted_id)

    yield col  # tests receive the surveys collection handle if they want it

    if inserted_ids:
        await col.delete_many({"_id": {"$in": inserted_ids}})
