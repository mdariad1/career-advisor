.PHONY: dev dev-up dev-clean down down-all logs build up test test-backend test-nlp test-frontend lint

# ── Development ──────────────────────────────────────────────────────────────

# Foreground (interactive logs, Ctrl-C to stop)
dev:
	docker compose -f docker-compose.dev.yml up --build

# Detached — recreate containers so env-var changes take effect (most common workflow)
dev-up:
	docker compose -f docker-compose.dev.yml up -d --force-recreate

# Nuclear reset: tears down prod + dev networks/containers then starts dev fresh.
# Use when you hit network conflicts from accidentally running `make up` (prod).
dev-clean:
	docker compose down --remove-orphans || true
	docker compose -f docker-compose.dev.yml down --remove-orphans || true
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

# Stop and remove containers from both compose files (clears network conflicts)
down-all:
	docker compose down --remove-orphans || true
	docker compose -f docker-compose.dev.yml down --remove-orphans

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
