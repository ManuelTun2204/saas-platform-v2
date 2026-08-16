# Charla 2026-08-15: Bloque 2 - Ventas y Pagos

## Qué se hizo
Implementación completa del bloque "Ventas y pagos" (del plan priorizado de auditorías).

### Backend
- **El tenant ya NO se crea antes de pagar.** El checkout solo valida el ID y guarda la orden con toda la configuración del sitio (`site_config` con company_name, system_prompt, main_objective, escalation_email, objective, audience, tone, página, contactos). El tenant se crea recién cuando el pago está confirmado (en `_mark_tenant_paid`).
- **Webhooks de pago** (públicos, llamados por las pasarelas):
  - `POST /api/payments/webhook/stripe` — verifica firma con `STRIPE_WEBHOOK_SECRET` (si está configurada), acepta `checkout.session.completed` y `payment_intent.succeeded`.
  - `POST /api/payments/webhook/mercadopago` — verifica el pago con la API de MP (`external_reference` = order_id). Si no hay clave configurada responde "Mercado Pago no configurado" (ya no crashea).
  - `POST /api/payments/webhook/paypal` — acepta `PAYMENT.CAPTURE.COMPLETED`, `CHECKOUT.ORDER.APPROVED`, `CHECKOUT.ORDER.COMPLETED`; verifica contra la API de PayPal.
  - Todos marcan la orden como `paid` y disparan `finalize` (generación de la entrega).
- **Vista de órdenes para el admin**: `GET /api/payments/orders` (solo admin) + `POST /api/payments/cancel/{order_id}` (no deja cancelar pagadas).
- **Ingresos reales por mes**: `analytics` ahora lee `orders.json` → métricas `revenue_this_month`, `revenue_total`, `orders_total`, `orders_pending`, `orders_cancelled` y gráfica `revenue_monthly` (últimos 6 meses, solo pagadas).
- Escritura de `orders.json` y `tenants.json` ahora atómica (archivo temporal + renombre) para evitar corrupción con 2 workers.
- `validate_tenant_id()` extraído en deps para validar sin crear el registro.

### Panel admin (frontend)
- Nueva pestaña **Ordenes**: resumen (totales / pendientes / ingresos cobrados) + tabla con empresa, ID, paquete, monto, método, estado, fecha y acciones: "Ver entrega", "Regenerar entrega" (si pagada y no generada), "Cancelar" (si pendiente).
- Dashboard: la métrica ahora es **Ingresos (mes)** (antes "Ingresos Est.") y hay una gráfica nueva **Ingresos por Mes**.

### Otros
- `checkout_cancel.html` marca la orden como cancelada automáticamente.
- **Arranque offline de embeddings**: el modelo `all-MiniLM-L6-v2` se hornea en la imagen Docker y se activó `HF_HUB_OFFLINE=1` → el backend ya no se cuelga en arranques cuando la red a huggingface.co falla. Se añadió `PRICE_SEO_ONLY` al compose.

## Pruebas verificadas (Docker, proveedor demo)
- Login admin → checkout: **no crea tenant** (contador 0). ✓
- Status → paid → finalize → sitio generado, **tenant creado con company_name, industry, package y payment_status=paid**. ✓
- `GET /api/payments/orders` lista la orden con generated=True. ✓
- Analytics: `revenue_this_month=249`, chart mensual con 249 en 2026-08. ✓
- Cancelación de orden pendiente: success → status `cancelled`. (En demo no aplica porque el pago se marca pagado al instante.) ✓
- Webhooks: stripe/paypal devuelven "ignored" para eventos no manejados; MP sin clave devuelve error limpio (antes crasheaba). ✓

## Estado
- Commit `80ff2a1` subido a GitHub (main).
- Datos de prueba limpiados (tenants/orders/leads/conversations en `[]`, carpetas webs generadas eliminadas). Se conserva el usuario local `admin/admin123` en `data/users.json` (solo laptop).
- Backend corriendo en http://localhost:8000 con el modelo de embeddings offline.

## Siguientes bloques pendientes (del plan)
1. **Seguridad**: rate limit en login, permisos por rol, controlar tamaño de subida antes de leer el archivo.
2. **Costos**: usar modelo free de OpenRouter, no cargar embeddings dos veces, caché de respuestas LLM.
3. **Atractivo**: panel de leads, captura de email, mejoras del editor, SEO, emails con Resend.
4. Deuda técnica: migrar a Postgres (fase 3), limpiar contenedores huérfanos (saas-n8n, saas-postiz, etc.).
