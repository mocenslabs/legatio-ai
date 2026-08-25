# ============================================================
# Legatio AI - Backend Makefile
# ============================================================
# Common commands for development workflow
# Usage: make <command>
# ============================================================

.PHONY: help install test lint format check migrate makemigrations runserver shell

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements/development.txt

test: ## Run tests with coverage
	pytest --cov=apps --cov-report=term-missing

lint: ## Run linters (ruff)
	ruff check .

format: ## Format code (ruff fix)

	ruff check --fix .

typecheck: ## Run type checker (mypy)
	mypy .

check: lint typecheck test ## Run all checks (lint + typecheck + test)

makemigrations: ## Create new migrations
	python manage.py makemigrations

migrate: ## Apply migrations
	python manage.py migrate

runserver: ## Start development server
	python manage.py runserver 0.0.0.0:8000

shell: ## Open Django shell
	python manage.py shell

dbshell: ## Open database shell
	python manage.py dbshell

superuser: ## Create superuser
	python manage.py createsuperuser
