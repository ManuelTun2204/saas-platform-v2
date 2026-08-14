# SaaS Platform V2

Plataforma SaaS multi-tenant para generación de sitios web con IA, chatbot RAG, SEO y captura de leads.

## Stack

- **Backend**: Python 3.11 + FastAPI + Uvicorn
- **IA**: OpenRouter (LLM) + ChromaDB + sentence-transformers (embeddings CPU-only)
- **Emails**: Resend
- **Almacenamiento**: JSON en disco (temporal, ver roadmap) + archivos en `data/`
- **Deploy local**: Docker Compose (imagen ~2.85GB)

## Requisitos

- Docker Desktop (Windows) o Docker Engine (Linux)
- Claves en `.env` (ver `.env.example`)

## Configuración

Copia `.env.example` a `.env` y completa las claves:

| Variable | Uso |
|---|---|
| `OPENROUTER_API_KEY` | LLM (generación de sitios y chatbot) |
| `RESEND_API_KEY` | Notificaciones de leads por email |
| `ADMIN_EMAIL` | Destinatario de las notificaciones de lead |
| `JWT_SECRET_KEY` | Firma de tokens JWT (obligatoria; si falta, se genera una aleatoria que invalida sesiones al reiniciar) |
| `ALLOWED_ORIGINS` | Orígenes permitidos para CORS (separados por coma; `*` = todos) |
| `PUBLIC_URL` | URL pública de la app; se usa en emails y en el código de embed del widget |
| `PAYMENT_PROVIDERS` | Pasarelas habilitadas: `all` o `stripe,mercadopago,paypal` |
| `STRIPE_SECRET_KEY` | Clave de Stripe (test: `sk_test_...`). Vacía = pasarela desactivada |
| `MP_ACCESS_TOKEN` | Token de Mercado Pago (sandbox: `TEST-...`). Vacía = pasarela desactivada |
| `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` | Credenciales de PayPal (sandbox). Vacías = pasarela desactivada |
| `PRICE_FULL` / `PRICE_WEB_CHAT` / `PRICE_CHAT_ONLY` | Precios en USD de los paquetes (defaults: 399 / 249 / 99) |

> **Pagos:** si no configuras ninguna pasarela, el sistema usa **modo demo** (pago simulado): el checkout se completa al instante y la entrega se genera, ideal para probar todo el flujo sin cuentas.

`.env` está gitignoreado y nunca se sube al repositorio.

## Iniciar / Detener

Opciones en el menú interactivo `dev.ps1` (PowerShell):

```
[1]  Iniciar servicios con Docker (build + up)
[2]  Detener servicios Docker
[3]  Ver logs del backend en vivo
[4]  Reiniciar servicios Docker
[5]  Ver estado del sistema (health check)
[6]  Ejecutar backend local (uvicorn, sin Docker)
[7]  Hacer backup de datos
[8]  Ver estado de git
[9]  Crear commit de cambios
[0]  Salir
```

O directamente:

```powershell
docker compose up -d --build backend   # build + iniciar
docker compose down                     # detener
```

El contenedor sigue corriendo aunque cierres la ventana de PowerShell: no es necesario mantenerla abierta.

Panel de administración: **http://localhost:8000/** (login con usuario admin).

## Estructura de datos (`data/`)

| Ruta | Contenido |
|---|---|
| `data/users.json` | Usuarios (PBKDF2, nunca se expone `password_hash`) |
| `data/tenants.json` | Empresas/tenants |
| `data/storage/conversations.json` | Conversaciones del chatbot |
| `data/storage/leads.json` | Leads capturados |
| `data/websites/<tenant>/` | Sitios generados (servidos en `/data/websites/...`) |
| `data/tenants/<tenant>/documents` | Documentos subidos para RAG |
| `data/exports/` | Exportaciones ZIP |
| `data/tenants/<tenant>/vector_db/` | Índices vectoriales ChromaDB |

Solo `data/websites` y `data/exports` se sirven por HTTP (montados en `/data/websites` y `/data/exports`). El resto de `data/` no es accesible públicamente.

## API (resumen)

Autenticación: header `Authorization: Bearer <access_token>`.

| Endpoint | Método | Acceso | Función |
|---|---|---|---|
| `/api/auth/login` | POST | Público | Login (emite access + refresh) |
| `/api/auth/refresh` | POST | Público* | Renovar tokens con refresh token |
| `/api/auth/register` | POST | Admin | Crear usuario |
| `/api/auth/me` | GET | Autenticado | Info del usuario actual |
| `/api/users` | GET/POST | Admin | Listar/crear usuarios |
| `/api/users/{username}` | DELETE | Admin | Eliminar usuario (no a sí mismo) |
| `/api/tenants` | GET/POST | Autenticado | Listar/crear tenants |
| `/api/tenants/{tenant_id}` | DELETE | Autenticado | Eliminar tenant |
| `/api/generate/{tenant_id}` | POST | Autenticado | Generar sitio web con IA |
| `/api/documents/upload/{tenant_id}` | POST | Autenticado | Subir documento para RAG (max 10MB, .txt/.pdf) |
| `/api/chat/{tenant_id}` | POST | Público* | Chatbot RAG (rate limit 20/min por IP) |
| `/api/tenant/{tenant_id}/details` | GET | Autenticado | Detalles de un tenant |
| `/api/export/{tenant_id}` | POST | Autenticado | Exportar sitio a ZIP |
| `/api/site-editor/{tenant_id}` | GET/POST | Autenticado | Leer/actualizar datos del sitio |
| `/api/analytics/global` | GET | Autenticado | Métricas y gráficas del dashboard |
| `/api/payments/config` | GET | Público | Pasarelas disponibles + precios de paquetes |
| `/api/payments/checkout` | POST | Autenticado | Crear tenant + orden + redirigir a la pasarela |
| `/api/payments/status/{order_id}` | GET | Público* | Estado de una orden (rate limit) |
| `/api/payments/finalize/{order_id}` | POST | Público* | Generar la entrega cuando la orden está pagada (idempotente) |
| `/health` | GET | Público | Health check |

\* el refresh valida que el token sea de tipo `refresh`; el chat valida que el usuario (vía email) exista en el vectorstore del tenant; `status`/`finalize` son públicos con rate limit porque el cliente los usa desde la página de retorno del checkout.

## Pagos integrados

Flujo (funciona en localhost con el **modo demo** y en producción con pasarelas reales):

1. El cliente elige paquete y método de pago en el panel → `POST /api/payments/checkout`.
2. Se crea el tenant (estado `pending`) + la orden en `data/storage/orders.json` y se redirige a la pasarela (Stripe Checkout, Mercado Pago o PayPal).
3. Al regresar, `/checkout-return` consulta `GET /api/payments/status/{order_id}` (polling cada 2s).
4. Al confirmarse el pago, `POST /api/payments/finalize/{order_id}` genera la entrega (web/chatbot/SEO) y marca el tenant como `paid`.

- **Stripe**: usa Checkout Sessions y se verifica consultando la sesión (sin webhooks → funciona en localhost).
- **Mercado Pago**: crea una preferencia con `external_reference = order_id` y se verifica buscando el pago aprobado.
- **PayPal**: crea una orden `CAPTURE` y se captura al confirmar.
- **Demo**: si no hay claves configuradas, el pago se simula y la entrega se genera al instante.

Para activar una pasarela real solo hay que poner las claves en `.env` y reconstruir: `docker compose up -d --build backend`.

## Widget de chatbot

El widget (`/static/widget/widget.js`) se incrusta en sitios de terceros:

```html
<script>var CHATBOT_TENANT_ID = "tu-tenant-id";</script>
<script src="<PUBLIC_URL>/static/widget/widget.js"></script>
```

El widget detecta automáticamente el origen desde el que se carga, por lo que funciona embebido en cualquier dominio sin configuración adicional.

## Seguridad aplicada

- `/data` completo ya no se sirve por HTTP (solo `/data/websites` y `/data/exports`)
- CORS con `allow_credentials=False` y orígenes configurables
- Endpoints duplicados sin auth eliminados; `upload`, `export`, `details`, `analytics` requieren token
- Rate limit en `/api/chat` (20 req/min por IP)
- Upload limitado a 10MB con nombre de archivo saneado
- `get_current_user` verifica que el usuario exista y usa su rol actual (revocación inmediata)
- Escritura atómica de JSON (temp + `os.replace`) contra corrupción con 2 workers
- Historial de Git purgado de datos sensibles (`data/`, `.bak`, scripts temporales)

## Roadmap

- [x] **Fase 1** — MVP (generación de sitios, chatbot, leads, panel)
- [x] **Fase 2** — Seguridad y JWT real (refresh funcional, roles, revocación, rate limit, CORS)
- [x] **Fase 2.5** — Panel premium (tarjetas de paquetes, detalle de empresa, editor de sitio, widget premium) y **pagos integrados** (Stripe / Mercado Pago / PayPal + modo demo)
- [~] **Fase 3** — Postgres (servicio listo en compose, migración de almacenamiento pendiente), HTTPS (pendiente), backups automáticos (hechos)

## Backups

- Manual: opción `[7]` de `dev.ps1` → copia `data/` a `backups/` (ignorado por git).
- Automático: `scripts/backup.ps1` con rotación (mantiene los últimos 10, configurable con `-Keep N`). Registrado como tarea de Windows "SaaS Platform V2 - Backup" (diaria a las 03:00).

## Postgres (Fase 3)

El almacenamiento actual es JSON (temporal). La base Postgres ya está preparada en el compose pero **no se inicia por defecto**:

```powershell
docker compose --profile postgres up -d db
```

Variables en `.env`: `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DATABASE_URL`.

La migración del almacenamiento (que la app lea de Postgres en lugar de JSON) es la fase pendiente.
