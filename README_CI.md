# Pre-commit / CI fixes + how to run ruff and mypy

## Apply

```bash
cd ~/projects/legatio-ai-v2
unzip -o legatio-precommit-ci-fixes.zip
```

Files included:
- backend/apps/billing/models.py (SIM103)
- backend/apps/organizations/models.py (DJ012)
- backend/legatio/settings/production.py (F405 noqa)

## Checks (same spirit as CI) — Docker recommended

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  ruff check apps core legatio

docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  ruff format apps core legatio

docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  ruff check --fix apps core legatio

docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  mypy apps core legatio
```

Host alternative (from backend/ with PYTHONPATH):

```bash
cd backend
export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=legatio.settings.development
ruff check apps core legatio
ruff format apps core legatio
ruff check --fix apps core legatio
mypy apps core legatio
```

Full pre-commit:

```bash
pre-commit run --all-files
```

If pre-commit mypy fails with "No module named legatio" but Docker mypy passes, trust Docker/CI. Do not push with failing Docker mypy.

## Commit

```bash
git add -u backend/
git status
git commit -m "feat(api): harden backend for multi-tenant readiness"
```

Use the full multi-line message from the previous step if you prefer the long body.
Then: git push -u origin HEAD
