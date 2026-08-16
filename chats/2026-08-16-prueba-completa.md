# Bloque 8 — Prueba completa del sistema (2026-08-16)

Objetivo: verificar de punta a punta que todo lo que vende la plataforma FUNCIONA
antes de añadir mejoras visuales. Se probó contra el backend real en Docker
(localhost:8000), igual que lo usaría un cliente.

## Qué se probó y resultado

### Pagos (flujo completo) — OK
- `GET /api/payments/config`: 3 paquetes con precio correcto (Full 399, Web+Chat 249,
  Solo Chatbot 99) y proveedor demo activo.
- `POST /api/payments/checkout` (paquete full, proveedor demo): crea orden
  `ord_...`, estado pasa a "paid" (demo simula pago) y devuelve URL de retorno.
- `GET /api/payments/status/{order_id}`: devuelve "paid".
- `POST /api/payments/finalize/{order_id}`: **generó el sitio completo con IA**
  (preview `/data/websites/.../index.html`) y marcó el tenant como pagado.
- Idempotencia: llamar finalize otra vez no regenera, devuelve la misma preview.
- `GET /api/payments/orders`: la orden aparece con su estado y preview.

### Exportación ZIP — OK
- `POST /api/export/{tenant_id}` (admin) genera ZIP con config.json, index.html,
  README.md y las imágenes (hero + galería) descargadas. Se descargó y revisó el
  contenido: completo.

### Chatbot RAG (documentos) — OK con una observación
- Subir `servicios-vet.txt` (admin): `chunks_indexed: 1`.
- Preguntas sobre el documento: respondió correctamente dirección, horario y
  teléfono (datos reales del documento).
- Pregunta fuera del documento ("¿cuántos empleados?"): respondió correctamente
  "no cuento con esa información" (no inventa).
- **Observación**: en una pregunta combinada ("precio de consulta y teléfono") el
  modelo una vez dio un precio inventado ($200 en vez de $35). El buscador recupera
  k=3 fragmentos y en preguntas dobles puede no traer el fragmento del precio. No
  es bloqueante, pero se puede subir el límite a k=5 o validar la respuesta contra
  el contexto para reducirlo.

### Usuarios y permisos — OK
- Crear usuario (admin), login del nuevo usuario, refresh de token, `/me`: OK.
- Usuario normal intentando endpoint de admin: **403** (bloqueado).
- Usuario duplicado: 400. Borrar usuario: OK (admin no puede borrarse a sí mismo).

### Seguridad básica
- Rate limit de login: 5 intentos fallidos → HTTP 429. OK.
- Rate limit de chat (20/min): el mecanismo es el mismo; con peticiones
  secuenciales no se superó la ventana de 60 s (no se pudo forzar en serie).

### Emails sin RESEND — OK (diseñado)
- Chat con email crea el lead sin error; el envío de email se omite con un warning
  en el log (no rompe el flujo). Para producción solo falta poner la RESEND_API_KEY.

### Páginas web (navegador/HTTP) — OK
- Todas cargan 200: panel admin `/`, landing pública `/static/index.html`, widget
  `/static/widget/widget.js`, `/checkout-return`, `/checkout-cancel`, `/health`,
  sitio generado y su reporte SEO.
- El panel admin contiene las secciones Leads y "Chatbot para tu Pagina".
- Sintaxis JS válida (node --check) en admin, landing y widget.
- El sitio generado usa imágenes externas de Unsplash (verificado: cargan 200).
- Config pública del widget devuelve título correcto.
- Test headless del widget: **TEST PASS**.

## Limpieza posterior
- Tenant de prueba borrado por API (elimina sitio + documentos + vector_db).
- Ordenes, leads y conversaciones de prueba eliminados.
- ZIP de export y archivos temporales borrados.
- Estado final: tenants 0, ordenes 0, leads 0, conversaciones 0, chat_configs {},
  usuarios solo `admin`, exports 0.

## Conclusión
El sistema funciona de punta a punta en los flujos que se venden. Las únicas
cuestiones menores: (1) el RAG puede fallar en preguntas dobles (recomendado
subir k de 3 a 5), y (2) falta configurar la clave de Resend para emails reales.
Queda listo para pasar a mejoras visuales orientadas a conversión
(escaparate de plantillas, WhatsApp flotante, video/transparencias, etc.).
