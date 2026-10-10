# Legatio AI — MVP Demo Script

Guide to demonstrate Legatio AI MVP (v0.1).

**Sources:** `05-ROADMAP.md` §10.3 · `01-PRD.md` §16 · DEL-036

## Prerequisites

1. Docker + Docker Compose
2. Repo cloned / extracted
3. `.env` created from `.env.example`

## Setup

```bash
# 1. Start services
docker compose -f infrastructure/docker-compose.yml --env-file .env up -d

# 2. Wait for readiness
sleep 15

# 3. Migrations
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
    python manage.py migrate --noinput

# 4. Seed demo data
./scripts/seed.sh
# Force re-seed:
# ./scripts/seed.sh --force
```

## Demo credentials

| Email             | Password  |
|-------------------|-----------|
| alice@example.com | alice1234 |
| bob@example.com   | bob1234   |

## Demo flow (API)

### 1. Login

```bash
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"alice@example.com","password":"alice1234"}' \
    | jq -r '.access // .access_token // .token')
echo "Token: ${TOKEN:0:20}..."
```

### 2. Constitution (Madrid Travel — 5 rules)

```bash
curl -s http://localhost/api/v1/constitutions/ \
    -H "Authorization: Bearer $TOKEN" | jq
```

Expected: **Madrid Travel Constitution** with rules for max €700, never share phone, large payments need approval, etc.

### 3. Completed negotiation (3 rounds)

```bash
curl -s http://localhost/api/v1/negotiations/ \
    -H "Authorization: Bearer $TOKEN" | jq

# Replace {room_id}
curl -s http://localhost/api/v1/negotiations/{room_id}/ \
    -H "Authorization: Bearer $TOKEN" | jq
```

Seeded flow:

- Round 1: €820 → REQUIRE_APPROVAL → REJECTED
- Round 2: €680 + phone → DENY (Rule #17)
- Round 3: €700, no phone → REQUIRE_APPROVAL → APPROVED

### 4. Signed agreement

```bash
curl -s http://localhost/api/v1/agreements/ \
    -H "Authorization: Bearer $TOKEN" | jq

curl -s http://localhost/api/v1/agreements/{agreement_id}/ \
    -H "Authorization: Bearer $TOKEN" | jq

curl -s http://localhost/api/v1/agreements/{agreement_id}/canonical/ \
    -H "Authorization: Bearer $TOKEN" | jq

curl -s http://localhost/api/v1/agreements/{agreement_id}/signature/ \
    -H "Authorization: Bearer $TOKEN" | jq
```

Expected: status `SIGNED`, HMAC-SHA256 signature, verified hash.

### 5. Audit trail

```bash
curl -s http://localhost/api/v1/audit/events/ \
    -H "Authorization: Bearer $TOKEN" | jq

curl -s http://localhost/api/v1/audit/entities/NegotiationRoom/{room_id}/ \
    -H "Authorization: Bearer $TOKEN" | jq

curl -s -X POST http://localhost/api/v1/audit/verify/ \
    -H "Authorization: Bearer $TOKEN" | jq
```

### 6. Export agreement

```bash
curl -s -X POST http://localhost/api/v1/agreements/{agreement_id}/export/ \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"format":"json"}' -o agreement.json
cat agreement.json | jq
```

## Features demonstrated

1. Constitution management (rules + versioning)
2. Multi-round negotiation with simulated agents
3. Policy Engine: ALLOW / DENY / REQUIRE_HUMAN_APPROVAL
4. Human approval workflow
5. Agreement: canonical JSON + cryptographic signature
6. Append-only, hash-chained audit trail
7. REST API + JWT

## MVP acceptance criteria (`01-PRD.md` §16)

- [x] Register / login
- [x] Create Constitution with ≥ 5 rules
- [x] Start negotiation
- [x] Policy Engine evaluates proposals
- [x] Forbidden actions blocked
- [x] Approval approve / reject
- [x] Agreement with hash + signature
- [x] Exportable audit trail
- [x] Use cases: Travel, Subscription, Purchase (E2E)

## E2E tests (MVP use cases)

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
    pytest tests/e2e/mvp/ -v --tb=short
```

## Coverage gate (≥ 80%)

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
    pytest tests/ \
      --cov=apps --cov=services --cov=core \
      --cov-report=term-missing \
      --cov-fail-under=80
```

## Troubleshooting

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env ps
docker compose -f infrastructure/docker-compose.yml --env-file .env logs backend --tail=100

# Reset DB + re-seed
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
    python manage.py flush --noinput
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
    python manage.py migrate --noinput
./scripts/seed.sh --force
```
