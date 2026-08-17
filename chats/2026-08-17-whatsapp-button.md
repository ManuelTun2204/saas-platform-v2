# Botón WhatsApp flotante - memoria de trabajo (2026-08-17)

## Qué se hizo
- Botón flotante de WhatsApp en las 3 plantillas generadas (landing.html, services.html, portfolio.html).
- Aparece solo si `contact_phone` tiene valor (condición `{% if contact_phone %}`).
- Botón verde circular (#25D366), fijo en `bottom-6 right-6`, z-50, con hover scale y sombra verde.
- Link `wa.me/{numero}?text=Hola,%20me%20interesa%20su%20servicio` (mensaje prellenado).
- El número se limpia automáticamente: sin espacios, sin +, sin guiones.

## Archivos modificados
- `backend/app/templates/landing.html` — Botón antes de `</body>`
- `backend/app/templates/services.html` — Botón antes de `</body>`
- `backend/app/templates/portfolio.html` — Botón antes de `</body>`

## No hubo cambios de backend
- `contact_phone` ya existía en todo el pipeline (admin → schema → payment_service → website_service → templates).
- El admin ya lo llama "Telefono / WhatsApp".

## Pendiente / siguiente
- Escaparate de plantillas en la landing pública.
- Fondo de video en hero.
