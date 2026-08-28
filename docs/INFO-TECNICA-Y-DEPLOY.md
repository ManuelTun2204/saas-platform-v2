# INFO-TECNICA-Y-DEPLOY

> Documento técnico: cómo funciona el sistema y cómo desplegarlo en un hosting.
> Proyecto: **SaaS Platform v2** — Generación de sitios web con IA, chatbot RAG, SEO y captura de leads.
> Preparado por: Equipo de desarrollo · agosto 2026

---

## 1. Resumen ejecutivo (qué es el sistema)

**SaaS Platform v2** es una plataforma **multi-tenant (multi-cliente)** que le permite a un solo operador (tú, el dueño del negocio de desarrollo web) **vender, generar y administrar sitios web con inteligencia artificial** para múltiples clientes, cada uno con:

- **Una página web profesional** generada con IA (textos, imágenes, galería, blog, tienda online, SEO).
- **Un chatbot con IA** que responde con los datos reales del negocio (RAG + documentos del cliente).
- **Captura de leads** (correos de visitantes) y notificaciones por email.
- **Una app móvil PWA** para que el cliente administre sus leads, pedidos y estadísticas.
- **Panel admin centralizado** donde tú controlas todos los clientes, pagos y sitios.

La clave del modelo de negocio: **generas sitios en minutos con IA en lugar de días a mano**, cobras cuota mensual, y el cliente administra su propio negocio desde su app.

---

## 2. Arquitectura técnica

```
Cliente (visitante)  ──►  Sitio web /data/websites/<tenant>/index.html
                                │  chatbot flotante + WhatsApp + captura de leads
                                ▼
Cliente (dueño)      ──►  App móvil PWA /app/<tenant>  (dashboard: leads, pedidos, stats, blog)
                                ▲
                                │
        ┌───────────────────────┴───────────────────────────┐
        │              BACKEND (FastAPI, Python 3.11)       │
        │  rutas: auth, tenants, payments, analytics,       │
        │         leads, blog, ecommerce, pwa               │
        │  servicios: llm, website, rag, usage, storage...  │
        └───────────────┬───────────────────┬───────────────┘
                        │                   │
                        ▼                   ▼
                OpenRouter (IA)      Almacenamiento
                Qwen3 + embeddings    data/ (JSON) + ChromaDB
                (modelos baratos)     (volumen Docker)
```

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11 + **FastAPI** + Uvicorn (2 workers) |
| IA | **OpenRouter** (LLM Qwen3) + ChromaDB + sentence-transformers (embeddings CPU) |
| Emails | **Resend** |
| Almacenamiento | JSON en disco (`data/`) + ChromaDB vectorial |
| Contenedor | **Docker** (imagen ~2.85 GB, modelo de embedding pre-horneado) |
| Frontend del cliente | PWA (HTML/JS) servida por el backend |

### Paquetes que se venden (precios configurados en `.env`)

| Plan | Precio | Qué incluye | Límite chat/mes |
|---|---|---|---|
| **Básico** | $29/mes | Chatbot IA + captura de leads + widget | 500 |
| **Pro** | $79/mes | Sitio web con IA + galería + contacto + Maps + WhatsApp + multi-idioma + SEO | 3,000 |
| **Premium** | $149/mes | Todo lo Pro + dominio personalizado + SSL + analytics + páginas adicionales + soporte 24/7 + backup | 10,000 |

> Nota: en el panel admin también existen paquetes legacy con otra nomenclatura (Full Service, Web+Chat, SEO Only). Los precios reales de venta son los de arriba ($29/$79/$149).

---

## 3. Funcionamiento paso a paso

1. **El cliente compra** el plan (Stripe, Mercado Pago, PayPal o modo demo) → `POST /api/payments/checkout`.
2. **Se genera la entrega con IA** → `POST /api/payments/finalize` crea el sitio web completo (texto, imágenes, plantilla según la industria) y lo guarda en `data/websites/<tenant>/`.
3. **El chatbot se entrena** con los datos del cliente (se suben documentos `.txt`/`.pdf` → RAG).
4. **El cliente administra** su negocio desde la **app móvil PWA** (`/app/<tenant>`, login propio creado desde el admin).
5. **Tú supervisas todo** desde el **panel admin** (`/`): métricas, leads, pagos, edición de sitios, exportar ZIP.

### Los 3 lados del sistema (importante para entenderlo)

| Vista | URL | Quién la usa | Qué ve |
|---|---|---|---|
| **Panel ADMIN** | `/` (login `admin`/`admin123`) | TÚ (el operador) | Todos los clientes, pagos, leads, editores |
| **Vista CLIENTE** | `/app/<tenant>` | El dueño del negocio | Su dashboard móvil (leads, pedidos, stats, blog) |
| **Vista VISITANTE** | `/data/websites/<tenant>/index.html` | El público | La página web + chatbot + captura de lead |

---

## 4. Cómo desplegarlo en un hosting (producción)

### 4.1 Opción recomendada — VPS con Docker (control total)

Un **VPS** (DigitalOcean, Hetzner, Vultr, Contabo, Linode) con Docker es lo más fiel a cómo se prueba hoy localmente y da control total.

**Requisitos mínimos del VPS:**
- 2 vCPU, 4 GB RAM, 40 GB SSD (imagen ~2.85 GB + datos del modelo)
- Ubuntu 22.04/24.04 + Docker + Docker Compose
- Dominio apuntando al VPS (registro A)

**Pasos:**
```bash
# 1. Conectarse al servidor y clonar el repo
git clone https://github.com/ManuelTun2204/saas-platform-v2.git
cd saas-platform-v2

# 2. Crear el .env (copiar .env.example y llenar claves REALES de producción)
cp .env.example .env
nano .env   # OPENROUTER_API_KEY, JWT_SECRET_KEY, RESEND_API_KEY,
            # PUBLIC_URL=https://tu-dominio.com, ALLOWED_ORIGINS=tu-dominio.com
            # keys de pago reales (Stripe/MP/PayPal), precios

# 3. Construir e iniciar (el build hornea el modelo, tarda varios minutos la primera vez)
docker compose up -d --build backend

# 4. Verificar
curl http://localhost:8000/health   # Debe responder {"status":"ok"}
```

**Exponer al público (HTTPS):** se recomienda un **reverse proxy**:
- **Traefik** (manager en Docker) con Let's Encrypt SSL automático, o
- **Nginx** + `certbot`, o **Caddy** (SSL automático integrado).

```nginx
# Ejemplo Nginx (proxy inverso)
server {
    server_name tu-dominio.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
# Después: sudo certbot --nginx -d tu-dominio.com
```

**Puntos críticos en producción:**
1. `PUBLIC_URL` debe ser `https://tu-dominio.com` (se usa en emails y el código de embed del widget).
2. `ALLOWED_ORIGINS` NO debe ser `*` en producción; pon el dominio real.
3. `JWT_SECRET_KEY` **obligatoria** y larga/aleatoria (sin ella el backend no arranca, por diseño de seguridad).
4. Persistencia: el volumen `./data` debe estar en disco persistente y con **backups** (`scripts/backup.ps1` o `cron` + `rsync`).
5. Se recomienda activar el perfil **Postgres** para pasar de JSON a base de datos real cuando crezca la carga (fase preparada en compose).

### 4.2 Alternativa — VPS sin Docker (Python directo)

Si quieres evitar Docker en el servidor:
```bash
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Horner el modelo:  python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```
(Systemd + Nginx como proxy. Menos fiel al entorno de desarrollo, más manual.)

### 4.3 Considerando PaaS (Railway/Render/Fly)

Es posible: para cada deploy se construye la imagen `backend/Dockerfile`, se inyectan las variables del `.env`, y se usa el volumen/detecta el `data/`. ⚠️ **Ojo:** esta app usa **almacenamiento en disco** (`data/`), así que en un PaaS efímero **hay que persistir `data/`** (blob storage o volumen persistente); el índice ChromaDB también debe persistirse. En **Railway** se puede conectar un *Volume* persistente montado en `/app/data`. Es viable, pero el **VPS con Docker es la opción más sólida** porque el sistema ya fue diseñado/probado así.

---

## 5. Despliegue local (desarrollo / demo)

```bash
docker compose up -d --build backend     # build + iniciar
docker compose down                       # detener
```
- Panel admin: `http://localhost:8000/` (user `admin` / `admin123`)
- Landing pública: `http://localhost:8000/landing`
- Health check: `http://localhost:8000/health`

> Cada cambio de código requiere **rebuild**: `docker compose up -d --build backend` (el build tarda ~35–60 s por la carga del modelo; el exit-code no-cero es solo un warning de PowerShell, la imagen sí se construye).

---

## 6. Variables de entorno (.env) — checklist de producción

| Variable | Obligatoria | Uso |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | IA (generación de sitios y chatbot) |
| `JWT_SECRET_KEY` | ✅ | Firma de tokens JWT |
| `RESEND_API_KEY` | ⚠️ | Notificaciones por email (sin ella no envía, pero no rompe) |
| `ADMIN_EMAIL` | ✅ | Destinatario de alertas de leads |
| `PUBLIC_URL` | ✅ | URL pública (emails + embed del widget) |
| `ALLOWED_ORIGINS` | ✅ | CORS (poner dominio real en producción) |
| `STRIPE/MP/PAYPAL` keys | ⚠️ | Pasarelas reales (vacías = modo demo) |
| `PRICE_BASIC/PRO/PREMIUM` | — | Precios (defaults 29/79/149 USD) |
| `LLM_*_MODEL` | — | Modelos de IA (defaults Qwen3) |

> El `.env` **nunca se sube a GitHub** (está en `.gitignore`).

---

## 7. Estado real y pendientes

**Funcionando (probado):** pagos (demo + Stripe/MP/PayPal), generación de sitios con IA, 7 plantillas, blog, e-commerce, tienda, app móvil PWA con login, cuenta de cliente, editor visual, analytics, export ZIP, multi-idioma, widget premium con RAG, seguridad (JWT, rate limit, límites de uso por plan).

**Pendientes de alta prioridad (roadmap):**
- Dashboard del cliente con analytics avanzados
- Calendly embebido
- SEO automático (sitemap, schema.org)
- Google Analytics / Pixel
- Popup de captura de leads
- Migración de almacenamiento JSON → **Postgres** (compose ya lo tiene preparado)
- HTTPS en `PUBLIC_URL` real de producción

---

*Documento técnico generado por el equipo de desarrollo. Para dudas técnicas, ver `ESTADO-PROYECTO.md`, `README.md` y `AGENTS.md` del repo.*
