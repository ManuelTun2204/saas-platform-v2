# Glassmorphism - memoria de trabajo (2026-08-17)

## Qué se hizo
- Nuevo tema visual "Vidrio" (glassmorphism) para sitios generados.
- Efecto: fondo degradado oscuro (#0f0c29 → #302b63 → #24243e), cards con `backdrop-filter: blur(24px)` y transparencia rgba(255,255,255,0.08), bordes sutiles, gradientes de texto, navbar transparente con blur.
- CSS condicional: solo se aplica cuando `visual_style == 'glassmorphism'`.
- Colores por defecto: primary=#667eea, secondary=#764ba2 (azul-violeta).

## Archivos modificados
- `backend/app/services/website_service.py` — Agregado `"glassmorphism"` al dict `theme_colors`
- `backend/app/static/admin/index.html` — Nueva tarjeta "Vidrio" en selector de temas (4ta opción)
- `backend/app/templates/landing.html` — Bloque CSS glassmorphism con ~40 reglas
- `backend/app/templates/services.html` — Mismo bloque adaptado
- `backend/app/templates/portfolio.html` — Mismo bloque adaptado

## Decisiones
- Se mostraron 4 temas en el panel (antes solo 3): Moderno, Natural, Elegante, Vidrio.
- `portafolio.html` (ortografía española) no se usa en el código; no se modificó.
- El prompt al LLM recibe "glassmorphism" como visual_style; el LLM ajusta el copywriting (más premium/moderno).

## Pendiente / siguiente
- Escaparate de plantillas en la landing pública (mostrar 3-4 sitios reales antes de comprar).
- Botón WhatsApp flotante en sitios generados.
