# Legatio AI — Point 4: Plans / billing (model + flags)

## What was added

- App `apps.billing`
  - **Plan** — code, price_cents, limits JSON, features JSON, external_price_id
  - **OrganizationSubscription** — org ↔ plan, status, trial, period, Stripe placeholders
  - **UsageRecord** — monthly metric counters
- Services: `ensure_default_plans`, `start_free_subscription`, `organization_has_feature`,
  `organization_within_limit`, `increment_usage`
- Flag **`BILLING_ENABLED`** (default False): when off, limits/features are not enforced
- API:
  - `GET  /api/v1/billing/plans/`
  - `GET  /api/v1/billing/organizations/{id}/subscription/`
  - `POST /api/v1/billing/organizations/{id}/subscription/start-free/`
- Command: `python manage.py seed_plans`

Default catalog: **free** / **pro** / **business**

## Apply

```bash
unzip -o legatio-point4-billing.zip

grep BILLING_ENABLED backend/legatio/settings/base.py
grep apps.billing backend/legatio/settings/base.py

# optional in .env
# BILLING_ENABLED=False

docker compose -f infrastructure/docker-compose.yml --env-file .env up -d --force-recreate backend

docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  python manage.py migrate billing

docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  python manage.py seed_plans
```

## Tests

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  pytest tests/unit/billing/ -q
```

## Notes

- No Stripe/MercadoPago yet — only data model + helpers.
- Wire `organization_within_limit` / `increment_usage` into agent creation and negotiation start when you turn `BILLING_ENABLED=True`.
- Point 2 (production deploy) is next after this.
