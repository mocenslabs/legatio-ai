# ==============================================================================
# Legatio AI — Backend Makefile
# Run from backend/ with the project virtual environment activated or present.
# ===============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := .venv/bin/python

.PHONY: help install test test-cov lint format format-check typecheck check \
	migrate makemigrations runserver shell dbshell superuser

help: ## Show available backend commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install backend development dependencies
	$(PYTHON) -m pip install -r requirements/development.txt

test: ## Run backend tests with coverage
	$(PYTHON) -m pytest

test-cov: ## Run backend tests with an explicit coverage report
	$(PYTHON) -m pytest --cov=apps --cov=services --cov-report=term-missing

lint: ## Run Ruff linting and Mypy
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy .

format: ## Format Python code with Ruff Formatter
	$(PYTHON) -m ruff format .

format-check: ## Check Python formatting without modifying files
	$(PYTHON) -m ruff format --check .

typecheck: ## Run Mypy type checking
	$(PYTHON) -m mypy .

check: format-check lint test ## Run the backend quality gate

migrate: ## Apply Django migrations
	$(PYTHON) manage.py migrate

makemigrations: ## Create Django migrations
	$(PYTHON) manage.py makemigrations

runserver: ## Start Django development server
	$(PYTHON) manage.py runserver 0.0.0.0:8000

shell: ## Open Django shell
	$(PYTHON) manage.py shell

dbshell: ## Open database shell
	$(PYTHON) manage.py dbshell

superuser: ## Create a Django superuser
	$(PYTHON) manage.py createsuperuser
