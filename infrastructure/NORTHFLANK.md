# Northflank notes

- API Dockerfile: `backend/Dockerfile.prod` (context `backend/`)
- Worker: same image, command `celery -A legatio worker --loglevel=info`
- See [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for env vars and Neon/Cloudflare.
