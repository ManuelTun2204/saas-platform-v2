# Auditoría rápida saas-platform-v2 - recomendación de trabajo (2026-09-28)

> Estado: working tree limpio, HEAD `3a18014`, docker APAGADO en esta PC (solo corre premium backend en :3000).
> 23 archivos `.py` (259 KB), frontend VACÍA (sin Next.js).

## Hallazgo #1 — La documentación no coincide con el sistema real
- AGENTS.md obsoleto: describe Postgres :5432, Redis :6379, dashboard Streamlit :8501 y `cd frontend && npm run dev`.
  NADA de eso existe. El docker-compose real SOLO tiene `backend` (FastAPI :8000) con volumen `./data`.
- `frontend/` vacía (0 archivos, sin package.json): el frontend real son HTML estáticos servidos por FastAPI
  (/landing, /admin/index.html, PWA /app, 7 plantillas en backend/app/templates). Fuente fiel: ESTADO-PROYECTO.md (2026-08-18).

## Hallazgo #2 — [ALTO] Persistencia JSON sin control de concurrencia
- `storage_service.py` lee/escribe JSON (tenants, leads, orders, conversations, usage) con read-modify-write
  SIN locks (0 hits de threading.Lock/asyncio.Lock). Con FastAPI async multi-request = condición de carrera:
  dos pedidos simultáneos pueden sobrescribirse/corromper el archivo. Crítico para SaaS multi-tenant.

## Hallazgo #3 — Seguridad
- `.env`/`data`/`backups` gitignoreados; grep de secretos en git = 0. JWT_SECRET_KEY obligatoria al arrancar (fix e63ff3c). OK.
- OJO: ESTADO-PROYECTO.md documenta credenciales `admin/admin123` — verificar que se rotaron, si no es puerta abierta.

## Hallazgo #4 — Sin suite de tests (solo test_generator.py smoke manual). Monstruos: website_service.py (53KB), payment_service.py + ecommerce.py (27KB c/u), pwa.py (19KB), tenants.py (21KB).

## RECOMENDACIÓN PRIORIZADA (orden de trabajo sugerido)
1. **[ALTO] Locks en storage_service.py** (asyncio.Lock por colección o migrar a SQLite/Postgres; mínimo: lock global por escritura).
2. **[MEDIO] Reescribir AGENTS.md** al sistema real (backend FastAPI + JSON + HTML estático). La doc actual confunde y hace perder tiempo.
3. **[MEDIO-ALTO] Rotar credenciales por defecto** si `admin/admin123` sigue activa; quitarlas del ESTADO-PROYECTO.md.
4. **[MEDIO] Primera suite pytest**: storage race, auth, límites de chat por plan, checkout demo.
5. **[BAJO] Partir monstruos**: website_service.py (plantillas), payment/ecommerce (lógica común).

## Decisión
- No se modificó nada. Abrir cuando el usuario diga "trabajemos en saas" — arranque recomendado: #1 locks de storage.