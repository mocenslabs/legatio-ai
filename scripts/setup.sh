#!/usr/bin/env bash
# =============================================================================
# Legatio AI — Local development setup
# =============================================================================
# Idempotent bootstrap for the monorepo.
# Usage (from repo root):
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
#   ./scripts/setup.sh --seed-force
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-infrastructure/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env}"
SEED_FORCE=0

for arg in "$@"; do
  case "$arg" in
    --seed-force|-f) SEED_FORCE=1 ;;
    --help|-h)
      echo "Usage: ./scripts/setup.sh [--seed-force]"
      exit 0
      ;;
  esac
done

COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32mOK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARN\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mERROR\033[0m %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

log "Checking prerequisites"
need_cmd docker
need_cmd git
if ! docker compose version >/dev/null 2>&1; then
  die "Docker Compose v2 required (docker compose)"
fi
ok "docker + compose available"

if [ ! -f "$COMPOSE_FILE" ]; then
  die "Compose file not found: $COMPOSE_FILE"
fi

log "Environment file"
if [ ! -f "$ENV_FILE" ]; then
  if [ -f .env.example ]; then
    cp .env.example "$ENV_FILE"
    ok "Created $ENV_FILE from .env.example"
    warn "Review $ENV_FILE — replace placeholder secrets for anything beyond local dev"
  else
    die ".env.example not found; cannot create $ENV_FILE"
  fi
else
  ok "$ENV_FILE already exists"
fi

# Generate a local Django secret if still placeholder
if grep -q '__DJANGO_SECRET_KEY__\|changeme\|replace-me' "$ENV_FILE" 2>/dev/null; then
  if command -v openssl >/dev/null 2>&1; then
    NEW_SECRET="$(openssl rand -hex 32)"
    # portable-ish replace of common placeholder
    if grep -q '__DJANGO_SECRET_KEY__' "$ENV_FILE"; then
      sed -i.bak "s/__DJANGO_SECRET_KEY__/${NEW_SECRET}/" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
      ok "Generated DJANGO_SECRET_KEY in $ENV_FILE"
    else
      warn "Placeholder secret detected — set DJANGO_SECRET_KEY manually if needed"
    fi
  else
    warn "openssl not found; leave secrets as in .env.example for local only"
  fi
fi

log "Building and starting containers"
"${COMPOSE[@]}" up -d --build
ok "Stack is up"

log "Waiting for backend health"
ATTEMPTS=0
MAX_ATTEMPTS=60
until "${COMPOSE[@]}" exec -T backend python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/')" \
  >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
    warn "Backend health check timed out — continuing; run migrate/seed manually if needed"
    break
  fi
  sleep 2
done
if [ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]; then
  ok "Backend is healthy"
fi

log "Running migrations"
"${COMPOSE[@]}" exec -T backend python manage.py migrate --noinput
ok "Migrations applied"

log "Seeding MVP data"
if [ -x scripts/seed.sh ]; then
  if [ "$SEED_FORCE" -eq 1 ]; then
    ./scripts/seed.sh --force
  else
    ./scripts/seed.sh || ./scripts/seed.sh --force
  fi
  ok "Seed completed"
else
  warn "scripts/seed.sh not found or not executable — skip seed"
fi

log "Summary"
echo ""
echo "  Frontend (Vite):  http://localhost:5173"
echo "  API (backend):    http://localhost:8000/api/v1/health/"
echo "  Via nginx (if up): http://localhost/  (stop host Apache if port 80 conflicts)"
echo ""
echo "  Demo login (after seed): alice@example.com / alice1234"
echo ""
echo "  Useful commands:"
echo "    make up | make down | make logs | make lint | make test-backend"
echo "    make seed SEED_FORCE=1"
echo ""
ok "Setup finished"
