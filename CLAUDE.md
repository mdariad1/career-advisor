# Career Advisor — Claude Code Context

## What this project is
An intelligent career counseling platform for university students combining
psychometric assessment, NLP-based open-text analysis, and live job market
data. Architecture and design decisions are fully documented in chapter3.tex.

## Architecture overview
- frontend/     Vue.js + Tailwind CSS (port 5173 in dev)
- backend/      FastAPI Python, central API orchestrator (port 8000)
- nlp_service/  FastAPI Python, BERT embedding + SVM classification (port 8001)
- job_sync/     Python APScheduler, runs every 6h, no HTTP port
- MongoDB       port 27017, database: career_db
- All services run in Docker; docker-compose.dev.yml for local development

## Key design decisions (read chapter3.tex for full detail)
- Scoring formula: score(c,u) = 0.25*aptitude + 0.30*personality_fit + 0.25*nlp_similarity + 0.20*market_demand
- Weights stored per-user in MongoDB, updated via feedback loop (α=0.025)
- SHAP explanations are analytically exact (weighted linear sum, no approximation)
- NLP applied ONLY to: open-text responses, job skill normalization
- MCQ scoring (ScienceQA, Engineering Aptitude) is purely deterministic
- Demographics stored in user_demographics collection, NEVER read by recommendation pipeline
- Bias audit joins recommendations + user_demographics, admin JWT only

## MongoDB collections
users, user_demographics, results, nlp_analysis, weights, recommendations,
jobs_snapshot, feedback, sessions, career_archetypes, surveys, bias_audit

All 12 collections have indexes defined in `backend/app/database.py::ensure_indexes()`.
Called at app startup (lifespan) and in test setup — this replaces the Docker init script
for Atlas, where collections are created lazily.

## NLP model
sentence-transformers/all-MiniLM-L6-v2 (384-dim embeddings)
SVM classifier trained on Q&A Kaggle dataset
Labels: analytical, creative, interpersonal, technical, leadership, structured

## Datasets (all in /data directory, gitignored except structure)
- ScienceQA: HuggingFace, text-only subset, grade >= 7
- Engineering Aptitude: Kaggle
- Q&A Dataset: Kaggle (NLP training)
- OCEAN Big Five: HuggingFace
- AI Job Market: Kaggle (career taxonomy seed)

## API route groups
/auth, /survey, /profile, /recommendations, /feedback, /jobs, /audit

## Environment variables (see .env.example)
MONGO_URI, JWT_SECRET, JWT_REFRESH_SECRET, NLP_SERVICE_URL,
JOBDATAPOOL_API_KEY, SYNC_INTERVAL_HOURS, TARGET_COUNTRY_CODE

## Testing
- Backend: pytest (tests/backend/)
- NLP service: pytest (tests/nlp/)
- Frontend: Vitest (frontend/src/__tests__/)
- Run all: make test

## MongoDB connection notes
- Use direct replica-set URI, NOT `mongodb+srv://` — SRV resolution is broken with Motor on Python 3.13
- URI format: `mongodb://user:pass@host1:27017,host2:27017,host3:27017/career_db?authSource=admin&replicaSet=...&tls=true`
- The replica set name and hosts can be resolved from DNS: `nslookup -type=SRV _mongodb._tcp.<cluster>.mongodb.net`
- `uuidRepresentation="standard"` is required in `AsyncIOMotorClient` kwargs

## Pydantic models
All 13 document models live in `backend/app/models/`. They extend `MongoModel` (from `common.py`),
which provides `PyObjectId`, `model_dump_mongo()`, and `ConfigDict(populate_by_name=True)`.
Use `datetime.now(UTC)` via `default_factory=lambda: datetime.now(UTC)` — never `datetime.utcnow`.

## Testing notes
- `pytest.ini` sets `asyncio_mode=auto`, `asyncio_default_test_loop_scope=session`, `asyncio_default_fixture_loop_scope=session`
- Both scopes must be `session` — Motor binds to the creating event loop; fixtures in a different loop cause "Future attached to a different loop" errors
- HTTP integration tests use `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")` — NOT Starlette's sync `TestClient` (which spawns its own anyio loop)
- Session-scoped `client` fixtures share one Motor client across all tests; function-scoped `cleanup_*` fixtures must depend on `client` to guarantee ordering
- Each JWT must include a `jti` (random hex nonce) — tokens issued within the same second are otherwise identical, causing `DuplicateKeyError` on the `sessions.token_hash` unique index
- `tests/backend/conftest.py` inserts `../../backend` into `sys.path`
- Atlas creates collections lazily; call `ensure_indexes()` before `list_collection_names()` in tests

## Survey question bank
- Questions live in the `surveys` collection, seeded via `backend/app/seed.py::seed_surveys()`
- 25 aptitude MCQs (ScienceQA-style, grade 7-10; engineering aptitude): `answer_index` = correct choice (0-indexed)
- 25 OCEAN personality questions (5 per dimension, Likert 0-4): `metadata.ocean_dimension` + `metadata.polarity` (1 / -1)
- Personality score per dimension: `raw = answer / 4.0`; flip if `polarity == -1`; mean per dimension → ocean_vector[5]
- Aptitude score: `correct / total` → stored in `users.aptitude_score`
- `conftest.py::seeded_surveys` fixture seeds once per test session and cleans up only what it inserted

## Current status
[x] Project scaffold — all four services, Docker, Makefile, GitHub Actions CI
[x] MongoDB connection layer — Motor client, ensure_indexes(), typed collection accessors
[x] Pydantic v2 document models — all 13 collections modelled
[x] FastAPI app factory with lifespan (ping + ensure_indexes at startup)
[x] Router stubs — /auth, /survey, /profile, /recommendations, /feedback, /jobs, /audit
[x] Frontend skeleton — Vue 3 + Tailwind, router, Pinia stores (auth, user), axios client
[x] Frontend views — Login, Register, Dashboard, Assessment (3-step), Recommendations, Jobs, Audit
[x] Frontend components — AppNav, WeightPanel, ShapBreakdown
[x] Live Atlas connectivity tests — 6/6 passing
[x] Auth layer — /auth/register, /login, /refresh, /logout, /me implemented and tested (11/11)
[x] Survey layer — /survey/start, /submit, /submit-text, /status implemented and tested (16/16)
    - Aptitude MCQ scoring (deterministic, updates users.aptitude_score)
    - Personality OCEAN scoring (Likert → [O,C,E,A,N] vector, updates users.ocean_vector)
    - Open-text ingestion (NlpAnalysisDocument created, NLP service called async, graceful fallback)
[ ] Business logic — /profile, /recommendations, /feedback, /jobs, /audit not yet implemented
    [ ] /profile GET — aggregate psychometric profile + weights from users collection
    [ ] /profile/weights GET — return per-user WeightVector
    [ ] /recommendations POST/GET — scoring formula + SHAP breakdown
    [ ] /feedback POST — accept accept/reject signal, update weights (α=0.025)
    [ ] /jobs GET — paginated jobs_snapshot query with filters
    [ ] /audit GET — bias audit pipeline (admin only, joins recommendations + demographics)
[ ] NLP service — embed + classify endpoints stubbed, model loading not implemented
[ ] Job sync — APScheduler + JobDataPool API integration not implemented
[ ] Frontend ↔ backend integration — views wired to real API calls
[ ] NLP SVM classifier training pipeline