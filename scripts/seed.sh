#!/usr/bin/env bash
# ============================================================
# Legatio AI - Seed Data Script (SKELETON)
# ============================================================
# Populates the development database with sample data.
# This is a Phase 0 placeholder — actual seed data is added
# incrementally as each phase completes.
#
# Planned seed data (per 03-DATA-MODEL.md Section 19):
#   - 2 users (alice@example.com, bob@example.com)
#   - 3 agents (user agent, simulated hotel agent, simulated ISP agent)
#   - 1 active constitution with 5 rules ("Madrid travel" scenario)
#   - 1 completed negotiation with full audit trail
#
# Usage: ./scripts/seed.sh
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "═══════════════════════════════════════════════"
echo "   Legatio AI — Seed Development Data"
echo "═══════════════════════════════════════════════"
echo ""

echo -e "${BLUE}[1/1]${NC} Seed script is a Phase 0 skeleton."
echo -e "${BLUE}[1/1]${NC} Real seed data will be added as phases complete:"
echo ""
echo "   Phase 2 → Users + Agents + Constitutions + Rules"
echo "   Phase 3 → Negotiation rooms + Simulated agents"
echo "   Phase 5 → Agreements + Audit trail"
echo ""
echo -e "${GREEN}✅${NC} Nothing to seed yet. Exiting cleanly."
echo ""

# Future implementation:
# cd infrastructure
# docker compose exec -T backend python manage.py loaddata seed/users.json
# docker compose exec -T backend python manage.py loaddata seed/agents.json
# docker compose exec -T backend python manage.py loaddata seed/constitutions.json
