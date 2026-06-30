# Career Advisor — Claude Code Context

## What this project is
An intelligent career counseling platform for university students combining
psychometric assessment, NLP-based open-text analysis, and live job market
data. Architecture and design decisions are fully documented in chapter3.tex.

## Architecture overview
- frontend/     Vue.js + Tailwind CSS (port 5173 in dev)
- backend/      FastAPI Python, central API orchestrator (port 8000)
- nlp_service/  FastAPI Python, BERT embedding + SVM classification (port 8001)
- job_sync/     Python APScheduler, runs every 24h, no HTTP port
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
- Tech Layoffs & Hiring Trends 2026: Kaggle (`data/tech_layoffs.csv`, 12,000 rows, synthetic) —
  drives `career_archetypes.market_demand_seed`, see `data/compute_market_demand.py`

## API route groups
/auth, /survey, /profile, /recommendations, /feedback, /jobs, /audit

## Environment variables (see .env)
MONGO_URI, JWT_SECRET, JWT_REFRESH_SECRET, NLP_SERVICE_URL,
ADZUNA_APP_ID, ADZUNA_APP_KEY, SYNC_INTERVAL_HOURS, TARGET_COUNTRIES

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
[x] Profile layer — /profile, /profile/weights, DELETE /profile implemented and tested (9/9)
    - GET /profile: unified psychometric profile (aptitude_score, ocean_vector, nlp_labels, weights, assessments_completed flags)
    - GET /profile/weights: per-user WeightVector with defaults (0.25/0.30/0.25/0.20)
    - DELETE /profile: GDPR cascade-delete (user, demographics, sessions, results, nlp_analysis)
[x] Recommendations layer — /recommendations POST/GET/{id} implemented and tested (14/14)
    - POST /recommendations: score all archetypes → top-5 → persist + return; replaces prior run
    - GET /recommendations: return cached top-5 (no recompute)
    - GET /recommendations/{id}: single recommendation lookup
    - Scoring: score = w_apt*aptitude + w_pf*personality_fit + w_nlp*nlp_similarity + w_md*market_demand
    - SHAP: analytically exact additive decomposition (weighted contribution per term, sums to score)
    - NLP similarity: embedding cosine sim > label Jaccard > neutral 0.5 fallback
    - Personality fit: OCEAN cosine similarity; defaults to 0.5 if personality survey not done
    - 8 career archetypes seeded in career_archetypes collection via seed.py::CAREER_ARCHETYPES
[x] Feedback layer — /feedback POST implemented and tested (11/11)
    - Accept: bumps top SHAP factor weight by α=0.025, normalises to sum=1.0, clamps [0.05, 0.50]
    - Reject: logs event only, weights unchanged
    - Persists FeedbackDocument; returns weights_before, weights_after, top_factor
[x] Jobs layer — /jobs GET implemented and tested (10/10)
    - Filters: industry, country_code (exact match); excludes stale listings
    - Pagination: skip/limit (max 100); returns total, skip, limit, jobs list
[x] Audit layer — /audit/run POST, /audit/reports GET/{id} implemented and tested (11/11)
    - Admin-only (require_admin dependency); promotes role via JWT
    - Joins recommendations (most-recent score per user) with user_demographics
    - Disparate Impact Ratio = min_group_mean / max_group_mean; flagged if DIR < 0.80
    - Equal Opportunity Score = min_group_mean / overall_mean
    - Computes metrics for: gender, age_group, field_of_study, socioeconomic_background
    - Persists BiasAuditDocument snapshot; GET /reports lists all; GET /reports/{id} for single
[x] NLP service — /embed, /classify, /analyse implemented and tested (27/27)
    - sentence-transformers/all-MiniLM-L6-v2 → 384-dim normalised embedding (lazy singleton)
    - OneVsRestClassifier(SVC, rbf, probability=True) → 6 thematic labels with per-label scores
    - /analyse combines both in one call (used by backend survey _call_nlp_service)
    - Lifespan pre-loads both models at startup; gracefully warns if classifier not trained
    - nlp_service/.venv uses Python 3.13-compatible pinned versions
[x] Job sync — Adzuna API integration implemented
    - run_sync_cycle(): loops over all configured countries × 8 career archetypes, fetches from Adzuna, NLP-classifies skills, upserts jobs_snapshot, marks stale
    - Adzuna endpoint: GET /v1/api/jobs/{country}/search/{page}?app_id=&app_key=&what=&category=
    - Career archetype → Adzuna category+keyword mapping in _CAREER_QUERIES (job_sync/app/sync.py)
    - Supports all 19 Adzuna countries via TARGET_COUNTRIES (comma-separated, e.g. "gb,us,de")
    - Rate budget: 19 countries × 8 careers × 1 page × 1 cycle/day = 152 req/day (free tier: 250)
    - _MAX_PAGES=1 (50 jobs/archetype/country); SYNC_INTERVAL_HOURS=24
    - Stores: job_id, title, company, industry (career_id slug), country_code, location (display_name), salary_range, skills, raw_skills, redirect_url, is_stale, synced_at
    - html.unescape() applied to title and company to handle API HTML entities
    - Respects inter_query_delay_seconds (1s) and job_stale_days (14) from config
[x] Frontend ↔ backend integration — views wired to real API calls
    - AssessmentView: loads questions from /survey/start; MCQ radio buttons (aptitude); Likert 0-4 buttons (personality)
    - RecommendationsView: unwraps data.recommendations; 404 → generate button; regenerate button
    - JobsView: unwraps data.jobs from paginated response shape {total, skip, limit, jobs}; job title links to redirect_url; location displayed from Adzuna display_name
    - ShapBreakdown: fixed value scaling (contributions are 0–0.5 floats, multiplied by 100 for display)
[x] NLP SVM classifier training pipeline — app/train.py with 90 hand-crafted labeled examples (15/label)
    - Multi-label training data (6 labels: analytical, creative, interpersonal, technical, leadership, structured)
    - Embeds corpus with MiniLM, fits OneVsRest SVM, saves bundle to models/svm_classifier.joblib
    - `python -m app.train` or `make nlp-train`; conftest auto-trains if model file absent
[x] Frontend dark mode UI — full Tailwind dark theme applied to all views (commit 4209ef8)
    - All views (Login, Register, Dashboard, Assessment, Recommendations, Jobs, Audit) use dark neutral palette
    - Tailwind properly configured via postcss.config.js and tailwind.config.js (content paths fixed)
    - Vite dev proxy uses VITE_API_TARGET env var (set to http://backend:8000 in docker-compose.dev.yml)
[x] Auth hardening — JWT access token life increased from 15 → 60 minutes (commit bd5d21e)
    - Axios client (frontend/src/api/index.ts) has full token refresh interceptor: queues concurrent requests during in-flight refresh, clears session and redirects on refresh failure
[x] Jobs layer improvements — search fixed and extended (commits b95f28f + session)
    - Industry filter: case-insensitive partial regex matching industry slug OR job title ($or) — "teacher" matches educator jobs
    - Country filter: case-insensitive exact ISO code match ("gb" → "GB")
    - Combined filters use MongoDB $and to compose $or conditions correctly
[x] Vite/Vitest config split — production build type-check fixed
    - test block moved from vite.config.ts to vitest.config.ts (imports defineConfig from vitest/config)
    - vite.config.ts is now purely Vite config; resolves vue-tsc --build TS2769 error caused by vitest bundling its own vite copy
[x] Market demand from real data — career_archetypes.market_demand_seed derived from tech_layoffs.csv
    - data/compute_market_demand.py: stdlib-only script, reads tech_layoffs.csv (12,000 rows), writes data/market_demand_scores.json
    - Per-archetype composite score (weights sum to 1.0): 0.35*hiring_trend + 0.25*job_security_score + 0.20*open_roles + 0.10*salary_budget_change + 0.10*(10-ai_replacement_risk)
    - Row attribution: primary match via top_hiring_role → career_id (ROLE_MAP); industry → career_id fallback (INDUSTRY_FALLBACK) for archetypes not covered by any role
    - Dataset is layoffs-biased so raw scores cluster ~0.42-0.47; scaled so data_scientist (highest, 4309 rows) anchors at 0.85, preserving relative order
    - mechanical_engineer/biomedical_researcher/educator have no dataset signal (non-tech fields) — hand-tuned below the tech cluster (0.68/0.60/0.52)
    - New `market_demand_source` field per archetype: "tech_layoffs_2026_csv" | "tech_layoffs_2026_csv_industry_proxy" | "hand_tuned"
    - seed.py::seed_archetypes() now upserts (not insert-only) — refreshes market_demand_seed/market_demand_source on existing docs every app startup, no DB wipe needed
    - Re-run `python data/compute_market_demand.py` after refreshing the CSV, then copy new values into seed.py::CAREER_ARCHETYPES
[x] Makefile dev workflow targets — added after a network conflict from mixing prod/dev compose
    - `make dev-up`: detached dev start with --force-recreate (daily workflow)
    - `make dev-clean`: tears down both docker-compose.yml and docker-compose.dev.yml (containers + networks) then starts dev fresh — fixes "container not connected to network career-advisor_internal" errors
    - `make down-all`: stops/removes containers from both compose files without restarting
    - Root cause of the conflict: `docker compose up` (prod) and `docker compose -f docker-compose.dev.yml up` (dev) both name containers career-advisor-*-1 but define different networks (prod adds an `external` network); running one after the other without a full `down` leaves containers attached to networks the other compose file doesn't know about