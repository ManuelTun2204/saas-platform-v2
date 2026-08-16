# Bloque 5 — Atractivo: captura de leads, SEO y emails (2026-08-16)

Objetivo: que el SaaS atraiga y convierta mejor visitantes — capturar el correo de
quien visita la web (lead), hacer el sitio encontrable en Google (SEO) y avisar por
email tanto al negocio como al visitante.

## Qué se hizo

### A. Captura de email en el widget de chat (`widget.js`)
- Después de **2 mensajes** del visitante sin dar correo, el chat muestra un
  formulario inline: "¿Me dejas tu correo para que te contactemos? 📧".
- La quick reply **"Quiero que me contacten"** (y variantes contactar/correo/email)
  también abre el formulario.
- El correo capturado se guarda y se manda en todas las peticiones siguientes
  (`payload.email`), junto con `source` = URL de la página donde está el widget.
- Validación de formato de correo (regex) antes de enviar.
- Si el usuario escribe el correo a mano en el chat, el backend ya lo detectaba.

### B. Panel de Leads completo (backend + admin)
- **Nuevo router** `routers/leads.py` (solo admin):
  - `GET /api/leads` con búsqueda `q` (por correo o empresa) y filtro `status`;
    devuelve counts por estado y el lead enriquecido con el nombre de la empresa.
  - `PATCH /api/leads/{id}` para cambiar estado (`nuevo`, `contactado`, `convertido`).
    Estado inválido → 400. Leads viejos sin id: se les genera uno estable.
- Al crear un lead desde el chat ahora se guarda `id`, `status: "nuevo"` y `source`.
  - Se evita duplicar: mismo correo + misma empresa no crea otro lead.
- **Admin**: nueva pestaña **"Leads"** en el navbar (patrón de la vista Ordenes):
  tarjetas con totales (Leads, Nuevos, Contactados, Convertidos), buscador,
  filtro por estado, tabla con correo/empresa/pregunta/página/fecha, y un selector
  para cambiar el estado de cada lead sin recargar.
- `analytics.py`: métricas `leads_nuevos`, `leads_contactados`, `leads_convertidos`
  y los últimos leads con estado y empresa (para el dashboard).

### C. SEO por sitio (generación + editor + plantillas)
- El generador ahora crea 3 campos editables por sitio (`website_service.py`):
  `seo_title`, `seo_description`, `seo_keywords` (valores por defecto armados con
  nombre/industria/hero).
- **Editor del admin**: nueva sección "SEO (aparece en Google)" con Título SEO,
  Descripción SEO y Palabras clave. Al guardar, regenera el sitio con esos datos.
- Guard del editor: pasó de "solo claves existentes" a una **lista blanca**
  `EDITABLE_KEYS` (incluye las claves SEO y campos nuevos).
- Plantillas con `<title>` + meta description/keywords + Open Graph (og:title,
  og:description, og:type): `landing.html`, `services.html`, `portfolio.html`,
  `portafolio.html`. Se quitó el bloqueo `{% if seo_enabled %}` (siempre SEO).

### D. Email de confirmación al visitante (`email_service.py`)
- Nueva función `send_lead_confirmation(lead_email, company_name)`: correo
  automático "¡Gracias por tu interés!" al visitante cuando deja su correo.
- Se envía junto al aviso al negocio (`send_lead_notification`). Si no hay
  `RESEND_API_KEY` configurada, se salta con un warning (no rompe nada).

## Probado en vivo (con Docker)
- Generación de sitio con IA → HTML con `<title>`, meta descripción/keywords, og tags.
- Chat con email + source → lead creado con `id`, `status:"nuevo"`, `source`, empresa.
- Duplicado: mismo correo+empresa no agrega otro lead.
- Leads: listar, buscar (`q`), filtrar por estado, PATCH a `contactado`, estado
  inválido → 400.
- Editor: GET devuelve campos SEO; POST guarda y regenera el sitio con el nuevo
  `<title>` ("Cafe Don Jose | Mejores Cafes").
- Emails sin `RESEND_API_KEY`: se omiten con warning, sin error.

## Commit
`2a69167` — feat: bloque atractivo (13 archivos, +475/-22), subido a GitHub
(`main`). Antes de este bloque la app estaba en `f09e0e0` (bloque costos).

## Notas / pendientes
- Para activar los emails reales: configurar `RESEND_API_KEY` y `ADMIN_EMAIL`
  en `.env` (no se suben al repo) y reiniciar el backend.
- Quedan pendientes fuera de este bloque: deuda técnica Postgres y contenedores
  huérfanos (`saas-postgres`, `saas-n8n`, `saas-postiz`, `saas-typebot-*`).
