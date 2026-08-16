# Bloque 3 — Seguridad (2026-08-15)

Objetivo: endurecer la autenticación y el acceso a los endpoints del panel admin.

## Qué se hizo

### 1. Límite de intentos de login (fuerza bruta)
- `POST /api/auth/login` ahora limita intentos con ventana deslizante de 5 minutos:
  - Por IP: max 20 intentos/5 min.
  - Por usuario+IP: max 5 intentos/5 min.
- Solo los intentos **fallidos** cuentan para el límite por usuario: logins exitosos repetidos no bloquean al admin.
- Respuesta cuando se excede: HTTP 429 "Demasiados intentos. Espera 5 minutos."

### 2. Permisos por rol (solo admin)
Nueva dependencia `require_admin` en `deps.py` (403 si el rol no es `admin`). Aplicada a:
- `tenants.py`: crear/listar/eliminar tenant, generar sitio, subir documentos, detalles, exportar, site-editor (GET y POST).
- `analytics.py`: `/api/analytics/global`.
- `payments.py`: listar órdenes de pago.
- `auth.py`: registrar usuario, listar/crear/eliminar usuarios.
- Públicos por diseño (no requieren login): configuración de pagos, chat del widget, webhooks, status/finalize/cancel de órdenes, checkout (solo requiere sesión).

### 3. Límite de tamaño de subida ANTES de leer el archivo
- `upload_document` ahora valida el tamaño máximo (10 MB) en dos pasos: primero con la cabecera `Content-Length` y luego leyendo en bloques de 1 MB, abortando en cuanto se supera (evita llenar la memoria).
- Respuesta: HTTP 413 "El archivo excede el limite de 10 MB". Se mantiene la validación de extensión (.txt/.pdf) y el nombre seguro.

### 4. Escrituras atómicas (robustez con 2 workers)
- Nuevo helper `write_json_atomic` en `deps.py` (escribe `.tmp` y luego `os.replace`).
- Aplicado a: `users.json` (register, create/delete user), `tenants.json` (delete_tenant, create_tenant_record, `_save_tenant_info`), `site_data.json` (site-editor y `_render_site`), `leads.json` (chat).
- `storage_service.py` y `payment_service.py` ya usaban este patrón.

## Archivos modificados
- `backend/app/deps.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/tenants.py`
- `backend/app/routers/analytics.py`
- `backend/app/routers/payments.py`
- `backend/app/services/website_service.py`

## Pruebas realizadas (Docker)
- Login admin OK; usuario no-admin recibe 403 en `/api/tenants`, `/api/analytics/global`, `/api/payments/orders`, `/api/users`.
- 6 fallos de login seguidos → 401,401,401,401,401,429 (bloqueo correcto).
- 10 logins exitosos consecutivos → todos OK (no se bloquean).
- 3 fallos + 1 acierto → 401,401,401,200 (sigue permitido).
- Subida de 11 MB → 413; subida válida de .txt → 200.
- Regresión flujo de compra: checkout → paid → finalize → tenant con payment_status=paid, analytics con revenue correcto (249 USD).
- Datos de prueba eliminados (tenants, órdenes, leads, conversaciones en `[]`; conserva solo `admin/admin123`).

## Notas
- El límite vive en memoria por worker: al reiniciar el contenedor se reinician los contadores. Suficiente para esta escala.
- No se añadieron dependencias nuevas ni cambios de Dockerfile/compose.
