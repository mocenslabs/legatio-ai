# =============================================================================
# Legatio AI — Monorepo Makefile
# =============================================================================
# Usage: make help
# =============================================================================

COMPOSE_FILE ?= infrastructure/docker-compose.yml
ENV_FILE     ?= .env
COMPOSE      := docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE)

.PHONY: help setup env up down restart logs ps \
        backend-shell frontend-shell seed migrate \
        test test-backend test-frontend \
        lint lint-backend lint-frontend format \
        build ci-local clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

setup: ## Full local bootstrap (env, build, up, migrate, seed)
	@bash scripts/setup.sh

env: ## Create .env from .env.example if missing
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example — review secrets before production use."; \
	else \
		echo ".env already exists"; \
	fi

# ---------------------------------------------------------------------------
# Docker Compose
# ---------------------------------------------------------------------------

up: ## Start all services (detached)
	$(COMPOSE) up -d

down: ## Stop services (keep volumes)
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

logs: ## Tail logs (all services)
	$(COMPOSE) logs -f --tail=200

ps: ## Show running containers
	$(COMPOSE) ps

build: ## Rebuild images
	$(COMPOSE) build

# ---------------------------------------------------------------------------
# App helpers
# ---------------------------------------------------------------------------

backend-shell: ## Shell inside backend container
	$(COMPOSE) exec backend bash

frontend-shell: ## Shell inside frontend container
	$(COMPOSE) exec frontend sh

migrate: ## Run Django migrations
	$(COMPOSE) exec backend python manage.py migrate --noinput

seed: ## Seed MVP demo data (use SEED_FORCE=1 to force)
	@if [ "$(SEED_FORCE)" = "1" ]; then \
		./scripts/seed.sh --force; \
	else \
		./scripts/seed.sh; \
	fi

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

lint-backend: ## Ruff + format check + mypy
	$(COMPOSE) exec backend ruff check .
	$(COMPOSE) exec backend ruff format --check .
	$(COMPOSE) exec backend mypy .

lint-frontend: ## ESLint + type-check
	$(COMPOSE) exec frontend npx eslint . --max-warnings=0
	$(COMPOSE) exec frontend npm run type-check

lint: lint-backend lint-frontend ## Lint backend + frontend

format: ## Auto-format backend (ruff) + frontend (prettier)
	$(COMPOSE) exec backend ruff check --fix .
	$(COMPOSE) exec backend ruff format .
	$(COMPOSE) exec frontend npm run format || true

test-backend: ## Pytest with coverage gate 80%
	$(COMPOSE) exec backend pytest \
		--cov=apps --cov=services --cov=core \
		--cov-report=term-missing --cov-fail-under=80

test-frontend: ## Frontend production build (type-check included)
	$(COMPOSE) exec frontend npm run build

test: test-backend ## Run backend tests (alias)

ci-local: lint test-backend test-frontend ## Approximate CI checks locally

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Stop stack and remove containers (volumes kept)
	$(COMPOSE) down --remove-orphans

clean-volumes: ## DANGER: stop stack and delete volumes (wipes DB)
	$(COMPOSE) down -v --remove-orphans
