# Legatio AI — Deployment guide (Northflank + Neon + Cloudflare)

Temporary / staging production for real traffic. Monorepo-friendly: each platform builds from a **subdirectory**.

## Architecture

```text
Browser  →  Cloudflare Pages (Vue SPA)
                │  HTTPS  VITE_API_BASE_URL
                ▼
         Northflank  —  Backend (Daphne ASGI)
                │              │
                │              ├── Celery worker (same image, different command)
                │              └── Redis (Northflank addon or Upstash)
                ▼
              Neon PostgreSQL (sslmode=require)
```

| Piece | Platform | Build context |
|-------|----------|---------------|
| API + WebSockets | Northflank service | `backend/` + `Dockerfile.prod` |
| Worker | Northflank service | same image, `celery -A legatio worker` |
| DB | Neon | connection env vars only |
| Cache / broker | Northflank Redis or Upstash | `REDIS_URL` |
| Frontend | Cloudflare Pages | `frontend/` root, `npm run build` |

---

## 1. Neon

1. Create a project and database (e.g. `legatio`).
2. Copy the connection details. Prefer the **pooled** host for the web service if available.
3. Set on the backend:

```text
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_SSLMODE=require
```

Django already maps these in `legatio.settings.base.DATABASES`. Production forces SSL if `POSTGRES_SSLMODE` is unset (`require`).

---

## 2. Northflank — backend

### Service A: `legatio-api`

- **Build**: Dockerfile
  - Dockerfile path: `backend/Dockerfile.prod`
  - Build context: `backend `backend`
- **Port**: `8000`
- **Health check**: `GET /api/v1/health/` (or `/api/v1/ready/` when Redis is up)
- **Entrypoint**: `scripts/entrypoint.prod.sh` (migrate + collectstatic + Daphne)

### Service B: `legatio-worker` (recommended)

- Same image as API
- Override command:

```bash
celery -A legatio worker --loglevel=info
```

Optional beat:

```bash
celery -A legatio beat --loglevel=info
```

### Redis

Add a Redis addon on Northflank (or Upstash). Set:

```text
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://.../1
```

### Environment

Copy from `.env.production.example`. Critical:

| Variable | Notes |
|----------|--------|
| `DJANGO_SETTINGS_MODULE` | `legatio.settings.production` |
| `DJANGO_SECRET_KEY` | long random |
| `DJANGO_ALLOWED_HOSTS` | Northflank hostname + custom API domain |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Cloudflare Pages / custom app URL (`https://...`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | same origins with `https://` |
| `ENCRYPTION_KEY` | Fernet key |
| `SERVER_SIGNING_KEY` | agreement HMAC |
| `JWT_SECRET_KEY` | JWT signing |

Generate Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Custom domain (API)

Point `api.yourdomain.com` to the Northflank service. Add that host to `DJANGO_ALLOWED_HOSTS`.

---

## 3. Cloudflare Pages — frontend

1. Connect the GitHub repo.
2. **Root directory**: `frontend`
3. **Build command**: `npm ci && npm run build`
4. **Output directory**: `dist`
5. **Environment variables** (build):

```text
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_DEFAULT_LOCALE=en
```

6. After first deploy, put the Pages URL (and custom `app.yourdomain.com` if any) into backend `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

SPA routing: Cloudflare Pages serves `index.html` for unknown paths by default for most Vue setups; if 404 on refresh, enable “SPA / single-page application” fallback in Pages settings.

---

## 4. Monorepo tips

- Northflank and Cloudflare both support **subdirectory** roots — you do **not** need to split the repo.
- CI (GitHub Actions) already builds backend and frontend images separately; align production Dockerfiles with `backend/Dockerfile.prod`.
- Never build the frontend with a relative `/api` proxy assumption in production; the browser must call the **public API origin** via `VITE_API_BASE_URL`.

---

## 5. Post-deploy checklist

- [ ] `GET https://api.../api/v1/health/` → ok
- [ ] `GET https://api.../api/v1/ready/` → database + cache (+ channel layer)
- [ ] Register / login from the Pages URL (CORS)
- [ ] Create agent → constitution → negotiation smoke path
- [ ] WebSocket notifications (if used): ensure Daphne + Redis channel layer, not `runserver`
- [ ] `ENCRYPTION_KEY` / `SERVER_SIGNING_KEY` stable across restarts (do not rotate casually or old TOTP/signatures break)

---

## 6. Local production-like smoke

```bash
# From repo root — build backend prod image
docker build -f backend/Dockerfile.prod -t legatio-api:prod backend/

# Run against Neon (example)
docker run --rm -p 8000:8000 --env-file .env.production legatio-api:prod
```

Frontend:

```bash
cd frontend
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1 npm run build
npx serve dist
```

---

## 7. Known limits (temporary production)

- Single region, no multi-AZ guarantees beyond Neon/Northflank defaults.
- Celery beat is optional for MVP demos.
- File/media storage is local-container unless you add object storage later.
- Billing flag should stay `BILLING_ENABLED=False` until a provider is wired.
