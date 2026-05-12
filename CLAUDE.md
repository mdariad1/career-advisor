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

## Current status
[ ] Update this section as development progresses