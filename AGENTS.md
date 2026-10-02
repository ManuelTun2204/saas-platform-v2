# SaaS Platform V2 - Guia para Opencode

## 🔴 URGENTE 2026-10-01 - LEER ANTES DE TOCAR NADA

**LO QUE DICE ESTE ARCHIVO DEBAJO ESTA MALO. NO CONFIES EN EL.**

Verificado en esta PC (no es opinion, es `Test-Path` + `docker compose config`):

| Este doc afirma | Realidad verificada |
|---|---|
| `frontend/` Next.js en 3000 | **NO EXISTE** el directorio |
| `dashboard/` Streamlit en 8501 | **NO EXISTE** el directorio |
| `docker compose exec postgres` | **NO hay servicio `postgres`** |
| `docker compose logs -f postgres` | **idem, servicio inexistente** |
| Redis en 6379 | **NO esta en el compose** |
| `curl /api/users`, `/api/sites`, `/api/templates`, `/api/ecommerce` | **NO existen** |

**Realidad (2026-10-01):** el compose declara UN solo servicio, `backend`
(FastAPI). Los endpoints que SI existen son:
`/`, `/demo`, `/health`, `/landing`,
`/api/analytics/global`, `/api/analytics/tenant/{tenant_id}`,
`/api/auth/me`, `/api/leads`, `/api/payments/config`,
`/api/domain/{tenant_id}`, `/api/domains`,
`/api/blog/{tenant_id}`, `/api/blog/{tenant_id}/all`,
`/api/chat/{tenant_id}/config`, `/api/chat-config/{tenant_id}`.
Persistencia en archivos JSON (`./data`), no en Postgres.

**Open problems (auditoria 2026-09-28, `chats/2026-09-28-auditoria-recomendacion.md`):**
1. `storage_service.py` hace JSON read-modify-write SIN locks = condicion de
   carrera entre tenants [ALTO].
2. Credenciales `admin/admin123` documentadas [ALTO].
3. Sin suite de tests (solo hay un generator).
4. `website_service.py` ~53 KB, un solo archivo gigante.

**Este proyecto NO esta vendible hoy** (ver la seccion comercial de la
memoria central). Se trabaja "despues". Cuando se retome, lo primero es
**reescribir este archivo a la realidad**; lo de abajo se conserva solo como
registro de lo que se CREIA que habia.

---

## [OBSOLETO] Regla de la casa: UN PROYECTO A LA VEZ

Decisión permanente de Manuel: **se trabaja con un solo proyecto activo a la vez.**

Este proyecto usa el **8000** (backend), que es el mismo puerto que pide
`municipal-reclutamiento` (api). Si los dos suben juntos, el segundo falla con
`port is already allocated`. Por eso no se cambian los puertos: la regla ya lo
evita.

- Al pedir este proyecto: `docker compose up -d` en este repo, verificar el
  puerto y abrir `http://localhost:8000/docs`.
- Antes de levantar otro: `docker compose stop` aquí (apaga sin borrar datos).
- El procedimiento completo por proyecto está en la skill `levantar-proyecto`
  (opencode). Este bloque es solo el recordatorio de por qué.

## Comandos Principales

### Docker (Backend)
```bash
# Levantar todo
docker compose up -d

# Rebuild backend (despues de cambios en codigo Python)
docker compose up -d --build backend

# Ver logs
docker compose logs -f backend
docker compose logs -f postgres

# Parar todo
docker compose down
```

### Frontend (Next.js - sin Docker)
```bash
# Instalar dependencias
cd frontend && npm install

# Desarrollo
npm run dev

# Build
npm run build

# Lint
npm run lint

# Typecheck
npm run typecheck
```

### Base de datos
```bash
# Conectar a Postgres
docker compose exec postgres psql -U postgres -d saas_platform

# Migraciones (si usas Alembic)
docker compose exec backend alembic upgrade head
```

## Puertos

| Servicio | Puerto | URL |
|----------|--------|-----|
| Backend API | 8000 | http://localhost:8000/docs |
| Frontend | 3000 | http://localhost:3000 |
| Dashboard Admin | 8501 | http://localhost:8501 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

## Estructura del Proyecto

```
saas-platform-v2/
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── routers/        # Endpoints API
│   │   ├── models/         # Modelos Pydantic
│   │   ├── services/       # Logica de negocio
│   │   └── main.py         # App principal
│   └── requirements.txt
├── frontend/               # Next.js Frontend
│   ├── src/
│   │   ├── app/            # App Router
│   │   ├── components/     # Componentes React
│   │   └── lib/            # Utilidades
│   └── package.json
├── dashboard/              # Dashboard Streamlit (admin)
├── docker-compose.yml
└── .env                    # Variables de entorno (gitignored)
```

## API Endpoints Principales

```bash
# Health
curl http://localhost:8000/health

# Usuarios
curl http://localhost:8000/api/users

# Sitios web
curl http://localhost:8000/api/sites

# Plantillas
curl http://localhost:8000/api/templates

# Blog
curl http://localhost:8000/api/blog

# E-commerce
curl http://localhost:8000/api/ecommerce
```

## Notas Importantes

- **.env esta gitignoreado** - nunca imprimir valores
- **Puertos en uso**: 5432 (PG), 6379 (Redis), 8000 (API), 8501 (Dashboard)
- **Despues de cambiar Python**: `docker compose up -d --build backend`
- **Despues de cambiar React/Next**: `cd frontend && npm run dev`
- **Lint**: `npm run lint` (frontend)
- **Typecheck**: `npm run typecheck` (frontend)
