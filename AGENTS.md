# SaaS Platform V2 - Guia para Opencode

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
