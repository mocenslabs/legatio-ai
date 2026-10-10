# Legatio Frontend — Stage 2

Extiende Stage 1 con:

- **Constitutions**: listado, detalle, alta
- **Negotiations**: listado, detalle, alta, start, process_round, proposals
- **Approvals**: pendientes, approve / reject
- **Responsive**: sidebar drawer en mobile + tablas con scroll
- **Tema claro / oscuro**: `data-theme` + CSS variables (sin hardcode en Vue)
- i18n ampliado (en/es)

## Aplicar

Sobre el frontend ya con Stage 1:

```bash
unzip frontend_stage2.zip -d /tmp/fe2
rsync -av /tmp/fe2/frontend_stage2/ frontend/
# No hace falta npm install si no cambió package.json

docker compose -f infrastructure/docker-compose.yml --env-file .env restart frontend
# o rebuild si preferís
```

Si el volumen de node_modules ya tiene Stage 1 deps, no necesitás reinstalar.

## Probar

1. Login con alice@example.com
2. Toggle **Light / Dark** y **EN / ES**
3. Reducí el viewport → menú ☰
4. Constitutions → ver seed "Madrid Travel Constitution"
5. Negotiations → abrir sala seed → Start / Process round
6. Approvals → aprobar / rechazar pendientes

## Stage 3

Agreements (sign/export) + Audit trail + notificaciones WebSocket.
