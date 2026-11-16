# Legatio AI — API v1 (mínima)

Base URL local: `http://localhost:8000/api/v1/`

## Documentación interactiva

| Recurso | URL |
|---------|-----|
| OpenAPI schema (JSON) | `/api/v1/schema/` |
| Swagger UI | `/api/v1/docs/` |
| ReDoc | `/api/v1/redoc/` |
| API root (índice) | `/api/v1/` |

## Auth

1. `POST /api/v1/auth/register/` — crear usuario
2. `POST /api/v1/auth/login/` — obtener access + refresh JWT
3. Header: `Authorization: Bearer <access_token>`
4. WebSocket: `ws://localhost:8000/ws/notifications/?token=<access_token>`

## Errores (formato estándar)

```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid email or password.",
    "details": {}
  }
}
```

## Health

- Liveness: `GET /api/v1/health/`
- Readiness: `GET /api/v1/ready/` → `{ database, cache, channel_layer }`

## Recursos principales

- `agents`, `constitutions`, `negotiations`, `approvals`, `agreements`, `audit`
- Ver Swagger para request/response schemas generados desde el código.
