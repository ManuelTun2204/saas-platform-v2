# Estado del Proyecto — SaaS Platform v2

> Última actualización: 2026-08-16
> Commit HEAD: `fd70882`
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

## Qué funciona (probado el 2026-08-16)

### Pagos
- Checkout con proveedor demo (pago simulado) → genera sitio completo con IA → entrega lista.
- También soporta Stripe, Mercado Pago y PayPal (configurar keys en `.env`).
- 3 paquetes: Full Service ($399), Web + Chat ($249), Solo Chatbot ($99).

### Generación de sitios web con IA
- Genera landing pages y páginas de servicios completas con texto, imágenes (Unsplash), galería, CTA, chatbot y SEO.
- Estilo visual configurable (moderno, minimalista, corporativo, creativo, natural, elegante).
- Colores de marca personalizables.

### Chatbot
- Widget instalable con una línea de código en cualquier página web.
- Configuración por tenant (título, colores, bienvenida, respuestas rápidas).
- RAG: subir documentos .txt/.pdf para que el chatbot responda con datos reales.
- Captura de leads cuando el usuario da su email.

### Panel admin
- Dashboard con métricas (leads, ingresos, costo de IA).
- Editor visual del sitio (hero, sobre nosotros, servicios, galería, colores, SEO).
- Leads con búsqueda, filtro por estado y cambio de estado.
- Sección "Chatbot para tu Pagina" con snippet de instalación y personalización.
- Gestión de usuarios (admin/user).
- Exportar sitio como ZIP.

### Seguridad
- JWT tokens con refresh.
- Rate limit en login (5 intentos fallidos → bloqueo) y en chat (20/min).
- Solo admin accede a endpoints sensibles (403 si no).

### Emails
- Funcional si se configura `RESEND_API_KEY`. Sin ella, los emails se omiten con warning (no rompe).

---

## Arquitectura

```
saas-platform-v2/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI: CORS, routers, archivos estáticos
│   │   ├── deps.py              ← Inyección de dependencias (servicios, auth, rate limit)
│   │   ├── schemas.py           ← Modelos Pydantic (CheckoutRequest, ChatRequest, etc.)
│   │   ├── routers/
│   │   │   ├── auth.py          ← Login, refresh, register, usuarios, /me
│   │   │   ├── tenants.py       ← CRUD tenants, chat, editor, export, chat config, docs
│   │   │   ├── payments.py      ← Checkout, status, finalize, cancel, webhooks, órdenes
│   │   │   ├── analytics.py     ← Dashboard, métricas, logs de costo IA
│   │   │   └── leads.py         ← GET/PATCH leads, búsqueda, filtros
│   │   ├── services/
│   │   │   ├── llm_service.py   ← Llamadas a OpenRouter (Qwen3 por defecto)
│   │   │   ├── website_service.py  ← Generación/modular de sitios con IA
│   │   │   ├── rag_service.py      ← ChromaDB + embeddings para RAG
│   │   │   ├── payment_service.py  ← Lógica de pagos (demo, Stripe, MP, PayPal)
│   │   │   ├── export_service.py   ← Exportar sitio como ZIP con imágenes
│   │   │   ├── email_service.py    ← Envío de emails via Resend
│   │   │   ├── chat_config_service.py ← Config del widget por tenant
│   │   │   ├── storage_service.py  ← Lectura/escritura de JSON de datos
│   │   │   └── auth_service.py     ← JWT, hashing de contraseñas
│   │   ├── static/
│   │   │   ├── index.html       ← Página pública de ventas (landing del SaaS)
│   │   │   ├── admin/index.html ← Panel admin (HTML + JS inline)
│   │   │   └── widget/widget.js ← Widget embebible de chat
│   │   └── templates/
│   │       ├── landing.html     ← Plantilla de sitio generado
│   │       ├── services.html    ← Plantilla para servicios
│   │       ├── checkout_return.html
│   │       └── checkout_cancel.html
│   └── requirements.txt
├── data/                         ← Datos en JSON (volumen Docker)
│   ├── tenants.json              ← Lista de tenants (vacío = sin clientes)
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
└── requirements.txt              ← Dependencias Python
```

---

## Estado de datos (limpio)

| Archivo | Estado |
|---|---|
| tenants.json | `[]` (0 tenants) |
| leads.json | `[]` (0 leads) |
| orders.json | `[]` (0 órdenes) |
| conversations.json | `[]` (0 conversaciones) |
| chat_configs.json | `{}` (sin configuraciones) |
| llm_usage.json | Tiene registros de las pruebas (no afecta) |
| users.json | Solo `admin` |
| websites/ | Vacío |
| exports/ | Vacío |

---

## Observaciones conocidas del testing

1. **RAG: pregunta doble puede inventar precio.** El buscador recupera k=3 fragmentos. En preguntas con 2 temas distintos puede no traer el fragmento correcto → alucina parcial. **Solución fácil:** subir `k` de 3 a 5 en `rag_service.py:110` (`search_kwargs={"k": 5}`).

2. **RESEND_API_KEY vacía.** Los emails de lead se omiten sin error. Para producción: poner la clave real en `.env`.

3. **Servicio `db` en compose sin usar.** Hay un servicio Postgres en `docker-compose.yml` (perfil `postgres`) que nunca se arranca. La app es 100% JSON. Se puede borrar para simplificar, o conservar para una futura migración.

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

---

## Mejoras pendientes (priorizadas para conversión)

### Alta prioridad (impacto visual/conversión)
1. **Escaparate de plantillas** — Mostrar 3-4 sitios reales generados en la landing pública ANTES de que el cliente compre (hoy compra "a ciegas").
2. **Botón WhatsApp flotante** — En los sitios generados, botón verde de WhatsApp abajo a la derecha (clave en LATAM).
3. **Fondo de video en hero** — Opción de video de fondo (YouTube embed o archivo) en la portada del sitio generado.
4. **Tema glassmorphism** — Nuevo estilo visual "Vidrio/Transparencias" con blur y opacidad.

### Media prioridad
5. **Subir logo y fotos reales** — Permitir al admin subir su logo y galería de fotos propias (no solo Unsplash).
6. **Progreso visual de generación** — Pasos animados ("Creando tu texto… fotos… sitio") en vez de spinner.
7. **Demo del chatbot en la landing** — Widget funcional para probar antes de comprar.
8. **Mapa de Google** — En la sección de contacto del sitio generado.

### Baja prioridad
9. **Testimonios con fotos** — Sección de testimonios en las plantillas.
10. **Formulario de contacto** — Además del chat, formulario que deje leads.
11. **Subir k del RAG a 5** — Para reducir alucinaciones en preguntas dobles.
12. **Configurar Resend** — Para emails de lead reales.

---

## Contenedores Docker (estado actual)

Solo corre `saas-backend`. Los contenedores huérfanos (n8n, postiz, typebot, postgres 15) fueron eliminados en el bloque 6. El servicio `db` del compose existe pero nunca se arranca.

```
NAMES          IMAGE                        STATUS
saas-backend   saas-platform-v2-backend     Up X minutes
```

---

## Notas para la oficina

- **Cambios de código requieren rebuild:** `docker compose up -d --build backend`
- **Datos en volumen:** `./data:/app/data` (persiste entre reinicios)
- **El .env no se sube a GitHub** (tiene secretos). Si cambias de computadora, recrearlo.
- **Modelo LLM por defecto:** Qwen3 30B vía OpenRouter (barato, ~$0.01-0.02 por sitio generado).
- **Los archivos de memoria en `chats/`** son la documentación del desarrollo. Siempre hay uno por bloque funcional.
