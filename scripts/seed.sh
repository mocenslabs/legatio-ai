#!/bin/bash
# =============================================================================
# Legatio AI — Seed MVP Data Script (DEL-036)
# =============================================================================
# Populates the development database with demo data for the MVP.
#
# Usage:
#   ./scripts/seed.sh          # Seed if not already seeded
#   ./scripts/seed.sh --force  # Force re-seed (deletes existing seed users)
# =============================================================================
set -e

echo "============================================================"
echo "Legatio AI — Seed MVP Data"
echo "============================================================"

COMPOSE="docker compose -f infrastructure/docker-compose.yml --env-file .env"

# Check if Docker is running
if ! $COMPOSE ps >/dev/null 2>&1; then
    echo "❌ Docker Compose is not running."
    echo "   Run: $COMPOSE up -d"
    exit 1
fi
echo "✓ Docker Compose is running"

# Wait for database to be ready
echo "Waiting for database..."
until $COMPOSE exec -T db pg_isready -U legatio >/dev/null 2>&1; do
    sleep 1
done
echo "✓ Database is ready"

# Run migrations
echo "Running migrations..."
$COMPOSE exec -T backend python manage.py migrate --noinput
echo "✓ Migrations complete"

# Run seed command (discovered via INSTALLED_APPS "core")
echo "Running seed command..."
$COMPOSE exec -T backend python manage.py seed_mvp "$@"

echo ""
echo "============================================================"
echo "✅ Seed complete!"
echo "============================================================"
