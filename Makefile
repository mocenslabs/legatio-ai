# ==============================================================================
# Legatio AI — Makefile
# Convenience commands for development, testing, and quality checks.
# ==============================================================================
# Usage: make <target>
#        make help          → show all available commands
#
# NOTE: Recipes in this file MUST be indented with real TAB characters.
# ==============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
BACKEND_DIR      := backend
FRONTEND_DIR     := frontend
DOCKER_COMPOSE   := docker compose
PYTHON           := python
PYTEST           := pytest

# ==============================================================================
# HELP
# ==============================================================================
.PHONY: help
help: ## Show this help message
	@echo "Legatio AI — Available commands"
	@echo "==============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# SETUP
# ==============================================================================
.PHONY: setup
setup: ## Full project setup (env, deps, migrations, seed)
	@echo "→ Running setup script..."
	./scripts/setup.sh

.PHONY: install
install: install-backend install-frontend ## Install all dependencies (backend + frontend)

.PHONY: install-backend
install-backend: ## Install backend dependencies
	@echo "→ Installing backend dependencies..."
	cd $(BACKEND_DIR) && pip install -r requirements/development.txt
	cd $(BACKEND_DIR) && pre-commit install || true

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	@echo "→ Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install

# ==============================================================================
# DOCKER
# ==============================================================================
.PHONY: up
up: ## Start all services (attached)
	$(DOCKER_COMPOSE) up

.PHONY: up-detached
up-detached: ## Start all services (detached)
	$(DOCKER_COMPOSE) up -d

.PHONY: down
down: ## Stop all services
	$(DOCKER_COMPOSE) down

.PHONY: down-volumes
down-volumes: ## Stop all services and remove volumes (DESTRUCTIVE)
	$(DOCKER_COMPOSE) down -v

.PHONY: logs
logs: ## Tail logs from all services
	$(DOCKER_COMPOSE) logs -f

.PHONY: rebuild
rebuild: ## Rebuild and restart all containers
	$(DOCKER_COMPOSE) up -d --build

.PHONY: ps
ps: ## Show status of all services
	$(DOCKER_COMPOSE) ps

# ==============================================================================
# DATABASE
# ==============================================================================
.PHONY: migrate
migrate: ## Apply database migrations
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate

.PHONY: makemigrations
makemigrations: ## Generate new migrations
	cd $(BACKEND_DIR) && $(PYTHON) manage.py makemigrations

.PHONY: seed
seed: ## Seed database with demo data
	cd $(BACKEND_DIR) && $(PYTHON) manage.py seed

.PHONY: dbshell
dbshell: ## Open a database shell
	cd $(BACKEND_DIR) && $(PYTHON) manage.py dbshell

# ==============================================================================
# BACKEND — RUN & TEST
# ==============================================================================
.PHONY: run-backend
run-backend: ## Run Django development server
	cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver 0.0.0.0:8000

.PHONY: run-worker
run-worker: ## Run Celery worker
	cd $(BACKEND_DIR) && celery -A legatio worker -l info

.PHONY: run-beat
run-beat: ## Run Celery Beat scheduler
	cd $(BACKEND_DIR) && celery -A legatio beat -l info

.PHONY: test-backend
test-backend: ## Run backend tests
	cd $(BACKEND_DIR) && $(PYTEST)

.PHONY: test-backend-cov
test-backend-cov: ## Run backend tests with coverage
	cd $(BACKEND_DIR) && $(PYTEST) --cov=apps --cov=services --cov-report=term-missing

.PHONY: test-policy-engine
test-policy-engine: ## Run Policy Engine tests only
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit/test_policy_engine.py -v

# ==============================================================================
# FRONTEND — RUN & TEST
# ==============================================================================
.PHONY: run-frontend
run-frontend: ## Run Vue development server
	cd $(FRONTEND_DIR) && npm run dev

.PHONY: test-frontend
test-frontend: ## Run frontend unit tests
	cd $(FRONTEND_DIR) && npm test

.PHONY: test-frontend-cov
test-frontend-cov: ## Run frontend tests with coverage
	cd $(FRONTEND_DIR) && npm run test:coverage

.PHONY: build-frontend
build-frontend: ## Build frontend for production
	cd $(FRONTEND_DIR) && npm run build

# ==============================================================================
# QUALITY — LINT & FORMAT
# ==============================================================================
.PHONY: lint
lint: lint-backend lint-frontend ## Lint all code (backend + frontend)

.PHONY: lint-backend
lint-backend: ## Lint backend (ruff + mypy)
	@echo "→ Linting backend..."
	cd $(BACKEND_DIR) && ruff check .
	cd $(BACKEND_DIR) && mypy .

.PHONY: lint-frontend
lint-frontend: ## Lint frontend (eslint + type-check)
	@echo "→ Linting frontend..."
	cd $(FRONTEND_DIR) && npm run lint
	cd $(FRONTEND_DIR) && npm run type-check

.PHONY: format
format: format-backend format-frontend ## Format all code

.PHONY: format-backend
format-backend: ## Format backend (black + ruff --fix)
	@echo "→ Formatting backend..."
	cd $(BACKEND_DIR) && black .
	cd $(BACKEND_DIR) && ruff check --fix .

.PHONY: format-frontend
format-frontend: ## Format frontend (prettier)
	@echo "→ Formatting frontend..."
	cd $(FRONTEND_DIR) && npm run format

.PHONY: type-check
type-check: ## Run type checking (backend + frontend)
	cd $(BACKEND_DIR) && mypy .
	cd $(FRONTEND_DIR) && npm run type-check

# ==============================================================================
# FULL QUALITY GATE
# ==============================================================================
.PHONY: check
check: lint type-check test ## Run full quality gate (lint + type-check + tests)
	@echo "✅ All checks passed!"

.PHONY: test
test: test-backend test-frontend ## Run all tests (backend + frontend)
	@echo "✅ All tests passed!"

# ==============================================================================
# DOCS
# ==============================================================================
.PHONY: docs-check
docs-check: ## Verify all core documentation files exist
	@echo "→ Verifying documentation..."
	@test -f docs/01-PRD.md          || (echo "Missing docs/01-PRD.md" && exit 1)
	@test -f docs/02-ARCHITECTURE.md || (echo "Missing docs/02-ARCHITECTURE.md" && exit 1)
	@test -f docs/03-DATA-MODEL.md   || (echo "Missing docs/03-DATA-MODEL.md" && exit 1)
	@test -f docs/04-BUSINESS-FLOW.md|| (echo "Missing docs/04-BUSINESS-FLOW.md" && exit 1)
	@test -f docs/05-ROADMAP.md      || (echo "Missing docs/05-ROADMAP.md" && exit 1)
	@echo "✅ All documentation files present."

# ==============================================================================
# CLEAN
# ==============================================================================
.PHONY: clean
clean: ## Remove caches, build artifacts, and temp files
	@echo "→ Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/node_modules/.vite 2>/dev/null || true
	@echo "✅ Clean complete."
