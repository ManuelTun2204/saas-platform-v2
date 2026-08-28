# Estado del Proyecto — SaaS Platform v2

> Última actualización: 2026-08-18
> Commit HEAD: `f409fa8`
> Repo: https://github.com/ManuelTun2204/saas-platform-v2

---

## Cómo arrancar

1. Abrir Docker Desktop (si no corre, nada funciona).
2. En la carpeta del proyecto:
   ```
   docker compose up -d --build backend
   ```
3. API disponible en: `http://localhost:8000`
4. Panel admin: abrir `http://localhost:8000` en el navegador.
5. Landing pública: `http://localhost:8000/landing`

---

## Credenciales

| Credencial | Valor |
|---|---|
| Usuario admin | `admin` |
| Contraseña admin | `admin123` |
| OPENROUTER_API_KEY | En `.env` (no subir a GitHub) |
| JWT_SECRET_KEY | En `.env` |
| RESEND_API_KEY | Configurada en `.env` |

---

## Qué funciona (probado el 2026-08-18)

### Pagos
- Checkout con proveedor demo (pago simulado) → genera sitio completo con IA → entrega lista.
- También soporta Stripe, Mercado Pago y PayPal (configurar keys en `.env`).
- **3 paquetes SaaS**: Básico ($29/mes, solo chatbot), Pro ($79/mes, sitio+chatbot), Premium ($149/mes, todo incluido).
- Checkout return/cancel pages con feedback visual.
- Modo widget-only para plan Básico (no genera sitio, solo chatbot embebible).

### Generación de sitios web con IA
- Genera landing pages y páginas de servicios completas con texto, imágenes (Unsplash/Pollinations), galería, CTA, chatbot y SEO.
- Estilo visual configurable (moderno, minimalista, corporativo, creativo, natural, elegante, **glassmorphism**).
- Colores de marca personalizables.
- **Multi-idioma** — Selector ES/EN en el generador. LLM genera contenido en el idioma seleccionado. `lang` HTML dinámico, textos de footer/contacto traducidos.
- **Testimonios con fotos** — LLM genera `photo_prompt`, imágenes via Pollinations.ai.
- **Redes sociales** — Facebook, Instagram, TikTok, YouTube, X en el footer de las plantillas.
- **Upload de imágenes** — Logo y fotos reales se suben y persisten entre regeneraciones.

### Plantillas generadas (7)
- **landing.html** — Restaurantes, cafes, tiendas. Hero con video, testimonios, servicios, galería, contacto.
- **services.html** — Negocios de servicios. Hero con video, servicios, equipo, contacto.
- **portfolio.html** — Creativos, fotógrafos, arquitectos. Hero con video, portfolio, contacto.
- **medical.html** — Consultorios, clínicas, dentistas. Servicios médicos, equipo, testimonios.
- **ecommerce.html** — Tiendas online. Showcase de productos, categorías, testimonios.
- **fitness.html** — Gimnasios, entrenadores, yoga. Clases, entrenadores, precios.
- **hotel.html** — Hoteles, hostales. Habitaciones, galería, amenidades.
- Las 7: favicon SVG dinámico, `lang` HTML dinámico, Font Awesome 6.4.0, WhatsApp flotante + chatbot lado a lado con tooltips hover.

### Blog integrado (`/blog/{tenant}/{slug}`)
- CRUD de posts (admin): crear, editar, eliminar, publicar/borrador.
- Sección "Noticias y Artículos" visible en las 7 plantillas (muestra últimos 3 posts).
- Página individual de cada post con renderizado de markdown.
- Tags, imágenes, excerpts.

### E-commerce real (`/store/{tenant}`)
- CRUD de productos: nombre, descripción, precio, precio anterior (descuento), imagen, categoría, stock.
- Tienda pública: grid de productos, filtro por categoría, colores de marca.
- Carrito sidebar: agregar, cantidad +/−, eliminar.
- Checkout: nombre, email, teléfono, dirección, notas.
- Métodos de pago: Demo / Stripe / Mercado Pago.
- Pedidos: flujo de estados (pending → confirmed → shipped → delivered / cancelled).
- Admin UI: stats (productos, pedidos, ingresos, pendientes), gestión de pedidos.

### App Móvil PWA (`/app/{tenant}`)
- Dashboard optimizado para celular con 4 tabs: Stats, Leads, Pedidos, Blog.
- Login integrado dentro de la app (no necesita token en URL).
- Auto-refresh cada 60 segundos.
- Colores de marca del negocio.
- `manifest.json` dinámico (se puede "Agregar a pantalla de inicio" como app).
- Iconos SVG generados automáticamente con la inicial del negocio.
- **Cuenta de cliente**: se crea desde admin con usuario/contraseña, el cliente recibe su link.

### Landing del SaaS (`/landing`)
- **Escaparate de plantillas** — 4 ejemplos reales con preview, selector de estilos, "Usar esta plantilla".
- **Video de fondo en hero** — URLs Pexels por industria, fallback a imagen.
- **Barra de progreso visual** — 5 pasos animados durante generación.
- **Demo chatbot** — Botón "Abrir chat de demostración" que carga widget.
- **Formulario de contacto** — POST /api/contact funcional, rate limit 5/min por IP.

### Chatbot
- Widget premium instalable con una línea de código.
- **Widget con colores de marca** — Avatar con iniciales del negocio, estado "en línea", quick replies, typing indicator, timestamps, branding configurable.
- **Widget tracking** — Auto-registra page_view al cargar el widget.
- Configuración por tenant (título, colores, bienvenida, respuestas rápidas).
- RAG: subir documentos .txt/.pdf para que el chatbot responda con datos reales.
- Captura de leads cuando el usuario da su email.

### Panel admin
- Dashboard con métricas reales (leads, ingresos, costo de IA basado en paquetes).
- **Analytics por tenant** — Endpoint `/api/analytics/tenant/{id}` con page views, chat sessions.
- **Analytics global** — Endpoint `/api/analytics/global` con métricas globales.
- Editor visual del sitio (hero, sobre nosotros, servicios, galería, colores, SEO).
- Leads con búsqueda, filtro por estado y cambio de estado.
- Sección "Chatbot para tu Pagina" con snippet de instalación y personalización.
- Gestión de usuarios (admin/user).
- **Gestión de Blog** — Crear/editar/eliminar posts, publicar/borrador.
- **Gestión de Tienda** — CRUD productos, pedidos con flujo de estados.
- **Cuenta de Cliente** — Crear usuario para el cliente con acceso a app movil.
- Exportar sitio como ZIP.
- Selector de pasarela de pago y tema visual.

### Seguridad
- JWT tokens con refresh.
- Rate limit en login (5 intentos fallidos → bloqueo), en chat (20/min) y en formulario de contacto (5/min por IP).
- Solo admin accede a endpoints sensibles (403 si no).

### Emails
- Funcional si se configura `RESEND_API_KEY`. Sin ella, los emails se omiten con warning (no rompe).

---

## Arquitectura

```
saas-platform-v2/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI: CORS, routers, archivos estáticos, /landing
│   │   ├── deps.py              ← Inyección de dependencias (servicios, auth, rate limit)
│   │   ├── schemas.py           ← Modelos Pydantic
│   │   ├── routers/
│   │   │   ├── auth.py          ← Login, refresh, register, usuarios, /me
│   │   │   ├── tenants.py       ← CRUD tenants, chat, editor, export, chat config, docs
│   │   │   ├── payments.py      ← Checkout, status, finalize, cancel, webhooks
│   │   │   ├── analytics.py     ← Dashboard, métricas, analytics global/por tenant
│   │   │   ├── leads.py         ← GET/PATCH leads, búsqueda, filtros, POST /api/contact
│   │   │   ├── blog.py          ← CRUD posts, página individual markdown
│   │   │   ├── ecommerce.py     ← CRUD productos, tienda, carrito, checkout, pedidos
│   │   │   └── pwa.py           ← App movil PWA, manifest, iconos, dashboard movil
│   │   ├── services/
│   │   │   ├── llm_service.py   ← Llamadas a OpenRouter (Qwen3)
│   │   │   ├── website_service.py  ← Generación/modular de sitios con IA
│   │   │   ├── rag_service.py      ← ChromaDB + embeddings para RAG
│   │   │   ├── payment_service.py  ← Lógica de pagos (demo, Stripe, MP, PayPal)
│   │   │   ├── analytics_service.py ← Tracking de page views, chats
│   │   │   ├── domain_service.py   ← Registro/verificación de dominios
│   │   │   ├── export_service.py   ← Exportar sitio como ZIP
│   │   │   ├── email_service.py    ← Envío de emails via Resend
│   │   │   ├── chat_config_service.py ← Config del widget por tenant
│   │   │   ├── storage_service.py  ← Lectura/escritura de JSON
│   │   │   └── auth_service.py     ← JWT, hashing de contraseñas
│   │   ├── static/
│   │   │   ├── index.html       ← Landing del SaaS
│   │   │   ├── admin/index.html ← Panel admin completo
│   │   │   └── widget/
│   │   │       ├── widget.js    ← Widget premium embebible
│   │   │       └── chatbot-install.html
│   │   └── templates/
│   │       ├── landing.html     ← 7 plantillas de sitios
│   │       ├── services.html
│   │       ├── portfolio.html
│   │       ├── medical.html
│   │       ├── ecommerce.html
│   │       ├── fitness.html
│   │       ├── hotel.html
│   │       ├── checkout_return.html
│   │       └── checkout_cancel.html
│   └── requirements.txt
├── data/                         ← Datos en JSON (volumen Docker)
│   ├── tenants.json
│   ├── users.json
│   ├── storage/
│   │   ├── leads.json
│   │   ├── orders.json
│   │   ├── conversations.json
│   │   ├── chat_configs.json
│   │   └── llm_usage.json
│   └── websites/                 ← Sitios generados (uno por tenant)
│       └── {tenant_id}/
│           ├── index.html
│           ├── site_data.json
│           ├── blog/posts.json  ← Posts del blog
│           ├── store/           ← Tienda (productos, pedidos, config)
│           │   ├── products.json
│           │   ├── orders.json
│           │   └── config.json
│           └── uploads/         ← Imágenes subidas
├── docker-compose.yml
├── .env                          ← Variables de entorno (NO subir)
├── requirements.txt
└── ESTADO-PROYECTO.md            ← Este archivo
```

---

## Endpoints importantes

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Panel admin (HTML) |
| GET | `/landing` | Landing pública del SaaS |
| POST | `/api/auth/login` | Login → JWT token |
| GET | `/api/auth/me` | Verificar token |
| GET | `/api/tenants` | Listar empresas |
| POST | `/api/tenants` | Crear empresa |
| POST | `/api/site-editor/{tenant}` | Regenerar sitio |
| GET | `/api/blog/{tenant}` | Posts publicados |
| GET | `/api/blog/{tenant}/all` | Todos los posts (admin) |
| POST | `/api/blog/{tenant}` | Crear post |
| GET | `/blog/{tenant}/{slug}` | Ver post individual |
| GET | `/api/store/{tenant}/products` | Productos activos |
| POST | `/api/store/{tenant}/products` | Crear producto |
| POST | `/api/store/{tenant}/orders` | Crear pedido |
| GET | `/store/{tenant}` | Tienda pública |
| GET | `/app/{tenant}` | App movil PWA |
| POST | `/api/contact` | Formulario de contacto |

---

## Bloques completados (historial)

| # | Bloque | Commit | Qué incluye |
|---|---|---|---|
| 1 | Setup y seguridad | `cd2138a` | Rate limit, permisos admin, validación uploads |
| 2 | Ventas y pagos | `80ff2a1` | Stripe/MP/PayPal webhooks, tenant tras pago, dashboard |
| 3 | Costos IA | `f09e0e0` | Modelos Qwen3 baratos, logging de costos, gráfica |
| 4 | Atractivo visual | `2a69167` | Email en widget, panel Leads, SEO editable, email confirmación |
| 5 | Chatbot páginas | `141166e` | Widget con data-tenant, config por tenant, personalizar en panel |
| 6 | Limpieza técnica | `ebd9fa1` | Contenedores huérfanos eliminados, sistema simplificado |
| 7 | Prueba completa | `fd70882` | Test end-to-end de todo el sistema |
| 8 | Pagos en línea | `f747ce7` | payment_service.py REST + demo, checkout_return, checkout_cancel |
| 9 | Glassmorphism | `906b03a` | Tema "Vidrio" con backdrop-filter blur, cards transparentes |
| 10 | WhatsApp flotante | `843ae37` | Botón verde #25D366 en bottom-right, solo con phone |
| 11 | Escaparate plantillas | `75dfd84` | Landing pública /landing con 4 ejemplos, selector de estilos |
| 12 | Testimonios fotos | `240127c` | LLM genera photo_prompt, Pollinations.ai para imágenes |
| 13 | Formulario contacto | `af507c9` | POST /api/contact funcional, rate limit, leads con source |
| 14 | Favicon SVG | `5ff8363` | Iniciales del negocio en SVG inline, 3 plantillas |
| 15 | Demo chatbot | `1a9cb2d` | Botón "Abrir chat demo" en landing SaaS |
| 16 | Video hero | `ce73448` | Video de fondo con URLs Pexels por industria, fallback imagen |
| 17 | Barra progreso | `bad5e5b` | 5 pasos animados durante generación de sitio |
| 18 | Redes sociales | `b318522` | Facebook, Instagram, TikTok, YouTube, X en footer |
| 19 | Multi-idioma | `cf426f1` | Selector ES/EN, LLM en idioma, lang HTML dinámico |
| 20 | Upload imágenes | `1f81151` | Logo y fotos reales upload, persisten entre regeneraciones |
| 21 | 4 plantillas IA | `f4f39d5` | medical, ecommerce, fitness, hotel + _select_template() |
| 22 | WhatsApp fix | `19707d5` | WhatsApp movido a left-6 para no chocar con chatbot |
| 23 | WhatsApp + tooltips | `e984d0d` | WhatsApp right-24 junto al chatbot, tooltips hover |
| 24 | WhatsApp spacing | `0853438` | Más espacio entre iconos (right-24) |
| 25 | Blog integrado | `b5e6164` | CRUD posts, admin UI, sección en 7 plantillas, post individual markdown |
| 26 | E-commerce | `f9b0cc1` | Productos, carrito, checkout, pedidos admin |
| 27 | PWA movil | `8a35bc2` | Dashboard movil leads/pedidos/stats/blog, manifest, iconos |
| 28 | PWA login | `bd74575` | Login integrado en PWA, ya no pide auth en URL |
| 29 | Cuenta cliente | `f409fa8` | Crear usuario cliente desde admin con acceso a app movil |

---

## Observaciones conocidas

1. **RAG: pregunta doble puede inventar precio.** El buscador recupera k=5 fragmentos. En preguntas con 2 temas distintos puede no traer el fragmento correcto.
2. **RESEND_API_KEY** configurada funcional con `manueltunchan@gmail.com`.
3. **Cambios de código requieren rebuild:** `docker compose up -d --build backend`
4. **El rebuild sale con exit-code no-cero** por un warning de PowerShell, pero la imagen se construye (~35-60s por carga del embedding model).
5. **Datos en volumen:** `./data:/app/data` (persiste entre reinicios)
6. **El .env no se sube a GitHub** (tiene secretos).
7. **httpx==0.27.2** en requirements → integraciones de pago por REST directo (sin SDKs).

---

## Seguridad aplicada (2026-08-28, commit `e63ff3c`)

Antes de entregar a clientes reales se aplicaron 3 fixes críticos:

1. **Validación de tenant en `/api/chat/{tenant_id}`**: si el tenant no existe responde **404** antes de tocar el LLM. Evita que cualquiera golpee `/api/chat/<id-inventado>` y consuma tu API de OpenRouter.
2. **Límites de uso de chat por plan**: nuevo `backend/app/services/usage_service.py` cuenta mensajes por tenant/mes y aplica tope según el paquete (basic=500, pro=3000, premium/full=10000, por defecto 3000). Al alcanzar el límite responde "plan alcanzado" sin gastar API. Contador en `data/storage/usage.json` (gitignored).
3. **`JWT_SECRET_KEY` obligatoria**: ahora el backend **falla al arrancar** si no está en `.env` (antes generaba una aleatoria y rompía las sesiones en cada reinicio).

> Para aplicar los dos primeros hay que reconstruir: `docker compose up -d --build backend`.
> El `.env` ya incluye `JWT_SECRET_KEY`.

---

## Notas para continuar después

- **Pendientes de media prioridad**: Animaciones de scroll (IntersectionObserver), modo oscuro, testimonios de Google, páginas múltiples.
- **Pendientes de alta prioridad**: Dashboard del cliente con analytics, Calendly embebido, SEO automático (sitemap, schema.org), Google Analytics/Pixel, popup captura leads.
- **El usuario usa opencode como herramienta principal** para desarrollo.
- **2 PCs**: casa (Emilio Tun) y trabajo (Manuel) con sync via GitHub.
- **Variable `OPENCODE_SERVER_PASSWORD`** está en el entorno del proceso, NO en el registro de Windows.
- **Panel de proyectos simplificado**: `C:\projects\project-panel` (repo `ManuelTun2204/project-panel`). `open_opencode` solo abre la app de escritorio (`OpenCode.exe`).
