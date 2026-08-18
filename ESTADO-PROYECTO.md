# Estado del Proyecto — SaaS Platform v2

> Última actualización: 2026-08-17
> Commit HEAD: `f4f39d5`
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
| RESEND_API_KEY | Vacía (emails se omiten sin error) |

---

## Qué funciona (probado el 2026-08-17)

### Pagos
- Checkout con proveedor demo (pago simulado) → genera sitio completo con IA → entrega lista.
- También soporta Stripe, Mercado Pago y PayPal (configurar keys en `.env`).
- 3 paquetes: Full Service ($399), Web + Chat ($249), Solo Chatbot ($99).
- Checkout return/cancel pages con feedback visual.

### Generación de sitios web con IA
- Genera landing pages y páginas de servicios completas con texto, imágenes (Unsplash/Pollinations), galería, CTA, chatbot y SEO.
- Estilo visual configurable (moderno, minimalista, corporativo, creativo, natural, elegante, **glassmorphism**).
- Colores de marca personalizables.
- **Multi-idioma** — Selector ES/EN en el generador. LLM genera contenido en el idioma seleccionado. `lang` HTML dinámico, textos de footer/contacto traducidos.
- **Testimonios con fotos** — LLM genera `photo_prompt`, imágenes via Pollinations.ai.
- **Redes sociales** — Facebook, Instagram, TikTok, YouTube, X en el footer de las 3 plantillas.

### Landing del SaaS (`/landing`)
- **Escaparate de plantillas** — 4 ejemplos reales con preview, selector de estilos, "Usar esta plantilla" pre-llena el generador.
- **Video de fondo en hero** — `<video autoplay muted loop>` con URLs Pexels por industria, fallback a imagen si error.
- **Barra de progreso visual** — 5 pasos animados (validar → contenido IA → imágenes → SEO → publicar) durante generación.
- **Demo chatbot** — Botón "Abrir chat de demostración" que carga widget con tenant `showcase-restaurante`.
- **Formulario de contacto** — POST /api/contact funcional, rate limit 5/min por IP, crea lead con `source: "contact_form"`.

### Chatbot
- Widget premium instalable con una línea de código en cualquier página web.
- **Widget con colores de marca** — Avatar con iniciales del negocio, estado "en línea", quick replies, typing indicator, timestamps, branding configurable.
- Configuración por tenant (título, colores, bienvenida, respuestas rápidas).
- RAG: subir documentos .txt/.pdf para que el chatbot responda con datos reales.
- Captura de leads cuando el usuario da su email.
- Botón WhatsApp flotante (aparece solo si `contact_phone` tiene valor).

### Plantillas generadas (7)
- **landing.html** — Para restaurantes, cafes, tiendas. Hero con video, testimonios, servicios, galería, contacto, redes sociales, WhatsApp.
- **services.html** — Para negocios de servicios (dentistas, gimnasios, etc). Hero con video, servicios, equipo, contacto, redes sociales.
- **portfolio.html** — Para creativos, fotógrafos, arquitectos. Hero con video, portfolio, servicios, contacto, redes sociales.
- **medical.html** — Para consultorios, clínicas, dentistas. Servicios médicos, equipo, testimonios.
- **ecommerce.html** — Para tiendas online. Showcase de productos, categorías, carrito, contacto.
- **fitness.html** — Para gimnasios, entrenadores, yoga. Planes, entrenadores, instalaciones.
- **hotel.html** — Para hoteles, hostales, airbnb. Habitaciones, galería, servicios, reservas.
- Las 7: favicon SVG dinámico, `lang` HTML dinámico, Font Awesome 6.4.0.

### Panel admin
- Dashboard con métricas reales (leads, ingresos, costo de IA basado en paquetes).
- Editor visual del sitio (hero, sobre nosotros, servicios, galería, colores, SEO).
- Leads con búsqueda, filtro por estado y cambio de estado.
- Leads de formulario de contacto (`POST /api/contact`, rate limit 5/min, `source: contact_form`).
- Sección "Chatbot para tu Pagina" con snippet de instalación y personalización.
- Gestión de usuarios (admin/user).
- Exportar sitio como ZIP.
- Selector de pasarela de pago (demo, Stripe, Mercado Pago, PayPal).
- Selector de tema visual (moderno, minimalista, corporativo, creativo, natural, elegante, glassmorphism).
- Chatbot demo embebido en la landing.

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
│   │   ├── schemas.py           ← Modelos Pydantic (CheckoutRequest, WebsiteGenerationRequest con language, etc.)
│   │   ├── routers/
│   │   │   ├── auth.py          ← Login, refresh, register, usuarios, /me
│   │   │   ├── tenants.py       ← CRUD tenants, chat, editor, export, chat config, docs
│   │   │   ├── payments.py      ← Checkout, status, finalize, cancel, webhooks, órdenes
│   │   │   ├── analytics.py     ← Dashboard, métricas, logs de costo IA
│   │   │   └── leads.py         ← GET/PATCH leads, búsqueda, filtros, POST /api/contact
│   │   ├── services/
│   │   │   ├── llm_service.py   ← Llamadas a OpenRouter (Qwen3), genera JSON con social_media, photo_prompt, language
│   │   │   ├── website_service.py  ← Generación/modular de sitios con IA, video URLs por industria
│   │   │   ├── rag_service.py      ← ChromaDB + embeddings para RAG
│   │   │   ├── payment_service.py  ← Lógica de pagos (demo, Stripe, MP, PayPal) con PRICES dict
│   │   │   ├── export_service.py   ← Exportar sitio como ZIP con imágenes
│   │   │   ├── email_service.py    ← Envío de emails via Resend
│   │   │   ├── chat_config_service.py ← Config del widget por tenant
│   │   │   ├── storage_service.py  ← Lectura/escritura de JSON de datos
│   │   │   └── auth_service.py     ← JWT, hashing de contraseñas
│   │   ├── static/
│   │   │   ├── index.html       ← Landing del SaaS (escaparate, demo chatbot, generador con progreso + idioma)
│   │   │   ├── admin/index.html ← Panel admin (HTML + JS inline)
│   │   │   ├── widget/widget.js ← Widget premium embebible
│   │   │   └── widget/chatbot-install.html ← Página de instalación del widget
│   │   └── templates/
│   │       ├── landing.html     ← Plantilla de sitio generado (hero con video, favicon, contacto, redes)
│   │       ├── services.html    ← Plantilla para servicios (hero con video, contacto, redes)
│   │       ├── portfolio.html   ← Plantilla para creativos (hero con video, contacto, redes)
│   │       ├── checkout_return.html
│   │       └── checkout_cancel.html
│   └── requirements.txt
├── data/                         ← Datos en JSON (volumen Docker)
│   ├── tenants.json              ← Lista de tenants
│   ├── users.json                ← Usuarios admin
│   ├── storage/
│   │   ├── leads.json
│   │   ├── orders.json
│   │   ├── conversations.json
│   │   ├── chat_configs.json
│   │   └── llm_usage.json        ← Registro de costos de IA
│   ├── websites/                 ← Sitios generados (uno por tenant)
│   └── exports/                  ← ZIPs exportados
├── chats/                        ← Memoria de desarrollo (archivos .md por bloque)
├── docker-compose.yml            ← Solo servicio backend (JSON, sin Postgres activo)
├── .env                          ← Variables de entorno (NO subir)
├── requirements.txt              ← Dependencias Python
└── ESTADO-PROYECTO.md            ← Este archivo
```

---

## Observaciones conocidas del testing

1. **RAG: pregunta doble puede inventar precio.** El buscador recupera k=3 fragmentos. En preguntas con 2 temas distintos puede no traer el fragmento correcto → alucina parcial. **Solución fácil:** subir `k` de 3 a 5 en `rag_service.py:110` (`search_kwargs={"k": 5}`).

2. **RESEND_API_KEY vacía.** Los emails de lead se omiten sin error. Para producción: poner la clave real en `.env`.

3. **Servicio `db` en compose sin usar.** Hay un servicio Postgres en `docker-compose.yml` (perfil `postgres`) que nunca se arranca. La app es 100% JSON. Se puede borrar para simplificar.

4. **Variables DATABASE_URL/DB_* en `.env` sin uso.** No las lee ningún código Python.

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
| 19 | Multi-idioma | `cf426f1` | Selector ES/EN, LLM en idioma, lang HTML dinámico, textos traducidos |

---

## Mejoras pendientes (priorizadas)

### Alta prioridad
1. **Subir logo y fotos reales** — Permitir al admin subir su logo y galería de fotos propias (no solo Unsplash).
2. **Mapa de Google** — En la sección de contacto del sitio generado.

### Media prioridad
3. **Subir k del RAG a 5** — Para reducir alucinaciones en preguntas dobles.
4. **Configurar Resend** — Para emails de lead reales.

### Baja prioridad
5. **Limpiar compose** — Eliminar servicio Postgres/variables sin uso del docker-compose.
6. **Paginación de leads** — Para cuando hay muchos leads.

---

## Contenedores Docker (estado actual)

Solo corre `saas-backend`. Los contenedores huérfanos (n8n, postiz, typebot, postgres 15) fueron eliminados en el bloque 6. El servicio `db` del compose existe pero nunca se arranca.

```
NAMES          IMAGE                        STATUS
saas-backend   saas-platform-v2-backend     Up X minutes
```

---

## Desarrollo local con IA (Ollama + Aider)

El proyecto está configurado para desarrollo local sin costo usando Ollama y Aider.

### Herramientas instaladas
- **Ollama v0.32.14** — `C:\Users\Emilio Tun\AppData\Local\Programs\Ollama\ollama.exe` (inicio automático configurado en registry)
- **Aider v0.86.2** — `C:\Users\Emilio Tun\.local\bin\aider.exe`
- **Variable de entorno:** `OLLAMA_API_BASE=http://127.0.0.1:11434` (configurada con `setx`)
- **Acceso directo:** `Aider-SaaS.lnk` en el escritorio (abre cmd con todo configurado)

### Modelos disponibles
| Modelo | Tamaño | Velocidad CPU | Notas |
|---|---|---|---|
| `llama3.2:3b` | 2GB | ~10s | Rápido, buena calidad para ediciones simples |
| `qwen3:4b` | 2.5GB | ~30s+ | Tiene "thinking" (lento en CPU) |
| `deepseek-r1:latest` | 5.2GB | ~60s+ | Tiene "thinking" (muy lento en CPU) |

### Cómo usar Aider
Desde la carpeta del proyecto (`C:\projects\saas-platform-v2`):

```powershell
# Siempre abrir una consola nueva (para cargar OLLAMA_API_BASE)
$env:PATH = "C:\Users\Emilio Tun\.local\bin;$env:PATH"
$env:OLLAMA_API_BASE = "http://127.0.0.1:11434"

# Ejemplo: editar un archivo
aider --model ollama_chat/llama3.2:3b --no-show-model-warnings --no-pretty --no-gitignore --map-tokens 0 --yes-always --no-auto-commits --message "Tu instrucción aquí" -- backend/app/main.py
```

**Flags importantes:**
- `--map-tokens 0` — Desactiva el repo-map (ahorra 30+ segundos de análisis)
- `--yes-always` — Auto-acepta cambios sin confirmar
- `--no-auto-commits` — No hace commits automáticos
- `--exit` — Sale después de ejecutar el mensaje (no abre modo interactivo)

**Limitaciones conocidas:**
- Sin consola interactiva en este entorno (no detecta Windows console)
- Modelos grandes son muy lentos en CPU (sin GPU)
- Para tareas complejas, usar `llama3.2:3b` que es el más rápido
- Después de cambios, ejecutar: `docker compose up -d --build backend`

---

## Notas para la oficina

- **Cambios de código requieren rebuild:** `docker compose up -d --build backend`
- **El rebuild sale con exit-code no-cero** por un warning de PowerShell, pero la imagen se construye y el contenedor arranca (~35-60s por carga del embedding model).
- **Datos en volumen:** `./data:/app/data` (persiste entre reinicios)
- **El .env no se sube a GitHub** (tiene secretos). Si cambias de computadora, recrearlo.
- **Modelo LLM por defecto:** Qwen3 30B vía OpenRouter (barato, ~$0.01-0.02 por sitio generado).
- **Los archivos de memoria en `chats/`** son la documentación del desarrollo. Siempre hay uno por bloque funcional.
- **httpx==0.27.2** ya está en requirements → integraciones de pago por REST directo (sin SDKs).
