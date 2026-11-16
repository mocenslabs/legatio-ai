# Fix NameError ENCRYPTION_KEY

## Apply (from repo root)

```bash
unzip -o legatio-settings-encryption-fix.zip

# Force recreate so the container picks up host files
docker compose -f infrastructure/docker-compose.yml --env-file .env up -d --force-recreate backend

# Confirm no NameError
docker compose -f infrastructure/docker-compose.yml --env-file .env logs backend --tail 30
```

## Verify file on host

```bash
grep ENCRYPTION_KEY backend/legatio/settings/base.py
grep ENCRYPTION_KEY backend/legatio/settings/development.py
```

You should see ENCRYPTION_KEY defined in base.py and the defensive block in development.py.

## Then run tests

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  pytest tests/unit/policy_engine/test_risk.py \
         tests/unit/policy_engine/test_risk_settings.py \
         tests/unit/policy_engine/test_safe_evaluate.py \
         tests/unit/agreements/test_signing.py \
         tests/unit/agreements/test_services.py \
         tests/integration/audit/test_hash_chain_integrity.py \
         -q
```
