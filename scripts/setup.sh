#!/usr/bin/env bash
# ==============================================================================
# Legatio AI — Development Setup Script
# ==============================================================================
# Sets up the full development environment:
#   1. Verifies prerequisites (Docker, Python, Node, Git)
#   2. Creates .env from .env.example if it doesn't exist
#   3. Installs backend dependencies (venv + pip + pre-commit)
#   4. Installs frontend dependencies (npm)
#   5. Starts infrastructure services (PostgreSQL, Redis)
#   6. Runs database migrations (if backend is scaffolded)
#
# This script is IDEMPOTENT — you can run it multiple times safely.
#
# Usage:
#   ./scripts/setup.sh
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Colors & helpers
# ------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}→${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
error()   { echo -e "${RED}✗${NC} $1"; }

# Resolve project root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# ------------------------------------------------------------------------------
# Step 1: Check prerequisites
# ------------------------------------------------------------------------------
info "Checking prerequisites..."

MISSING=0

command -v git >/dev/null 2>&1 || { error "git is not installed"; MISSING=1; }
command -v docker >/dev/null 2>&1 || { error "docker is not installed"; MISSING=1; }
command -v python3 >/dev/null 2>&1 || { error "python3 is not installed"; MISSING=1; }
command -v node >/dev/null 2>&1 || { error "node is not installed"; MISSING=1; }
command -v npm >/dev/null 2>&1 || { error "npm is not installed"; MISSING=1; }

# Check docker compose (v2 plugin or standalone)
if command -v docker >/dev/null 2>&1; then
    if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
        error "docker compose is not available"
        MISSING=1
    fi
fi

if [ "${MISSING}" -eq 1 ]; then
    error "Missing prerequisites. Please install them and re-run this script."
    exit 1
fi

success "All prerequisites found."

# Show versions
info "Tool versions:"
echo "    git:    $(git --version | awk '{print $3}')"
echo "    docker: $(docker --version | awk '{print $3}' | tr -d ',')"
echo "    python: $(python3 --version | awk '{print $2}')"
echo "    node:   $(node --version)"
echo "    npm:    $(npm --version)"

# ------------------------------------------------------------------------------
# Step 2: Create .env if it doesn't exist
# ------------------------------------------------------------------------------
if [ ! -f .env ]; then
    info "Creating .env from .env.example..."
    cp .env.example .env
    success ".env created."
    warn "Remember to update DJANGO_SECRET_KEY for anything beyond local dev."
else
    success ".env already exists — skipping."
fi

# ------------------------------------------------------------------------------
# Step 3: Backend setup
# ------------------------------------------------------------------------------
if [ -d "backend" ]; then
    info "Setting up backend..."

    cd backend

    if [ ! -d ".venv" ]; then
        info "Creating Python virtual environment..."
        python3 -m venv .venv
    fi

    # Activate venv for this script's context
    # shellcheck disable=SC1091
    source .venv/bin/activate

    info "Upgrading pip..."
    pip install --upgrade pip --quiet

    if [ -f "requirements/development.txt" ]; then
        info "Installing backend dependencies..."
        pip install -r requirements/development.txt --quiet
    else
        warn "requirements/development.txt not found — skipping dependency install."
    fi

    # Install pre-commit hooks if configured
    if [ -f ".pre-commit-config.yaml" ] || [ -f "../.pre-commit-config.yaml" ]; then
        if command -v pre-commit >/dev/null 2>&1; then
            info "Installing pre-commit hooks..."
            pre-commit install
        else
            warn "pre-commit not installed — run 'pip install pre-commit' to enable hooks."
        fi
    fi

    deactivate
    cd "${PROJECT_ROOT}"
    success "Backend setup complete."
else
    warn "backend/ directory not found — skipping backend setup."
fi

# ------------------------------------------------------------------------------
# Step 4: Frontend setup
# ------------------------------------------------------------------------------
if [ -d "frontend" ]; then
    info "Setting up frontend..."
    cd frontend

    if [ -f "package.json" ]; then
        info "Installing frontend dependencies..."
        npm install
    else
        warn "package.json not found — skipping npm install."
    fi

    cd "${PROJECT_ROOT}"
    success "Frontend setup complete."
else
    warn "frontend/ directory not found — skipping frontend setup."
fi

# ------------------------------------------------------------------------------
# Step 5: Start infrastructure (PostgreSQL, Redis)
# ------------------------------------------------------------------------------
if [ -f "docker-compose.yml" ]; then
    info "Starting infrastructure services (postgres, redis)..."
    docker compose up -d postgres redis
    success "Infrastructure services started."
else
    warn "docker-compose.yml not found — skipping infrastructure startup."
fi

# ------------------------------------------------------------------------------
# Step 6: Run migrations (if backend is scaffolded)
# ------------------------------------------------------------------------------
if [ -d "backend" ] && [ -f "backend/manage.py" ]; then
    info "Waiting for database to be ready..."
    sleep 5

    info "Running database migrations..."
    cd backend
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python manage.py migrate
    deactivate
    cd "${PROJECT_ROOT}"
    success "Migrations applied."
else
    warn "backend/manage.py not found — skipping migrations."
fi

# ------------------------------------------------------------------------------
# Done
# ------------------------------------------------------------------------------
echo ""
success "Legatio AI development environment is ready! 🏛️"
echo ""
echo "Next steps:"
echo "  • Start all services:      make up"
echo "  • Seed demo data:          make seed"
echo "  • Run backend tests:       make test-backend"
echo "  • Run all quality checks:  make check"
echo "  • View all commands:       make help"
echo ""
echo "Happy building!"
