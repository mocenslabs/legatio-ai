#!/usr/bin/env bash
# ==============================================================================
# Legatio AI — One-Command Development Setup
#
# Prepares the local Python/Node environments, starts Docker infrastructure,
# applies migrations, and runs the Phase 0 quality gate.
# ===============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { printf '%b[%s]%b %s\n' "$BLUE" "$(date +%H:%M:%S)" "$NC" "$1"; }
ok()   { printf '%b[%s]%b ✅ %s\n' "$GREEN" "$(date +%H:%M:%S)" "$NC" "$1"; }
warn() { printf '%b[%s]%b ⚠️  %s\n' "$YELLOW" "$(date +%H:%M:%S)" "$NC" "$1"; }
fail() { printf '%b[%s]%b ❌ %s\n' "$RED" "$(date +%H:%M:%S)" "$NC" "$1"; exit 1; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose.yml"
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"

cd "$PROJECT_ROOT"

printf '\n'
printf '%s\n' '═══════════════════════════════════════════════'
printf '%s\n' '   Legatio AI — Development Environment Setup'
printf '%s\n' '═══════════════════════════════════════════════'
printf '\n'

# ------------------------------------------------------------------------------
# 1. Required tools
# ------------------------------------------------------------------------------
log '[1/8] Verifying required tools...'
command -v python3.12 >/dev/null 2>&1 || fail 'Python 3.12 is required.'
command -v node >/dev/null 2>&1 || fail 'Node.js is required.'
command -v npm >/dev/null 2>&1 || fail 'npm is required.'
command -v docker >/dev/null 2>&1 || fail 'Docker is required.'
docker compose version >/dev/null 2>&1 || fail 'Docker Compose is required.'

PYTHON_VERSION="$(python3.12 --version 2>&1)"
NODE_VERSION="$(node --version)"
ok "$PYTHON_VERSION"
ok "Node.js $NODE_VERSION"
ok "$(docker compose version --short | sed 's/^/Docker Compose /')"

# ------------------------------------------------------------------------------
# 2. Backend virtual environment and dependencies
# ------------------------------------------------------------------------------
log '[2/8] Preparing backend virtual environment...'
if [ ! -x "$PYTHON_BIN" ]; then
    python3.12 -m venv "$BACKEND_DIR/.venv"
    ok 'Created backend/.venv'
else
    ok 'backend/.venv already exists'
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$BACKEND_DIR/requirements/development.txt"
ok 'Backend dependencies installed'

# ------------------------------------------------------------------------------
# 3. Frontend dependencies
# ------------------------------------------------------------------------------
log '[3/8] Installing frontend dependencies...'
cd "$FRONTEND_DIR"
npm ci
cd "$PROJECT_ROOT"
ok 'Frontend dependencies installed'

# ------------------------------------------------------------------------------
# 4. Pre-commit
# ------------------------------------------------------------------------------
log '[4/8] Installing pre-commit hooks...'
"$PYTHON_BIN" -m pre_commit install
ok 'Pre-commit hooks installed'

# ------------------------------------------------------------------------------
# 5. Environment files
# ------------------------------------------------------------------------------
log '[5/8] Verifying environment files...'
if [ ! -f "$PROJECT_ROOT/infrastructure/.env" ]; then
    warn 'infrastructure/.env not found; creating development defaults'
    cat > "$PROJECT_ROOT/infrastructure/.env" <<'ENVEOF'
DB_NAME=legatio
DB_USER=legatio
DB_PASSWORD=legatio
SECRET_KEY=django-insecure-dev-only-key-change-in-production
DEBUG=True
ENVEOF
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

if [ ! -f "$FRONTEND_DIR/.env" ]; then
    cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
fi
ok 'Environment files ready'

# ------------------------------------------------------------------------------
# 6. Docker services
# ------------------------------------------------------------------------------
log '[6/8] Starting Docker services...'
docker compose -f "$COMPOSE_FILE" up -d --build
ok 'Docker services started'

# ------------------------------------------------------------------------------
# 7. Database and Django checks
# ------------------------------------------------------------------------------
log '[7/8] Applying migrations and checking Django...'
docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate
"$PYTHON_BIN" "$BACKEND_DIR/manage.py" check
"$PYTHON_BIN" "$BACKEND_DIR/manage.py" makemigrations --check --dry-run
ok 'Django checks and migrations passed'

# ------------------------------------------------------------------------------
# 8. Phase 0 quality gate
# ------------------------------------------------------------------------------
log '[8/8] Running Phase 0 quality gate...'
make --no-print-directory check

printf '\n'
printf '%s\n' '═══════════════════════════════════════════════'
ok 'Legatio AI development environment is ready.'
printf '%s\n' '═══════════════════════════════════════════════'
printf '\n'
printf '%s\n' '  Django admin: http://localhost:8000/admin'
printf '%s\n' '  Frontend:     http://localhost:5173'
printf '\n'
printf '%s\n' '  Stop services: make down'
printf '%s\n' '  View logs:     make logs'
printf '%s\n' '  Run checks:    make check'
printf '%s\n' '  Pre-commit:    make pre-commit'
