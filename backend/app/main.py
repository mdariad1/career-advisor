from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, survey, profile, recommendations, feedback, jobs, audit
from .database import ping_db, close_db, ensure_indexes, surveys_col, career_archetypes_col
from .seed import seed_surveys, seed_archetypes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    result = await ping_db()
    logger.info("MongoDB connected — ping: %s", result)
    await ensure_indexes()
    await seed_surveys(surveys_col())
    await seed_archetypes(career_archetypes_col())
    yield
    # shutdown
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Career Advisor API",
        description="Intelligent career counselling platform for university students.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(survey.router, prefix="/survey", tags=["survey"])
    app.include_router(profile.router, prefix="/profile", tags=["profile"])
    app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
    app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
    app.include_router(audit.router, prefix="/audit", tags=["audit"])

    @app.get("/health", tags=["health"])
    async def health():
        pong = await ping_db()
        return {"status": "ok", "mongo": pong}

    return app


app = create_app()

