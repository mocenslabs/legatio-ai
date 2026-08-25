#!/usr/bin/env bash
# ============================================================
# Legatio AI - One-Command Development Setup
# ============================================================
# This script sets up the complete development environment.
# Usage: ./scripts/setup.sh
# ============================================================

set -euo pipefail

# ──────────────────────────────────────────────
# Colors & helpers
# ──────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
ok()    { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} ✅ $1"; }
warn()  { echo -e "${YELLOW}[$(date +%H:%M:%S)]${NC} ⚠️  $1"; }
fail()  { echo -e "${RED}[$(date +%H:%M:%S)]${NC} ❌ $1"; exit 1; }

# Project root is one level up from this script
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "═══════════════════════════════════════════════"
echo "   Legatio AI — Development Environment Setup"
echo "═══════════════════════════════════════════════"
echo ""

# ──────────────────────────────────────────────
# Step 1: Verify Docker
# ──────────────────────────────────────────────
log "[1/6] Verifying Docker..."
command -v docker >/dev/null 2>&1 || fail "Docker is not installed. Visit https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 || fail "Docker Compose is not installed."
ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
ok "Docker Compose $(docker compose version --short)"

# ──────────────────────────────────────────────
# Step 2: Verify .env files
# ──────────────────────────────────────────────
log "[2/6] Verifying environment files..."
if [ ! -f "infrastructure/.env" ]; then
    warn "infrastructure/.env not found — creating from defaults"
    cat > infrastructure/.env <<EOF
DB_NAME=legatio
DB_USER=legatio
DB_PASSWORD=legatio
SECRET_KEY=django-insecure-dev-only-key-change-in-production
DEBUG=True
EOF
fi
ok "Environment files ready"

# ──────────────────────────────────────────────
# Step 3: Start infrastructure (PostgreSQL + Redis)
# ──────────────────────────────────────────────
log "[3/6] Starting infrastructure (PostgreSQL + Redis)..."
cd infrastructure
docker compose up -d postgres redis
cd "$PROJECT_ROOT"

log "Waiting for services to become healthy..."
sleep 5
ok "PostgreSQL and Redis are up"

# ──────────────────────────────────────────────
# Step 4: Build & start backend
# ──────────────────────────────────────────────
log "[4/6] Building and starting backend..."
cd infrastructure
docker compose build backend
docker compose up -d backend celery-worker celery-beat
cd "$PROJECT_ROOT"
ok "Backend services started"

# ──────────────────────────────────────────────
# Step 5: Run migrations
# ──────────────────────────────────────────────
log "[5/6] Running database migrations..."
cd infrastructure
docker compose exec -T backend python manage.py migrate
cd "$PROJECT_ROOT"
ok "Migrations applied"

# ──────────────────────────────────────────────
# Step 6: Verify health
# ──────────────────────────────────────────────
log "[6/6] Verifying services..."
cd infrastructure
docker compose ps
cd "$PROJECT_ROOT"

echo ""
echo "═══════════════════════════════════════════════"
ok "Setup complete!"
echo "═══════════════════════════════════════════════"
echo ""
echo "  Django admin:    http://localhost:8000/admin"
echo "  API docs:        http://localhost:8000/api/docs/"
echo ""
echo "  Useful commands:"
echo "    View logs:      cd infrastructure && docker compose logs -f"
echo "    Stop services:  cd infrastructure && docker compose down"
echo "    Restart all:    cd infrastructure && docker compose restart"
echo ""
