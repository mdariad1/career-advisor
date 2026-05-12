from fastapi import FastAPI
from .routers import embed, classify


def create_app() -> FastAPI:
    app = FastAPI(
        title="Career Advisor NLP Service",
        description="BERT embedding and SVM thematic classification for open-text responses.",
        version="0.1.0",
    )

    app.include_router(embed.router, prefix="/embed", tags=["embed"])
    app.include_router(classify.router, prefix="/classify", tags=["classify"])

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
