.PHONY: dev build test test-backend test-nlp test-frontend lint up down logs

# ── Development ──────────────────────────────────────────────────────────────

dev:
	docker compose -f docker-compose.dev.yml up --build

down:
	docker compose -f docker-compose.dev.yml down

logs:
	docker compose -f docker-compose.dev.yml logs -f

# ── Production build ─────────────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up -d

# ── Testing ───────────────────────────────────────────────────────────────────

test: test-backend test-nlp test-frontend

test-backend:
	cd backend && python -m pytest ../../tests/backend -v

test-nlp:
	cd nlp_service && python -m pytest ../../tests/nlp -v

test-frontend:
	cd frontend && npm run test

# ── Linting ───────────────────────────────────────────────────────────────────

lint:
	cd backend && python -m flake8 app/
	cd nlp_service && python -m flake8 app/
	cd job_sync && python -m flake8 app/
	cd frontend && npm run lint

# ── Data & model utilities ────────────────────────────────────────────────────

data-dir:
	mkdir -p data/scienceqa data/engineering_aptitude data/qa_dataset data/ocean data/job_market

nlp-train:
	cd nlp_service && python -m app.train

# ── Mongo ────────────────────────────────────────────────────────────────────

mongo-shell:
	docker exec -it $$(docker compose ps -q mongo) mongosh career_db
