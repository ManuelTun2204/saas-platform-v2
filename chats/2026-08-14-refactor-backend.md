# Charla 2026-08-14: Refactor del backend (main.py en routers) + verificacion con Docker

Fecha: 2026-08-14 (laptop) · Repo: `ManuelTun2204/saas-platform-v2`

## Que se hizo

1. **Refactor de `backend/app/main.py`**: el archivo gigante con todos los endpoints se dividio en 4 routers:
   - `backend/app/routers/auth.py` (login, refresh, me, register, usuarios)
   - `backend/app/routers/tenants.py` (CRUD de empresas, generar sitio, subir documentos, chat, detalles, exportar, editor de sitios)
   - `backend/app/routers/payments.py` (config, checkout, status, finalize, paginas de retorno)
   - `backend/app/routers/analytics.py` (analiticas globales del panel)
   - `backend/app/schemas.py` (modelos Pydantic) y `backend/app/deps.py` (servicios compartidos, rate limits, helpers)
   - `backend/app/main.py` ahora solo crea la app, monta estaticos, sirve el panel y el health.

2. **Verificacion completa en Docker** (imagen reconstruida):
   - Login de admin OK
   - `GET /api/payments/config` OK (modo demo)
   - Checkout demo -> finalize -> sitio generado OK (empresa creada con `payment_status=paid`)
   - Analiticas del panel reflejan la empresa pagada y el ingreso estimado
   - Bug 1 verificado: el chatbot ahora SÍ encuentra al tenant (antes leia un archivo equivocado)
   - Subida de documento `.txt` e indexacion OK
   - Editor de sitios (`GET /api/site-editor/...`) OK
   - Las 26 rutas del sistema estan todas presentes (paridad verificada, sin duplicados)

3. **Bug encontrado y corregido**: si `data/tenants.json` tenia un contenido invalido (`{}`), la creacion de empresas fallaba con `'dict' object has no attribute 'append'`. Se hizo el codigo robusto: si el archivo no es una lista, se empieza de cero.

4. **Carpetas raiz `app/` y `frontend/` eliminadas** (codigo muerto que no usaba el contenedor) y `estructura_completa.txt` actualizado.

## Importante

- **La clave de OpenRouter en `.env` ya NO es valida**: devuelve `401 User not found` al intentar usarla para chat/IA (solo el endpoint de listar modelos respondia, pero ese es publico). Con esa clave el chatbot no puede responder con IA (devuelve "problemas tecnicos") y los sitios se generan con datos de respaldo.
- Para arreglarlo: generar una clave NUEVA en https://openrouter.ai/settings/keys y actualizarla en el `.env` (en la PC que corra el sistema). No se sube a GitHub.

## Datos de prueba

- Los datos usados para probar se limpiaron. `data/` esta en `.gitignore` y NO se sube.
- En esta laptop quedo un usuario `admin` / `admin123` local solo para probar (no existe en la oficina).

## Estado

- Commit pendiente de subir con el refactor (routers), la robustez de tenants.json, la limpieza de codigo muerto y este documento.
- Cuando actualices la clave de OpenRouter, probar de nuevo el chat: preguntar algo que este en un documento subido y confirmar que responda con esa informacion.
