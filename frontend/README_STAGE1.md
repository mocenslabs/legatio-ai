# Legatio Frontend — Stage 1 (Auth + Shell)

## Qué incluye

- Vue 3 + TypeScript + Vite
- Vue Router (guards auth / guest)
- Pinia (`auth`, `locale`)
- Axios client con Bearer JWT
- vue-i18n (`en` / `es`) desde el día 0
- TanStack Vue Query (plugin montado; queries en Stage 2)
- Layout app (sidebar + header) + pantallas Login / Register / Dashboard
- **CSS sin hardcode en `.vue`**: todo en `src/assets/styles/` importado desde `main.css`

## Cómo aplicar sobre el monorepo

Desde la raíz del monorepo:

```bash
# Respaldo opcional
cp -a frontend frontend.bak 2>/dev/null || true

# Copiar Stage 1 (ajustá la ruta del zip descomprimido)
rsync -av /tmp/frontend_stage1/ frontend/
# o: unzip y copiá el contenido de frontend_stage1/ → frontend/

cd frontend
cp .env.example .env
# Ajustá VITE_API_BASE_URL si hace falta (detrás de nginx: /api/v1)

npm install
```

Si usás Docker Compose, rebuild del servicio frontend:

```bash
docker compose -f infrastructure/docker-compose.yml --env-file .env up -d --build frontend
```

## Probar

1. Backend + seed corriendo (`./scripts/seed.sh`)
2. Abrí el frontend (puerto 5173 o vía nginx)
3. Login: `alice@example.com` / `alice1234`
4. Cambiá idioma EN/ES con el switch
5. Navegación del shell y logout

## Estructura

```
src/
  api/           # HTTP clients
  assets/styles/ # Única fuente de estilos
  components/    # UI reutilizable
  composables/
  i18n/          # locales en/es
  router/
  stores/
  types/
  views/
  utils/
```

## Stage 2 (próximo)

Constitutions, Negotiations, Approvals (CRUD + acciones API reales).
