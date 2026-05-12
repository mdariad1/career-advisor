# Career Advisor

An intelligent career counselling platform for university students. Combines psychometric assessment, NLP-based open-text analysis, and live job-market data to generate ranked, explainable career recommendations.

## Services

| Service | Tech | Port |
|---|---|---|
| `frontend` | Vue 3 + Tailwind CSS | 5173 (dev) / 80 (prod) |
| `backend` | FastAPI + Motor | 8000 |
| `nlp_service` | FastAPI + sentence-transformers | 8001 |
| `job_sync` | APScheduler background worker | — |
| MongoDB | Atlas (career_db) | — |

## Quick start

```bash
cp .env.example .env       # fill in MONGO_URI, JWT_SECRET, etc.
make dev                   # starts all services with hot-reload
```

Frontend: http://localhost:5173  
API docs: http://localhost:8000/docs

## Running tests

```bash
make test                  # all suites
make test-backend          # pytest (tests/backend/)
make test-nlp              # pytest (tests/nlp/)
make test-frontend         # vitest (frontend/)
```

## Environment variables

See `.env.example`. Required keys: `MONGO_URI`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `NLP_SERVICE_URL`, `JOBDATAPOOL_API_KEY`.

## Architecture

See `chapter3.tex` for full design documentation and `CLAUDE.md` for AI assistant context.
