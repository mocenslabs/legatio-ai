# Legatio Frontend — Stage 3 (MVP UI complete)

Incluye Stage 1 + 2 + :

- **Agreements**: listado, detalle, sign, verify, export JSON
- **Audit**: listado de eventos + verify chain
- **Profile**: nombre, idioma/timezone, cambio de contraseña, 2FA enable/confirm/disable
- **Login 2FA**: si el backend responde `requires_2fa`

## Backend necesario para Profile completo

2FA ya está en el backend. Para **guardar nombre** y **cambiar contraseña** aplicá el zip `backend_profile_patch` (PATCH `/auth/me/` + POST `/auth/change-password/`).

## Aplicar frontend

```bash
unzip frontend_stage3.zip -d /tmp/fe3
rsync -av /tmp/fe3/frontend_stage3/ frontend/
docker compose -f infrastructure/docker-compose.yml --env-file .env restart frontend
```

## Probar

1. Profile → editar nombre (con parche backend)
2. 2FA enable (QR + código)
3. Agreements (datos del seed)
4. Audit → verify chain
5. Login con 2FA si lo activaste
