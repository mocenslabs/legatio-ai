# ==============================================================================
# Legatio AI — Root Makefile
# Development, testing, and repository quality commands.
#
# Run all commands from the repository root:
#     make help
# ================================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash
ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BACKEND_DIR := $(ROOT_DIR)/backend
FRONTEND_DIR := $(ROOT_DIR)/frontend
COMPOSE_FILE := $(ROOT_DIR)/infrastructure/docker-compose.yml
BACKEND_PYTHON := $(BACKEND_DIR)/.venv/bin/python
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

.PHONY: help
help: ## Show available commands
	@echo "Legatio AI — Available commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------
.PHONY: setup install install-backend install-frontend
setup: ## Run the complete development setup
	./scripts/setup.sh

install: install-backend install-frontend ## Install all project dependencies

install-backend: ## Create/update the backend virtual environment and dependencies
	@command -v python3.12 >/dev/null || (echo "Python 3.12 is required." && exit 1)
	@test -x "$(BACKEND_PYTHON)" || python3.12 -m venv "$(BACKEND_DIR)/.venv"
	"$(BACKEND_PYTHON)" -m pip install --upgrade pip
	"$(BACKEND_PYTHON)" -m pip install -r "$(BACKEND_DIR)/requirements/development.txt"

install-frontend: ## Install frontend dependencies from the lockfile
	cd "$(FRONTEND_DIR)" && npm ci

# ------------------------------------------------------------------------------
# Docker
# ------------------------------------------------------------------------------
.PHONY: up up-detached down down-volumes logs rebuild ps
up: ## Start all Docker services in the foreground
	$(DOCKER_COMPOSE) up

up-detached: ## Start all Docker services in the background
	$(DOCKER_COMPOSE) up -d

down: ## Stop all Docker services
	$(DOCKER_COMPOSE) down

down-volumes: ## Stop services and remove persistent volumes (DESTRUCTIVE)
	$(DOCKER_COMPOSE) down -v

logs: ## Follow Docker service logs
	$(DOCKER_COMPOSE) logs -f

rebuild: ## Rebuild and restart all Docker services
	$(DOCKER_COMPOSE) up -d --build

ps: ## Show Docker service status
	$(DOCKER_COMPOSE) ps

# ------------------------------------------------------------------------------
# Database / Django
# ------------------------------------------------------------------------------
.PHONY: django-check migrations-check migrate makemigrations seed dbshell

django-check: ## Run Django system checks
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py check

migrations-check: ## Verify there are no missing migrations
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py makemigrations --check --dry-run

migrate: ## Apply Django migrations
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py migrate

makemigrations: ## Create Django migrations
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py makemigrations

seed: ## Seed development data
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py seed

dbshell: ## Open the Django database shell
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py dbshell

# ------------------------------------------------------------------------------
# Backend
# ------------------------------------------------------------------------------
.PHONY: run-backend run-worker run-beat test-backend test-backend-cov
run-backend: ## Run the Django development server
	cd "$(BACKEND_DIR)" && .venv/bin/python manage.py runserver 0.0.0.0:8000

run-worker: ## Run the Celery worker
	cd "$(BACKEND_DIR)" && .venv/bin/celery -A legatio worker -l info

run-beat: ## Run Celery Beat
	cd "$(BACKEND_DIR)" && .venv/bin/celery -A legatio beat -l info

test-backend: ## Run backend tests
	cd "$(BACKEND_DIR)" && .venv/bin/python -m pytest

test-backend-cov: ## Run backend tests with coverage
	cd "$(BACKEND_DIR)" && .venv/bin/python -m pytest --cov=apps --cov=services --cov-report=term-missing

# ------------------------------------------------------------------------------
# Frontend
# ------------------------------------------------------------------------------
.PHONY: run-frontend test-frontend test-frontend-cov build-frontend
run-frontend: ## Run the Vue development server
	cd "$(FRONTEND_DIR)" && npm run dev

test-frontend: ## Run frontend tests
	cd "$(FRONTEND_DIR)" && npm test

test-frontend-cov: ## Run frontend tests with coverage
	cd "$(FRONTEND_DIR)" && npm run test:coverage

build-frontend: ## Build the frontend for production
	cd "$(FRONTEND_DIR)" && npm run build

# ------------------------------------------------------------------------------
# Quality
# ------------------------------------------------------------------------------
.PHONY: lint lint-backend lint-frontend format format-backend format-frontend \
	format-check format-check-backend format-check-frontend type-check

lint: lint-backend lint-frontend ## Lint backend and frontend

lint-backend: ## Run Ruff and Mypy on the backend
	cd "$(BACKEND_DIR)" && .venv/bin/python -m ruff check .
	cd "$(BACKEND_DIR)" && .venv/bin/python -m mypy .

lint-frontend: ## Run ESLint and TypeScript checks on the frontend
	cd "$(FRONTEND_DIR)" && npm run lint
	cd "$(FRONTEND_DIR)" && npm run type-check

format: format-backend format-frontend ## Format backend and frontend

format-backend: ## Format Python with Ruff Formatter
	cd "$(BACKEND_DIR)" && .venv/bin/python -m ruff format .

format-frontend: ## Format frontend with Prettier
	cd "$(FRONTEND_DIR)" && npm run format

format-check: format-check-backend format-check-frontend ## Check formatting without modifying files

format-check-backend: ## Check Python formatting with Ruff Formatter
	cd "$(BACKEND_DIR)" && .venv/bin/python -m ruff format --check .

format-check-frontend: ## Check frontend formatting with Prettier
	cd "$(FRONTEND_DIR)" && npm run format:check

type-check: ## Run backend and frontend type checks
	cd "$(BACKEND_DIR)" && .venv/bin/python -m mypy .
	cd "$(FRONTEND_DIR)" && npm run type-check

# ------------------------------------------------------------------------------
# Tests / quality gate
# ------------------------------------------------------------------------------
.PHONY: test check pre-commit docs-check

test: test-backend test-frontend ## Run all backend and frontend tests

check: docs-check django-check migrations-check format-check lint test build-frontend ## Run the complete Phase 0 quality gate
	@echo ""
	@echo "✅ Phase 0 quality gate passed."

pre-commit: ## Run all pre-commit hooks against the repository
	pre-commit run --all-files

# ------------------------------------------------------------------------------
# Documentation
# ------------------------------------------------------------------------------
.PHONY: docs-check
docs-check: ## Verify the required documentation files exist
	@echo "→ Verifying documentation..."
	@test -f docs/01-PRD.md || (echo "Missing docs/01-PRD.md" && exit 1)
	@test -f docs/02-ARCHITECTURE.md || (echo "Missing docs/02-ARCHITECTURE.md" && exit 1)
	@test -f docs/03-DATA-MODEL.md || (echo "Missing docs/03-DATA-MODEL.md" && exit 1)
	@test -f docs/04-BUSINESS-FLOW.md || (echo "Missing docs/04-BUSINESS-FLOW.md" && exit 1)
	@test -f docs/05-ROADMAP.md || (echo "Missing docs/05-ROADMAP.md" && exit 1)
	@echo "✅ Documentation structure is complete."

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------
.PHONY: clean
clean: ## Remove local caches and generated artifacts
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -prune -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf "$(FRONTEND_DIR)/dist" "$(FRONTEND_DIR)/node_modules/.vite"
	@echo "✅ Cleanup complete."
